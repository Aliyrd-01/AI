"""
Generation eval: faithfulness + answer relevancy + citation validity.

Runs the RAG pipeline end-to-end (retrieval -> grounded answer) over eval_set.json
and scores answers with an LLM judge from the same provider pool. Self-contained:
no ragas dependency, so it installs and runs anywhere the app does.

Usage:
    python eval/eval_generation.py --limit 20
    python eval/eval_generation.py --strategy hybrid_hyde --limit 10
    python eval/eval_generation.py --strategy hybrid_ce --limit 20 --k 5
"""

import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rag"))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL_SET = os.path.join(HERE, "eval_set.json")
RESULTS = os.path.join(HERE, "results_generation.json")

RELEVANCY_TPL = (
    "Rate how directly and completely the answer addresses the question on a scale "
    "0.0-1.0. Reply with ONLY the number.\n\nQuestion: {q}\nAnswer: {a}"
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="hybrid")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    import module_5_retrieval as m
    from module_7_generation import (
        format_context, sanitize_context, generate_citations,
        verify_grounding, check_faithfulness, parse_score, context_numbering,
        reorder_lost_in_middle,
    )
    from common import get_chat_llm, get_judge_llm, describe_llm

    with open(EVAL_SET, encoding="utf-8") as f:
        data = json.load(f)
    items = data["items"][: args.limit] if args.limit else data["items"]

    llm = get_chat_llm(temperature=0)     # answerer
    judge = get_judge_llm()               # independent judge (must differ from answerer)

    def retrieve(q, k):
        s = args.strategy
        if s == "dense_only":
            return m.search_dense(q, k)
        if s == "sparse_only":
            return m.search_sparse(q, k)
        if s == "hybrid_hyde":
            return m.search_hybrid_hyde(q, k, llm=llm)
        if s == "multi_query":
            return m.search_multi_query(q, k, llm=llm)
        if s == "hybrid_ce":
            return m.rerank_cross_encoder(q, m.search_hybrid(q, max(k, 20)), top_n=k)
        return m.search_hybrid(q, k)

    print("strategy=%s | k=%d | queries=%d" % (args.strategy, args.k, len(items)))
    print("-" * 78)

    rows = []
    for i, it in enumerate(items, 1):
        t0 = time.time()
        docs = retrieve(it["query"], args.k)
        # Тот же порядок, что уйдёт в промпт: [n] должен указывать на ids[n-1].
        docs = reorder_lost_in_middle(docs)
        numbering = [(i + 1, str(d[0])) for i, d in enumerate(docs)]
        context = sanitize_context(format_context(docs, reorder=False))
        answer = generate_citations(it["query"], context, llm)

        ids = [str(d[0]) for d in docs]
        issues, cited, has_issues = verify_grounding(answer, ids, len(docs), numbering=numbering)
        faith = check_faithfulness(context, answer, judge)   # None = judge failure
        try:
            rel = parse_score(judge.invoke(RELEVANCY_TPL.format(q=it["query"], a=answer)).content)
        except Exception:  # noqa: BLE001
            rel = None
        judge_errors = sum(1 for v in (faith, rel) if v is None)

        rows.append({
            "qid": it["qid"],
            "query": it["query"],
            "n_docs": len(docs),
            "n_citations": len(cited),
            "citation_valid": (not has_issues) and bool(cited),
            "faithfulness": round(faith, 3) if faith is not None else None,
            "answer_relevancy": round(rel, 3) if rel is not None else None,
            "judge_errors": judge_errors,
            "latency_s": round(time.time() - t0, 2),
        })
        def _f(x):
            return " n/a" if x is None else f"{x:.2f}"
        print("[%3d/%3d] faith=%s rel=%s cit=%s  \"%s\""
              % (i, len(items), _f(faith), _f(rel),
                 "ok" if rows[-1]["citation_valid"] else "bad", it["query"][:48]))

    valid_f = [r["faithfulness"] for r in rows if r["faithfulness"] is not None]
    valid_r = [r["answer_relevancy"] for r in rows if r["answer_relevancy"] is not None]
    n = len(rows) or 1
    summary = {
        "faithfulness": round(sum(valid_f) / len(valid_f), 4) if valid_f else 0.0,
        "answer_relevancy": round(sum(valid_r) / len(valid_r), 4) if valid_r else 0.0,
        "citation_valid_rate": round(sum(1.0 for r in rows if r["citation_valid"]) / n, 4),
        "avg_latency_s": round(sum(r["latency_s"] for r in rows) / n, 3),
        "judge_score_errors": sum(r["judge_errors"] for r in rows),
        "judged": {"faithfulness": len(valid_f), "answer_relevancy": len(valid_r)},
    }

    out = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tag": args.tag or "run",
        "strategy": args.strategy,
        "k": args.k,
        "n": len(rows),
        "judge": describe_llm(judge),
        "answerer": describe_llm(llm),
        "summary": summary,
        "rows": rows,
    }
    with open(RESULTS, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("-" * 78)
    print("faithfulness=%(faithfulness).3f  answer_relevancy=%(answer_relevancy).3f  "
          "citation_valid=%(citation_valid_rate).3f  avg=%(avg_latency_s).2fs" % summary)
    print("saved -> %s" % RESULTS)


if __name__ == "__main__":
    main()
