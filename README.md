# AI Portfolio Hub

One project = one site with my AI work: **Home · RAG · n8n · Agents · Benchmarks · Projects**.
A Streamlit multi-page app; the vector index lives in Qdrant Cloud, so the container stays thin.

## What's inside

| Page | Contents |
|---|---|
| `Home.py` | landing / overview |
| `pages/1_RAG.py` | production-style RAG demo (hybrid retrieval, citations, on-machine benchmark) |
| `pages/2_n8n.py` | 3 n8n workflows (diagrams + video + exported JSON) |
| `pages/3_Projects.py` | project list |
| `pages/4_Agents.py` | AutoAgent + MCP |
| `pages/5_Benchmarks.py` | RAG metrics + LLM suite |
| `pages/6_Unified_Agent.py` | unified agent demo |

## RAG section

**Retrieval** — 11 strategies you can pick from the sidebar, all share one pipeline:

- **dense**: `nomic-ai/nomic-embed-text-v1.5` (768d, int8-quantized in Qdrant)
- **sparse**: `Qdrant/bm25` with **client-side BM25 IDF** (the collection is created without
  `modifier=IDF`, so the app re-weights the query vector itself)
- **fusion**: Qdrant RRF / weighted RRF (dense + sparse)
- **rerank**: cross-encoder (`Xenova/ms-marco-MiniLM-L-6-v2`) or LLM rerank
- **query transforms**: HyDE, multi-query
- strategies: `dense_only`, `sparse_only`, `hybrid`, `hybrid_diverse`, `hybrid_weighted`,
  `hybrid_cross_encoder`, `hybrid_hyde`, `hybrid_hyde_cross_encoder`, `dense_hyde`,
  `multi_query`, `hybrid_llm_rerank`

**Generation** — answer with inline citations `[n](source#doc_id)`, strict-grounding mode,
metadata filters (language / source), and a **0..1 confidence** score
(raw scores live on different scales per strategy; they are normalized before the threshold slider).

**Strict grounding = auto-refuse** (not just a warning): when the answer cites none of the
retrieved documents, the pipeline replaces it with a refusal and keeps the raw model output in an
`Unverified draft` expander. Models sometimes emit bare numbers ("...a dark color 6.") instead of
link citations — `normalize_citations()` repairs those into real `[n](source#id)` links, but only
when the answer has no well-formed citation at all, and only for in-range numbers at plausible
positions (never decimals/dates). The gate itself is a pure function with unit tests.

**Dialog mode (multi-turn RAG)** — sidebar switch `Q&A` / `Chat (memory + follow-ups)`.
Chat mode keeps the conversation in `st.session_state` and renders it with `st.chat_message`;
before retrieval an LLM **rewrites the follow-up into a standalone query** using the history
("and what about dark urine?" → "what causes dark urine"), so retrieval gets a full query instead
of a fragment. The condensed query is shown under each reply ("Searched for: ..."), together with
per-turn sources, citations, cost and the refusal/draft state. Q&A mode stays untouched.

**Multi-corpus** — the sidebar selector switches the active Qdrant collection:

| Corpus | Collection | Size | Domain |
|---|---|---|---|
| MS MARCO | `rag_v2_q_test` | 310,746 chunks | web passages (Q&A) |
| SciDocs (BeIR) | `rag_scidocs` | 25,657 papers | scientific abstracts |

Adding a corpus is one script:

```powershell
python hub/eval/build_corpus.py --dataset scidocs          # full build
python hub/eval/build_corpus.py --dataset scidocs --limit 200 --collection rag_tmp  # smoke
python hub/eval/build_corpus.py --dataset scidocs --idf-only   # recompute IDF from corpus.jsonl
```

The build is resumable and network-proof: upserts retry with backoff, and a run that dies can be
restarted as-is (it auto-detects existing points and continues, e.g. `--start 5904`). IDF is
computed over the whole corpus at the end, so a resumed run stays consistent.

It downloads corpus/queries/qrels from HuggingFace, writes `data/corpus/<name>/corpus.jsonl`,
creates the retrieval eval set (`hub/eval/eval_set_<name>.json`), computes per-collection IDF
stats (`hub/eval/idf_stats_<collection>.json`) and uploads dense+sparse vectors to Qdrant.

**Tracing** — LangSmith (EU endpoint), project `production-rag`.

## Evaluation

- **Retrieval** (offline + on-demand in the page): Hit@5, Hit@10, MRR@10, NDCG@10 over an eval set
  with ground-truth qrels → `hub/eval/results_retrieval.json`.
- **Generation** (LLM judge, cross-model): faithfulness, answer relevancy, citation validity →
  `hub/eval/results_generation.json`.
- **Unit tests**: `python hub/eval/test_units.py`.

## Run

**Local (double-click):** `start.cmd` → http://localhost:8501

**Public link (double-click):** `start-public.cmd` → prints a `trycloudflare.com` URL
(needs `tools/cloudflared.exe`; the machine must stay on).

**Docker:**
```powershell
docker compose up --build      # http://localhost:7860
```

**Manual:**
```powershell
pip install -r requirements.txt
streamlit run hub/Home.py
```

## Structure

```
start.cmd / start-public.cmd     launchers
hub/
  Home.py                        landing page
  pages/1_RAG.py                 RAG demo
  pages/2_n8n.py                 3 workflows (diagrams + video + JSON)
  pages/3_Projects.py            projects
  pages/4_Agents.py              AutoAgent + MCP
  pages/5_Benchmarks.py          RAG metrics + LLM suite
  rag/                           RAG code (retrieval, generation, common, api)
  eval/                          metrics, eval scripts, results, corpus builders
  assets/n8n/                    n8n exports, videos, screenshots
tools/                           public launch (cloudflared) - not committed
Dockerfile / docker-compose.yml  local and VPS
Caddyfile                        reverse proxy + HTTPS (VPS)
```

## Notes / design decisions

- **Mojibake repair on read**: the MS MARCO payloads were indexed with broken encoding
  (UTF-8 decoded as cp1252 / latin-1). `_fix_mojibake` in `module_5_retrieval.py` repairs both
  flavours at query time, so the collection does not need re-indexing.
- **Client-side IDF**: Qdrant returns raw term matches; the BM25 weighting is applied in Python.
- **Score normalization**: each strategy's raw score is mapped to a comparable 0..1 confidence
  (cosine → clamp, logits → scaled, others → saturating `raw/(raw+scale)`).
- **Per-collection IDF files**: `idf_stats.json` for the default corpus, `idf_stats_<collection>.json`
  otherwise.

## Secrets

`.env` (Qdrant / LLM keys) is not committed. Template: `.env.example`.

## Demo video

Record a hub walkthrough (needs the hub running via `start.cmd`):

```powershell
npm i --no-save playwright
node record_demo.mjs          # output: docs/hub-demo.webm
```

Finished video: **`docs/hub-demo.mp4`** — a tour of all hub pages.
