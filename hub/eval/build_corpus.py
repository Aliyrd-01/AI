"""Build a Qdrant collection from an MTEB/BeIR retrieval dataset.

    python hub/eval/build_corpus.py --dataset scidocs                 # full build
    python hub/eval/build_corpus.py --dataset scidocs --limit 32 --collection rag_tmp

Steps:
    1. download corpus / queries / qrels from HuggingFace;
    2. write data/corpus/<dataset>/corpus.jsonl;
    3. build a retrieval eval set -> hub/eval/eval_set_<dataset>.json;
    4. compute BM25 IDF stats    -> hub/eval/idf_stats_<collection>.json;
    5. (re)create the Qdrant collection and upload dense (nomic 768d, int8
       quantized, same as rag_v2_q_test) + sparse (Qdrant/bm25) vectors.

Dense vectors are produced with the same fastembed model the query side uses,
so retrieval stays consistent. Only the targeted collection is (re)created.
"""

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.normpath(os.path.join(HERE, ".."))
RAG = os.path.join(HUB, "rag")
ROOT = os.path.normpath(os.path.join(HUB, ".."))
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, RAG)

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))

from common import _FASTEMBED_DENSE_MODEL, get_fastembed_sparse  # noqa: E402
from module_5_retrieval import get_client  # noqa: E402
from qdrant_client.http import models as qm  # noqa: E402


SPECS = {
    "scidocs": {
        "hf": "mteb/scidocs",
        "corpus_cfg": "corpus",
        "queries_cfg": "queries",
        "qrels_cfg": "default",
        "qrels_splits": ["test"],
        "source": "scidocs",
        "lang": "en",
    },
}


def _get(row, *keys, default=""):
    for k in keys:
        if k in row and row[k] is not None:
            return row[k]
    return default


def load_dataset_items(spec, limit, with_corpus=True):
    from datasets import load_dataset

    docs = []
    if with_corpus:
        corpus = load_dataset(spec["hf"], spec["corpus_cfg"], split="corpus")
        for row in corpus:
            doc_id = str(_get(row, "_id", "id"))
            title = str(_get(row, "title")).strip()
            text = str(_get(row, "text")).strip()
            docs.append({"doc_id": doc_id, "title": title,
                         "text": f"{title}\n{text}" if title else text})
            if limit and len(docs) >= limit:
                break

    queries = load_dataset(spec["hf"], spec["queries_cfg"], split="queries")
    qmap = {str(_get(r, "_id", "id")): str(_get(r, "text")).strip() for r in queries}
    qmap = {k: v for k, v in qmap.items() if v}

    qrels = []
    for split in spec["qrels_splits"]:
        try:
            ds = load_dataset(spec["hf"], spec["qrels_cfg"], split=split)
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠ qrels split '{split}' unavailable: {e}")
            continue
        for r in ds:
            if float(_get(r, "score", default=0) or 0) <= 0:
                continue
            qrels.append((str(_get(r, "query-id", "query_id")),
                          str(_get(r, "corpus-id", "corpus_id"))))
    return docs, qmap, qrels


def build_eval_set(qmap, qrels, docs, limit):
    known = {d["doc_id"] for d in docs}
    by_q = {}
    for qid, did in qrels:
        if did in known and qid in qmap:
            by_q.setdefault(qid, []).append(did)
    items = []
    for qid, rel in by_q.items():
        items.append({"qid": qid, "query": qmap[qid], "relevant": sorted(set(rel))})
        if limit and len(items) >= limit:
            break
    return items


def local_dense_vecs(model, texts, batch_size):
    return [[float(x) for x in v] for v in model.embed(texts, batch_size=batch_size)]


def _sparse_indices(sv):
    return [int(x) for x in (sv.indices.tolist() if hasattr(sv.indices, "tolist") else sv.indices)]


def _upsert_with_retry(client, collection, points, attempts=4):
    delay = 5
    for i in range(attempts):
        try:
            client.upsert(collection_name=collection, points=points, wait=True)
            return
        except Exception as e:  # noqa: BLE001
            if i == attempts - 1:
                raise
            print(f"  ⚠ upsert failed ({i + 1}/{attempts}): {type(e).__name__} - retry in {delay}s",
                  flush=True)
            time.sleep(delay)
            delay *= 2


def compute_idf(docs, max_chars, batch_size):
    """Exact BM25 document frequencies over the whole corpus (sparse pass only)."""
    sparse = get_fastembed_sparse()
    df = {}
    n_docs = len(docs)
    t0 = time.time()
    for start in range(0, n_docs, batch_size):
        chunk = docs[start:start + batch_size]
        texts = [d["text"][:max_chars] for d in chunk]
        for sv in sparse.embed(texts, batch_size=batch_size):
            for term in _sparse_indices(sv):
                df[term] = df.get(term, 0) + 1
        done = min(start + batch_size, n_docs)
        print(f"  idf {done}/{n_docs} ({done / max(time.time() - t0, 1e-6):.1f} docs/s)", flush=True)
    return {"n_docs": n_docs, "df": {str(k): v for k, v in df.items()}}


def build_index(client, collection, docs, batch_size, source, lang, max_chars, start=0):
    from fastembed import TextEmbedding
    dense = TextEmbedding(_FASTEMBED_DENSE_MODEL, threads=8)
    sparse = get_fastembed_sparse()

    if start == 0:
        if client.collection_exists(collection_name=collection):
            client.delete_collection(collection_name=collection)
        client.create_collection(
            collection_name=collection,
            vectors_config={
                "dense": qm.VectorParams(
                    size=768,
                    distance=qm.Distance.COSINE,
                    quantization_config=qm.ScalarQuantization(
                        scalar=qm.ScalarQuantizationConfig(
                            type=qm.ScalarType.INT8, always_ram=True
                        )
                    ),
                )
            },
            sparse_vectors_config={"sparse": qm.SparseVectorParams()},
        )
    else:
        print(f"  resuming existing collection '{collection}' at point {start}", flush=True)

    n_docs = len(docs)
    t0 = time.time()
    for start_ in range(start, n_docs, batch_size):
        chunk = docs[start_:start_ + batch_size]
        texts = [d["text"][:max_chars] for d in chunk]
        sparse_vecs = list(sparse.embed(texts, batch_size=batch_size))
        dense_vecs = local_dense_vecs(dense, texts, batch_size)
        points = []
        for j, (d, sv, dv) in enumerate(zip(chunk, sparse_vecs, dense_vecs)):
            idx = _sparse_indices(sv)
            val = [float(x) for x in (sv.values.tolist() if hasattr(sv.values, "tolist") else sv.values)]
            points.append(qm.PointStruct(
                id=start_ + j,
                vector={"dense": dv, "sparse": qm.SparseVector(indices=idx, values=val)},
                payload={
                    "doc_id": d["doc_id"],
                    "page_content": texts[j],
                    "title": d["title"],
                    "chunk_id": 0,
                    "source": source,
                    "lang": lang,
                },
            ))
        _upsert_with_retry(client, collection, points)
        done = min(start_ + batch_size, n_docs)
        rate = done / max(time.time() - t0, 1e-6)
        eta = (n_docs - done) / rate if rate else 0
        print(f"  indexed {done}/{n_docs} ({rate:.2f} docs/s, ETA {eta/60:.0f} min)", flush=True)
    return n_docs


def read_corpus_jsonl(path):
    docs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    return docs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="scidocs", choices=sorted(SPECS))
    ap.add_argument("--collection", default="")
    ap.add_argument("--limit", type=int, default=0, help="index only first N docs (smoke)")
    ap.add_argument("--eval-limit", type=int, default=100)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--max-chars", type=int, default=1600)
    ap.add_argument("--start", type=int, default=-1,
                    help="resume from this point index (-1 = auto-detect, 0 = rebuild)")
    ap.add_argument("--idf-only", action="store_true",
                    help="only recompute idf stats from data/corpus/<dataset>/corpus.jsonl")
    args = ap.parse_args()

    spec = SPECS[args.dataset]
    collection = args.collection or f"rag_{args.dataset}"
    corpus_path = os.path.join(DATA, "corpus", args.dataset, "corpus.jsonl")

    if args.idf_only:
        docs = read_corpus_jsonl(corpus_path)
        print(f"idf-only: {len(docs)} docs from {corpus_path}")
        stats = compute_idf(docs, args.max_chars, args.batch)
        idf_path = os.path.join(HERE, f"idf_stats_{collection}.json")
        with open(idf_path, "w", encoding="utf-8") as f:
            json.dump(stats, f)
        print(f"  idf ({len(stats['df'])} terms, n_docs={stats['n_docs']}) -> {idf_path}")
        return

    print(f"dataset: {spec['hf']} -> collection '{collection}'")
    if os.path.exists(corpus_path):
        docs = read_corpus_jsonl(corpus_path)
        if args.limit:
            docs = docs[:args.limit]
        print(f"  docs={len(docs)} (from local corpus.jsonl)")
        _, qmap, qrels = load_dataset_items(spec, args.limit, with_corpus=False)
    else:
        docs, qmap, qrels = load_dataset_items(spec, args.limit)
        os.makedirs(os.path.dirname(corpus_path), exist_ok=True)
        with open(corpus_path, "w", encoding="utf-8") as f:
            for d in docs:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        print(f"  corpus -> {corpus_path}")
    print(f"  docs={len(docs)} queries={len(qmap)} qrels={len(qrels)}")

    items = build_eval_set(qmap, qrels, docs, args.eval_limit)
    eval_path = os.path.join(HERE, f"eval_set_{args.dataset}.json")
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump({"collection": collection, "dataset": spec["hf"], "items": items},
                  f, ensure_ascii=False, indent=2)
    print(f"  eval set ({len(items)} q) -> {eval_path}")

    client = get_client()

    start = args.start
    if start < 0:
        start = 0
        try:
            existing = client.get_collection(collection).points_count or 0
            if 0 < existing < len(docs):
                start = (existing // args.batch) * args.batch
                print(f"  found {existing} existing points -> resuming from {start}")
        except Exception as e:  # noqa: BLE001
            print(f"  no existing collection ({type(e).__name__}) -> building from 0")

    build_index(client, collection, docs, args.batch,
                spec["source"], spec["lang"], args.max_chars, start=start)

    print(f"  computing idf over {len(docs)} docs...")
    stats = compute_idf(docs, args.max_chars, args.batch)
    idf_path = os.path.join(HERE, f"idf_stats_{collection}.json")
    with open(idf_path, "w", encoding="utf-8") as f:
        json.dump(stats, f)
    print(f"  idf ({len(stats['df'])} terms) -> {idf_path}")

    info = client.get_collection(collection)
    print(f"done: {collection} — {info.points_count} points, status={info.status}")


if __name__ == "__main__":
    main()
