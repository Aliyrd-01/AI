"""RAG demo page — hybrid retrieval (dense + sparse RRF) + citations. (RU/EN)"""

import json
import os
import secrets
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, ".."))
RAG_DIR = os.path.join(HUB, "rag")
EVAL_DIR = os.path.join(HUB, "eval")
sys.path.insert(0, HUB)
sys.path.insert(0, RAG_DIR)
sys.path.insert(0, EVAL_DIR)

import streamlit as st
from i18n import lang_switcher

st.set_page_config(page_title="RAG — Production Demo", page_icon="🔎", layout="centered")

lang = lang_switcher()

T = {
    "ru": {
        "caption": "dense + sparse (RRF) → rerank → LLM с цитатами · Qdrant Cloud · FastEmbed · LangChain",
        "retrieval": "Retrieval",
        "strategy": "Strategy",
        "top_k": "Candidates (top K)",
        "after_rerank": "After rerank",
        "answering": "Ответ",
        "min_score": "Мин. top score (0 = выкл)",
        "strict": "Строгий grounding (отказ, если ответ без цитат)",
        "refuse": "**Отказано:** ответ не опирается на найденные документы — ни одной валидной цитаты. "
                  "Модель отвечала по своим знаниям, а не по корпусу.",
        "draft": "Черновик без подтверждения (скрыт строгим grounding)",
        "meta": "Фильтр по метаданным",
        "language": "Язык",
        "source": "Источник",
        "corpus": "Корпус",
        "try": "Попробуй",
        "q": "Вопрос",
        "ask": "Спросить",
        "retrieving": "Ищу...",
        "answer": "Ответ",
        "total": "Всего",
        "retr": "Retrieval",
        "gen": "Генерация",
        "llm": "LLM",
        "sources": "Источники",
        "cited": "✅ цитируется",
        "conf": "Достоверность top-дока (0..1)",
        "bench_r": "Retrieval benchmarks",
        "bench_g": "Генерация",
        "no_results": "Нет результатов — запусти `python hub/eval/eval_retrieval.py`.",
        "ab": "Сравнить все стратегии (A/B на этом вопросе)",
        "compare": "Сравнить все",
        "trace": "Trace (dense vs sparse vs fused)",
        "trace_btn": "Trace",
        "helpful": "👍 Полезно",
        "not_helpful": "👎 Не полезно",
        "failed_fb": "Не полезно",
        "weak": "**Нет ответа в корпусе** — retrieval слабый или пустой.",
        "fb_log": "Спасибо — записал.",
        "bench_static": "📊 Статичный оффлайн-снимок (не пересчитывается)",
        "live_sub": "Живой бенчмарк на eval-наборе (на этой машине)",
        "live_cap": "Реальный прогон: Hit@K / MRR@10 / NDCG@10 по eval-набору активного корпуса.",
        "live_strats": "Стратегии",
        "live_limit": "Вопросов",
        "live_run": "Запустить",
        "live_note": "HyDE / multi_query вызывают LLM — медленно. Начни с dense_only / sparse_only / hybrid.",
        "mode": "Режим",
        "mode_qa": "Q&A (один вопрос)",
        "mode_chat": "Диалог (память + follow-up)",
        "chat_ph": "Спроси о корпусе...",
        "chat_clear": "Очистить диалог",
        "search_q": "Поиск по запросу",
        "chat_note": "Диалог помнит контекст: follow-up переписывается LLM в самостоятельный "
                     "запрос перед поиском (вопрос → «а что насчёт тёмной мочи?» → "
                     "«what causes dark urine»), поэтому в поиск уходит полный запрос, а не обрубок.",
        "session": "Сессия",
        "s_req": "запросов",
        "s_tok": "токенов",
        "s_cache": "кэш retrieval",
        "s_reset": "Сбросить",
        "copy": "Копировать",
        "copied": "скопировано",
        "download": "Скачать .md",
        "cache_hit": "из кэша (без пересчёта)",
        "cache_miss": "поиск заново",
        "obs": "🔭 Observability: LangSmith (EU) — подключается опционально "
               "(`LANGCHAIN_TRACING_V2`, eu.api.smith.langchain.com)",
    },
    "en": {
        "caption": "dense + sparse (RRF) → rerank → LLM with citations · Qdrant Cloud · FastEmbed · LangChain",
        "retrieval": "Retrieval",
        "strategy": "Strategy",
        "top_k": "Candidates (top K)",
        "after_rerank": "After rerank",
        "answering": "Answering",
        "min_score": "Min top score (0 = off)",
        "strict": "Strict grounding (refuse uncited answers)",
        "refuse": "**Refused:** the answer does not cite any retrieved document - not a single "
                  "valid citation. The model answered from its own knowledge, not from the corpus.",
        "draft": "Unverified draft (hidden by strict grounding)",
        "meta": "Metadata filter",
        "language": "Language",
        "source": "Source",
        "corpus": "Corpus",
        "try": "Try",
        "q": "Question",
        "ask": "Ask",
        "retrieving": "Retrieving...",
        "answer": "Answer",
        "total": "Total",
        "retr": "Retrieval",
        "gen": "Generation",
        "llm": "LLM",
        "sources": "Sources",
        "cited": "✅ cited",
        "mode": "Mode",
        "conf": "Top document confidence (0..1)",
        "mode_qa": "Q&A (single question)",
        "mode_chat": "Chat (memory + follow-ups)",
        "chat_ph": "Ask about the corpus...",
        "chat_clear": "Clear chat",
        "search_q": "Searched for",
        "chat_note": "The chat keeps context: a follow-up is rewritten by an LLM into a standalone "
                     "query before retrieval (question -> 'what about dark urine?' -> "
                     "'what causes dark urine'), so retrieval gets a full query, not a fragment.",
        "session": "Session",
        "s_req": "requests",
        "s_tok": "tokens",
        "s_cache": "retrieval cache",
        "s_reset": "Reset",
        "copy": "Copy",
        "copied": "copied",
        "download": "Download .md",
        "cache_hit": "cache hit (no recompute)",
        "cache_miss": "fresh retrieval",
        "obs": "🔭 Observability: LangSmith (EU) — optional "
               "(`LANGCHAIN_TRACING_V2`, eu.api.smith.langchain.com)",
        "bench_r": "Retrieval benchmarks",
        "bench_g": "Generation",
        "no_results": "No results — run `python hub/eval/eval_retrieval.py`.",
        "ab": "Run all strategies (A/B on this question)",
        "compare": "Compare all",
        "trace": "Trace (dense vs sparse vs fused)",
        "trace_btn": "Trace",
        "helpful": "👍 Helpful",
        "not_helpful": "👎 Not helpful",
        "failed_fb": "Not helpful",
        "weak": "**No answer in corpus** — retrieval too weak or empty.",
        "fb_log": "Thanks — logged.",
        "bench_static": "📊 Static offline snapshot (not recomputed here)",
        "live_sub": "Live benchmark on the eval set (this machine)",
        "live_cap": "Real run: Hit@K / MRR@10 / NDCG@10 over the active corpus eval set.",
        "live_strats": "Strategies",
        "live_limit": "Queries",
        "live_run": "Run",
        "live_note": "HyDE / multi_query call the LLM — slow. Start with dense_only / sparse_only / hybrid.",
    },
}[lang]

STRATEGIES = {
    "hybrid": "Hybrid — dense + sparse (RRF) + IDF  ← default",
    "hybrid_diverse": "Hybrid + MMR diversity",
    "hybrid_cross_encoder": "Hybrid + CrossEncoder rerank",
    "hybrid_hyde": "Hybrid + HyDE (hypothetical answer)",
    "hybrid_hyde_cross_encoder": "Hybrid + HyDE + CrossEncoder  (best quality)",
    "multi_query": "Multi-query (LLM rewrites) + hybrid",
    "dense_only": "Dense only (Nomic v1.5)",
    "sparse_only": "Sparse only (BM25 + IDF)",
    "hybrid_weighted": "Hybrid — weighted RRF",
    "hybrid_llm_rerank": "Hybrid + LLM rerank",
    "dense_hyde": "Dense + HyDE",
}
NEEDS_RERANK = ("hybrid_cross_encoder", "hybrid_hyde_cross_encoder", "hybrid_llm_rerank")

CORPORA = {
    "MS MARCO": {
        "collection": "rag_v2_q_test",
        "source": "msmarco",
        "desc": "MS MARCO · web passages (Q&A)",
        "eval_set": "eval_set.json",
        "build": None,
        "meta_langs": ["en"],
        "meta_sources": ["msmarco"],
        "examples": [
            "what color is amber urine",
            "what causes dark amber urine",
            "what do elevated liver enzymes mean",
            "how does a bill become law in the united states",
            "is autoimmune hepatitis a bile acid synthesis disorder",
            "what causes hiccups",
            "how much water should you drink a day",
            "how long does it take to boil an egg",
            "what is the tallest mountain in the world",
        ],
    },
    "SciDocs": {
        "collection": "rag_scidocs",
        "source": "scidocs",
        "desc": "SciDocs (BeIR) · scientific paper abstracts",
        "eval_set": "eval_set_scidocs.json",
        "build": "python hub/eval/build_corpus.py --dataset scidocs",
        "meta_langs": ["en"],
        "meta_sources": ["scidocs"],
        "examples": [],
    },
}


def corpus_examples(key):
    """Example queries for a corpus: curated list, else the corpus eval set."""
    static = CORPORA[key].get("examples") or []
    if static:
        return static
    path = os.path.join(EVAL_DIR, CORPORA[key]["eval_set"])
    if not os.path.exists(path):
        return static
    try:
        with open(path, encoding="utf-8") as f:
            items = json.load(f).get("items", [])
        return [it["query"] for it in items[:6] if it.get("query")] or static
    except Exception:
        return static


# ─── Secrets → os.environ ───────────────────────────────────────────────────
def load_secrets_to_env() -> list:
    try:
        items = dict(st.secrets)
    except Exception:
        return []
    loaded = []
    for k, v in items.items():
        if isinstance(v, str) and v and not os.environ.get(k):
            os.environ[k] = v
            loaded.append(k)
    return loaded


load_secrets_to_env()


@st.cache_resource(show_spinner="Loading Qdrant client...")
def get_collection_info(collection_name):
    from module_5_retrieval import get_client
    info = get_client().get_collection(collection_name)
    return collection_name, info.points_count


@st.cache_resource(show_spinner="Loading LLM pool...")
def get_llm():
    from common import get_chat_llm
    return get_chat_llm(temperature=0)


def _apply_meta_filter(docs, langs=(), sources=()):
    if not langs and not sources:
        return docs
    out = []
    for d in docs:
        pl = d[3] or {}
        if langs and pl.get("lang") not in langs:
            continue
        if sources and pl.get("source") not in sources:
            continue
        out.append(d)
    return out


def retrieve_docs(strategy, question, top_k, rerank_top, langs=(), sources=(), collection=None):
    import module_5_retrieval as m

    if collection:
        m.set_collection(collection)

    llm = None
    if strategy in ("dense_hyde", "hybrid_hyde", "hybrid_hyde_cross_encoder", "multi_query"):
        llm = get_llm()

    if strategy == "dense_only":
        docs = m.search_dense(question, top_k, None)
    elif strategy == "sparse_only":
        docs = m.search_sparse(question, top_k, None)
    elif strategy == "hybrid":
        docs = m.search_hybrid(question, top_k, None)
    elif strategy == "hybrid_diverse":
        docs = m.search_hybrid_diverse(question, top_k, None)
    elif strategy == "hybrid_weighted":
        docs = m.search_hybrid_weighted(question, top_k, None)
    elif strategy == "hybrid_llm_rerank":
        docs = m.search_hybrid_rerank(question, top_k, None, rerank_top=rerank_top)
    elif strategy == "hybrid_cross_encoder":
        base = m.search_hybrid(question, max(top_k, 20), None)
        docs = m.rerank_cross_encoder(question, base, top_n=rerank_top)
    elif strategy == "dense_hyde":
        docs = m.search_dense_hyde(question, top_k, None, llm=llm)
    elif strategy == "hybrid_hyde":
        docs = m.search_hybrid_hyde(question, top_k, None, llm=llm)
    elif strategy == "hybrid_hyde_cross_encoder":
        docs = m.search_hybrid_hyde_ce(question, top_k, None, llm=llm, rerank_top=rerank_top)
    elif strategy == "multi_query":
        docs = m.search_multi_query(question, top_k, None, llm=llm)
    else:
        raise ValueError(strategy)

    return _apply_meta_filter(docs, langs, sources)


# Cache-hit detection: st.cache_data gives no hit/miss API, so the inner call returns a
# nonce that is created once per unique argument set. Seeing the same nonce again means the
# value came from the cache (no recompute) — honest hit/miss, no guessing.
# Counters/nonces live in st.session_state because a Streamlit page script is re-executed on
# every rerun (module-level state would reset each time).
@st.cache_data(show_spinner=False, max_entries=256)
def _cached_retrieve_inner(strategy, question, top_k, rerank_top, langs=(), sources=(), collection=None):
    return (retrieve_docs(strategy, question, top_k, rerank_top, langs, sources, collection),
            secrets.token_hex(8))


def _cache_stats():
    if "cache_stats" not in st.session_state:
        st.session_state["cache_stats"] = {"hit": 0, "miss": 0}
    return st.session_state["cache_stats"]


@st.cache_resource(show_spinner=False)
def _seen_nonces():
    """Nonce set is process-wide: st.cache_data is process-wide too, so hit/miss attribution
    must be as well (session-scoped state would call the first hit after a page reload a miss).
    """
    return []


def cached_retrieve(strategy, question, top_k, rerank_top, langs=(), sources=(), collection=None):
    """Return (docs, cache_hit)."""
    docs, nonce = _cached_retrieve_inner(strategy, question, top_k, rerank_top,
                                         langs, sources, collection)
    seen = _seen_nonces()
    stats = _cache_stats()
    if nonce in seen:
        stats["hit"] += 1
        return docs, True
    stats["miss"] += 1
    if len(seen) >= 500:
        del seen[:250]
    seen.append(nonce)
    return docs, False


def _run_retrieval(strategy, question, top_k, rerank_top, langs, sources, collection=None):
    try:
        docs, hit = cached_retrieve(strategy, question, top_k, rerank_top, langs, sources, collection)
        return docs, None, hit
    except Exception as e:  # noqa: BLE001
        if strategy == "hybrid":
            raise
        docs, hit = cached_retrieve("hybrid", question, top_k, rerank_top, langs, sources, collection)
        return docs, f"{type(e).__name__}: {e}", hit


# Native retrieval scores live on wildly different scales, so comparing them to a
# single 0..1 "min top score" slider is meaningless as-is. Measured on rag_v2_q_test:
#   dense cosine ~0.75..0.86 · sparse BM25 ~120..170 · Qdrant RRF (2 prefetch, hybrid)
#   ~0..0.83 · Qdrant RRF (4 prefetch, hybrid_hyde) ~0..1.67 · python RRF (_rrf_merge:
#   hybrid_weighted/dense_hyde ~0.033, multi_query ~0.065) · cross-encoder logits ~0..10+.
# Each strategy's raw top score is mapped to a comparable 0..1 confidence:
#   cosine -> clamp · logit -> raw/scale · anything else -> saturating raw/(raw+scale).
_SCORE_SCALE = {
    "dense_only": ("cosine", 1.0),
    "hybrid_llm_rerank": ("cosine", 1.0),
    "sparse_only": ("sat", 12.0),
    "hybrid": ("sat", 0.25),
    "hybrid_diverse": ("sat", 0.25),
    "hybrid_hyde": ("sat", 0.50),
    "hybrid_weighted": ("sat", 0.02),
    "dense_hyde": ("sat", 0.02),
    "multi_query": ("sat", 0.04),
    "hybrid_cross_encoder": ("logit", 10.0),
    "hybrid_hyde_cross_encoder": ("logit", 10.0),
}


def _normalized_top_score(strategy, docs):
    """Return (raw_top, confidence_0_to_1) for the threshold slider."""
    raw = max((float(d[2]) for d in docs), default=0.0)
    kind, scale = _SCORE_SCALE.get(strategy, ("sat", 0.03))
    if kind == "cosine":
        return raw, max(0.0, min(1.0, raw))
    if kind == "logit":
        return raw, max(0.0, min(1.0, raw / scale))
    return raw, (raw / (raw + scale) if raw > 0 else 0.0)


_SESS_DEFAULT = {"req": 0, "tok_in": 0, "tok_out": 0, "cost": 0.0}


def _session_stats():
    if "sess" not in st.session_state:
        st.session_state["sess"] = dict(_SESS_DEFAULT)
    return st.session_state["sess"]


def _track_usage(tok_in, tok_out, cost):
    s = _session_stats()
    s["req"] += 1
    s["tok_in"] += int(tok_in or 0)
    s["tok_out"] += int(tok_out or 0)
    s["cost"] += float(cost or 0.0)


def _cache_note(hit):
    return f"⚡ {T['cache_hit']}" if hit else f"🌐 {T['cache_miss']}"


def render_usage_bar(key):
    """Session counter (requests / tokens / $ / retrieval cache) + reset."""
    s = _session_stats()
    stats = _cache_stats()
    total = stats["hit"] + stats["miss"]
    c1, c2 = st.columns([6, 1])
    with c1:
        st.caption(f"📈 **{T['session']}** · {s['req']} {T['s_req']} · "
                   f"{s['tok_in']:,} in / {s['tok_out']:,} out {T['s_tok']} · "
                   f"**${s['cost']:.6f}** · {T['s_cache']} "
                   f"{stats['hit']}/{total}")
    with c2:
        if st.button(T["s_reset"], key=f"reset_{key}"):
            st.session_state["sess"] = dict(_SESS_DEFAULT)
            st.session_state["cache_stats"] = {"hit": 0, "miss": 0}
            st.session_state["seen_nonces"] = []
            st.rerun()


def copy_button(text, key, height=40):
    """Clipboard button (Streamlit has none), styled to match a native st.button."""
    import streamlit.components.v1 as components

    bid = f"cp_{key}"
    payload = json.dumps(text or "")
    label = json.dumps(f"📋 {T['copy']}")
    ok = json.dumps(f"✓ {T['copied']}")
    components.html(f"""
<style>
  html, body {{ margin:0; padding:0; overflow:hidden; }}
  #{bid} {{ box-sizing:border-box; width:100%; height:40px; padding:4px 12px;
           border-radius:8px; cursor:pointer; font-size:16px; font-family:inherit;
           line-height:1.6; white-space:nowrap; transition:background .15s; }}
</style>
<button id="{bid}">📋 {T['copy']}</button>
<script>
const b = document.getElementById("{bid}");
const txt = {payload};
const label = {label}, ok = {ok};
let pdoc = null;
try {{ pdoc = window.parent.document; }} catch (e) {{ pdoc = null; }}
function darkTheme() {{
  try {{
    const rgb = getComputedStyle(pdoc.body).backgroundColor.match(/\\d+/g).map(Number);
    return (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) < 128;
  }} catch (e) {{
    return !!(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
  }}
}}
const dark = darkTheme();
const pal = dark
  ? {{ fg: "#fafafa", bg: "#262730", bd: "rgba(250,250,250,0.2)", hv: "rgba(250,250,250,0.08)" }}
  : {{ fg: "#31333f", bg: "#ffffff", bd: "rgba(49,51,63,0.2)", hv: "rgba(49,51,63,0.06)" }};
if (pdoc) {{ try {{ document.body.style.fontFamily = getComputedStyle(pdoc.body).fontFamily; }} catch (e) {{}} }}
b.style.color = pal.fg;
b.style.background = pal.bg;
b.style.border = "0.8px solid " + pal.bd;
b.onmouseenter = () => {{ b.style.background = pal.hv; }};
b.onmouseleave = () => {{ b.style.background = pal.bg; }};
b.onclick = async () => {{
  try {{ await navigator.clipboard.writeText(txt); }}
  catch (e) {{
    const ta = document.createElement("textarea");
    ta.value = txt; document.body.appendChild(ta); ta.select();
    document.execCommand("copy"); ta.remove();
  }}
  b.textContent = ok;
  setTimeout(() => {{ b.textContent = label; }}, 1500);
}};
</script>""", height=height)


def export_md(q, answer, docs, cited, source, meta="", search_query="", refused=False, draft=""):
    """Markdown report for download: question, run metadata, answer, sources with snippets."""
    import re

    body = re.sub(r"\[(\d+)\]\([^)]*#[^)]+\)", r"[\1]", (answer or "").strip())
    lines = ["# RAG answer", "", f"**{T['q'].rstrip(':')}:** {q}"]
    if search_query and search_query != q:
        lines.append(f"**{T['search_q']}:** `{search_query}`")
    if meta:
        lines += ["", f"**Run:** {meta}"]
    lines += ["", f"## {T['answer'].rstrip(':')}", "", body or "—"]
    if refused and draft:
        lines += ["", f"## {T['draft']}", "", draft]
    if docs:
        lines += ["", f"## {T['sources']} ({len(docs)})", ""]
        for i, d in enumerate(docs, 1):
            mark = f" — {T['cited'].replace('✅', '').strip()}" if str(d[0]) in (cited or set()) else ""
            lines.append(f"{i}. `{source}#{d[0]}` — score `{round(float(d[2]), 3)}`{mark}")
            snippet = " ".join((d[1] or "").split())[:400]
            lines += ["", f"   > {snippet}"]
    lines += ["", "---", "",
              "Generated by the portfolio RAG demo — Qdrant Cloud · hybrid dense + sparse (RRF) "
              "· cross-encoder rerank · LLM answers with citations."]
    return "\n".join(lines)



def _log_feedback(question, answer, strategy, verdict):
    path = os.path.join(EVAL_DIR, "feedback.jsonl")
    rec = {"ts": time.time(), "question": question, "strategy": strategy,
           "verdict": verdict, "answer": (answer or "")[:2000]}
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


with st.sidebar:
    st.header(T["retrieval"])
    mode = st.selectbox(T["mode"], [T["mode_qa"], T["mode_chat"]], key="ui_mode")
    dialog_mode = mode == T["mode_chat"]
    corpus_key = st.selectbox(T["corpus"], list(CORPORA), index=0)
    corpus = CORPORA[corpus_key]

    strategy = st.selectbox(T["strategy"], list(STRATEGIES), index=0,
                            format_func=lambda k: STRATEGIES[k])
    top_k = st.slider(T["top_k"], 1, 20, 8)
    need_rerank = strategy in NEEDS_RERANK
    rerank_top = st.slider(T["after_rerank"], 1, 10, 5) if need_rerank else 5

    st.divider()
    st.markdown(f"**{T['answering']}**")
    min_score = st.slider(T["min_score"], 0.0, 1.0, 0.0, 0.05)
    strict_grounding = st.checkbox(T["strict"], value=False)

    st.divider()
    st.markdown(f"**{T['meta']}**")
    lang_filter = st.multiselect(T["language"], corpus["meta_langs"], default=[])
    source_filter = st.multiselect(T["source"], corpus["meta_sources"], default=[])

    st.divider()
    st.markdown(f"**{T['corpus']}**")
    try:
        coll_name, points = get_collection_info(corpus["collection"])
    except Exception as e:  # noqa: BLE001
        coll_name, points = corpus["collection"], 0
        if "doesn't exist" in str(e) or "Not found" in str(e):
            st.warning(f"Collection `{coll_name}` is not built yet.")
        else:
            st.error(f"Qdrant unavailable: {e}")
    st.code(coll_name, language=None)
    st.caption(f"{corpus['desc']} · {points:,} docs · dense 768d + sparse BM25 + client IDF")
    if points == 0 and corpus.get("build"):
        st.caption(f"Build it with: `{corpus['build']}`")

    st.divider()
    st.markdown(f"**{T['try']}**")
    for q in corpus_examples(corpus_key):
        if st.button(q, use_container_width=True, key=f"ex_{corpus_key}_{q}"):
            st.session_state["q"] = q

    if dialog_mode:
        st.divider()
        if st.button(T["chat_clear"], use_container_width=True, key="chat_clear"):
            st.session_state["chat"] = []
            st.rerun()

st.title("🔎 RAG — Production Demo")
st.caption(T["caption"])
st.caption(T["obs"])

if dialog_mode:
    from common import describe_llm
    from module_7_generation import (
        apply_strict_grounding, condense_query, count_tokens, extract_citations,
        format_context, generate_citations, generate_citations_stream,
        normalize_citations, sanitize_context, verify_grounding,
    )

    st.caption(T["chat_note"])
    if "chat" not in st.session_state:
        st.session_state["chat"] = []
    history = st.session_state["chat"]

    for ti, turn in enumerate(history):
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])
            if turn["role"] != "assistant":
                continue
            if turn.get("refused"):
                st.error(T["refuse"])
                with st.expander(T["draft"], expanded=False):
                    st.markdown(turn.get("draft") or "—")
            docs = turn.get("docs") or []
            with st.expander(f"{T['sources']} ({len(docs)})"):
                st.caption(f"{T['search_q']}: `{turn.get('search_query', '')}`")
                for i, d in enumerate(docs, 1):
                    mark = f"  {T['cited']}" if str(d[0]) in (turn.get("cited") or set()) else ""
                    st.markdown(f"**[{i}]** `{corpus['source']}#{d[0]}` · score "
                                f"`{round(float(d[2]), 3)}`{mark}")
                    st.text((d[1] or "")[:300])
            report = export_md(turn.get("q") or turn.get("search_query", ""), turn["content"],
                               docs, turn.get("cited"), corpus["source"],
                               meta=turn.get("export_meta", ""),
                               search_query=turn.get("search_query", ""),
                               refused=turn.get("refused"), draft=turn.get("draft") or "")
            cb1, cb2, _sp = st.columns([1, 1, 3])
            with cb1:
                copy_button(report, key=f"hist_{ti}")
            with cb2:
                st.download_button(T["download"], data=report.encode("utf-8"),
                                   file_name=f"rag_answer_turn{ti + 1}.md", mime="text/markdown",
                                   key=f"dl_hist_{ti}", width="stretch")
            if turn.get("meta"):
                st.caption(turn["meta"])

    prompt = st.chat_input(T["chat_ph"])
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)

        pairs = [(t["role"], t["content"]) for t in history]
        llm = get_llm()
        t0 = time.time()
        with st.spinner(T["retrieving"]):
            try:
                search_query = condense_query(pairs, prompt, llm) if pairs else prompt
            except Exception:  # noqa: BLE001
                search_query = prompt
            try:
                docs, warn, cache_hit = _run_retrieval(strategy, search_query, top_k, rerank_top,
                                            tuple(lang_filter), tuple(source_filter),
                                            corpus["collection"])
            except Exception as e:  # noqa: BLE001
                docs, warn = None, f"{type(e).__name__}: {e}"
        t1 = time.time()

        answer, draft, refused, cited, top_conf = "", "", False, set(), 0.0
        meta, run_meta = "", ""
        with st.chat_message("assistant"):
            if warn and docs:
                st.warning(f"`{strategy}` failed ({warn}) — fell back to **hybrid**.")
            if not docs:
                answer = T["weak"]
                st.warning(answer)
            else:
                top_raw, top_conf = _normalized_top_score(strategy, docs)
                if min_score > 0 and top_conf < min_score:
                    answer = f"{T['weak']} · top confidence `{top_conf:.2f}` < `{min_score:.2f}`"
                    st.warning(answer)
                else:
                    st.caption(f"{T['search_q']}: `{search_query}`")
                    context = sanitize_context(format_context(docs, source=corpus["source"]))
                    t_gen0 = time.time()
                    ttft = {"v": None}
                    ph = st.empty()
                    buf = [""]

                    def _stream():
                        for chunk in generate_citations_stream(search_query, context, llm,
                                                               source=corpus["source"]):
                            if ttft["v"] is None:
                                ttft["v"] = time.time() - t_gen0
                            buf[0] += chunk
                            ph.markdown(buf[0])
                            yield chunk

                    try:
                        for _ in _stream():
                            pass
                    except Exception:  # noqa: BLE001
                        answer = generate_citations(search_query, context, llm,
                                                    source=corpus["source"])
                        ph.markdown(answer)
                    answer = buf[0] or answer
                    t_gen = time.time() - t_gen0

                    retrieved_ids = [str(d[0]) for d in docs]
                    repaired = normalize_citations(answer, retrieved_ids, corpus["source"])
                    if repaired != answer:
                        answer = repaired
                        ph.markdown(answer)
                    cited = {str(did) for _, did in extract_citations(answer)}
                    issues, _c, _h = verify_grounding(answer, retrieved_ids, len(docs))
                    if strict_grounding:
                        gate = apply_strict_grounding(answer, retrieved_ids, refusal=T["refuse"])
                        refused, draft = gate["refused"], gate["draft"]
                        if refused:
                            answer = gate["answer"]
                            ph.empty()
                            st.error(T["refuse"])
                            with st.expander(T["draft"], expanded=False):
                                st.markdown(draft)
                    tok_in = count_tokens(context + search_query)
                    tok_out = count_tokens(answer)
                    cost = tok_in * (0.004 / 1_000_000) + tok_out * (0.0162 / 1_000_000)
                    info = describe_llm(llm)
                    meta = (f"~{tok_in} in / ~{tok_out} out tokens · est. **${cost:.6f}** · "
                            f"gen {t_gen:.1f}s · {_cache_note(cache_hit)} · `{info['served']}`")
                    st.caption(meta)
                    _track_usage(tok_in, tok_out, cost)
                    run_meta = (f"{corpus_key} (`{corpus['collection']}`) · strategy `{strategy}` · "
                                f"LLM {info['provider']} (`{info['served']}`) · gen {t_gen:.1f}s · "
                                f"~{tok_in} in / ~{tok_out} out tokens · est. ${cost:.6f} · "
                                f"{_cache_note(cache_hit)}")
                    report = export_md(prompt, answer, docs or [], cited, corpus["source"],
                                       meta=run_meta, search_query=search_query,
                                       refused=refused, draft=draft)
                    cb1, cb2, _sp = st.columns([1, 1, 3])
                    with cb1:
                        copy_button(report, key="chat")
                    with cb2:
                        st.download_button(T["download"], data=report.encode("utf-8"),
                                           file_name=f"rag_answer_{int(time.time())}.md",
                                           mime="text/markdown", key="dl_chat", width="stretch")
                    if issues and not refused:
                        st.caption(f"⚠️ citation issues: {issues}")

            if not meta:
                st.caption(f"top confidence `{top_conf:.2f}`")

        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": answer, "docs": docs or [],
                        "cited": cited, "refused": refused, "draft": draft,
                        "q": prompt, "search_query": search_query, "meta": meta,
                        "export_meta": run_meta})
    st.divider()
    render_usage_bar("chat")
    st.stop()

def render_result(res, streamed=False):
    """Отрисовка сохранённого ответа (метрики, источники, стоимость, фидбек).

    Вызывается на КАЖДОМ рендере, а не только в ветке кнопки «Спросить»:
    иначе клик по 👍/👎 перезапускает скрипт, кнопка «Спросить» уже False,
    вложенные виджеты не создаются — и их True теряется (фидбек не логируется).
    """
    if res["warn"]:
        st.warning(f"`{res['strategy']}` failed ({res['warn']}) — fell back to **hybrid**.")

    if not streamed:
        st.markdown(f"### {T['answer']}")
        st.markdown(res["answer"])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(T["total"], f"{(res['t2'] - res['t0']):.1f}s")
    m2.metric(T["retr"], f"{(res['t1'] - res['t0']):.1f}s")
    m3.metric(T["gen"], f"{(res['t2'] - res['t_gen0']):.1f}s")
    m4.metric("TTFT", f"{res['ttft']:.1f}s" if res["ttft"] else "—")

    from common import describe_llm
    info = describe_llm(res["llm"])
    st.caption(f"**{T['llm']}:** `{info['provider']}` · served `{info['served']}` · "
               f"{_cache_note(res.get('cache_hit'))}")

    with st.expander(f"{T['sources']} ({len(res['docs'])})", expanded=True):
        st.caption(f"{T['conf']}: `{res.get('top_conf', 0.0):.2f}`")
        for i, d in enumerate(res["docs"], 1):
            mark = f"  {T['cited']}" if str(d[0]) in res["cited"] else ""
            st.markdown(f"**[{i}]** `{res.get('source', 'msmarco')}#{d[0]}` · score `{round(float(d[2]), 3)}`{mark}")
            st.text(d[1][:400])
    if res.get("refused"):
        st.error(T["refuse"])
        with st.expander(T["draft"], expanded=False):
            st.markdown(res.get("draft") or "—")
    elif res["issues"]:
        st.caption(f"⚠️ citation issues: {res['issues']}")

    st.caption(f"~{res['tok_in']} in / ~{res['tok_out']} out tokens · est. **${res['cost']:.6f}** per query")

    ttft = f"TTFT {res['ttft']:.1f}s · " if res["ttft"] else ""
    run_meta = (f"{corpus_key} (`{corpus['collection']}`) · strategy `{res['strategy']}` · "
                f"LLM {info['provider']} (`{info['served']}`) · "
                f"retrieval {res['t1'] - res['t0']:.1f}s · generation {res['t2'] - res['t_gen0']:.1f}s · "
                f"{ttft}"
                f"~{res['tok_in']} in / ~{res['tok_out']} out tokens · est. ${res['cost']:.6f} · "
                f"{_cache_note(res.get('cache_hit'))}")
    report = export_md(res["q"], res["answer"], res["docs"], res["cited"],
                       res.get("source", "msmarco"), meta=run_meta,
                       refused=res.get("refused"), draft=res.get("draft") or "")

    ca, cb, _sp = st.columns([1, 1, 3])
    with ca:
        copy_button(report, key="qa")
    with cb:
        st.download_button(T["download"], data=report.encode("utf-8"),
                           file_name=f"rag_answer_{int(res['t2'])}.md", mime="text/markdown",
                           key="dl_qa", width="stretch")

    fa, fb, _sp = st.columns([1, 1, 4])
    if fa.button(T["helpful"], key="fb_up"):
        _log_feedback(res["q"], res["answer"], res["strategy"], "up")
        st.toast(T["fb_log"])
    if fb.button(T["not_helpful"], key="fb_down"):
        _log_feedback(res["q"], res["answer"], res["strategy"], "down")
        st.toast(T["fb_log"])

    render_usage_bar("qa")


with st.form("qa_form"):
    question = st.text_input(T["q"], key="q", placeholder="e.g. what color is amber urine")
    submitted = st.form_submit_button(T["ask"], type="primary")

asked = submitted and bool((question or "").strip())

if asked:
    st.session_state.pop("rag_res", None)
    q = question.strip()
    langs = tuple(lang_filter)
    sources = tuple(source_filter)

    t0 = time.time()
    cache_hit = False
    try:
        with st.spinner(T["retrieving"]):
            docs, warn, cache_hit = _run_retrieval(strategy, q, top_k, rerank_top, langs, sources,
                                                   corpus["collection"])
    except Exception as e:  # noqa: BLE001
        st.error(f"**{type(e).__name__}:** {e}")
        docs, warn = None, None
    t1 = time.time()

    if docs is not None:
        top_raw, top_conf = _normalized_top_score(strategy, docs)
        too_weak = (not docs) or (min_score > 0 and top_conf < min_score)
        if too_weak:
            st.warning(f"{T['weak']} · top confidence `{top_conf:.2f}` < `{min_score:.2f}`")
        else:
            from module_7_generation import (
                format_context, generate_citations_stream, sanitize_context,
                extract_citations, verify_grounding, count_tokens,
                apply_strict_grounding, normalize_citations,
            )

            llm = get_llm()
            context = sanitize_context(format_context(docs, source=corpus["source"]))

            if warn:
                st.warning(f"`{strategy}` failed ({warn}) — fell back to **hybrid**.")
            st.markdown(f"### {T['answer']}")
            t_gen0 = time.time()
            ttft = {"v": None}
            answer_ph = st.empty()

            def _gen():
                for chunk in generate_citations_stream(q, context, llm, source=corpus["source"]):
                    if ttft["v"] is None:
                        ttft["v"] = time.time() - t_gen0
                    yield chunk

            try:
                buf = []
                for chunk in _gen():
                    buf.append(chunk)
                    answer_ph.markdown("".join(buf))
                answer = "".join(buf)
            except Exception:
                from module_7_generation import generate_citations
                answer = generate_citations(q, context, llm, source=corpus["source"])
                answer_ph.markdown(answer)
            t2 = time.time()

            answer = answer or ""
            retrieved_ids = [str(d[0]) for d in docs]
            repaired = normalize_citations(answer, retrieved_ids, corpus["source"])
            if repaired != answer:
                answer = repaired
                answer_ph.markdown(answer)
            cited = {str(did) for _, did in extract_citations(answer)}
            issues, _cited, _has_issues = verify_grounding(
                answer, retrieved_ids, len(docs))

            refused, draft = False, ""
            if strict_grounding:
                gate = apply_strict_grounding(answer, retrieved_ids, refusal=T["refuse"])
                refused, draft = gate["refused"], gate["draft"]
                if refused:
                    answer = gate["answer"]
                    answer_ph.empty()

            tok_in = count_tokens(context + q)
            tok_out = count_tokens(answer)
            cost = tok_in * (0.004 / 1_000_000) + tok_out * (0.0162 / 1_000_000)

            res = {
                "q": q, "strategy": strategy, "answer": answer, "docs": docs,
                "cited": cited, "issues": issues, "warn": warn,
                "source": corpus["source"], "refused": refused, "draft": draft,
                "t0": t0, "t1": t1, "t_gen0": t_gen0, "t2": t2,
                "ttft": ttft["v"], "llm": llm, "top_conf": top_conf,
                "tok_in": tok_in, "tok_out": tok_out, "cost": cost, "cache_hit": cache_hit,
            }
            _track_usage(tok_in, tok_out, cost)
            st.session_state["rag_res"] = res
            render_result(res, streamed=True)

# Persisted answer block: keeps the result (and the 👍/👎 buttons) alive on
# reruns triggered by feedback clicks.
if not asked and st.session_state.get("rag_res") is not None:
    render_result(st.session_state["rag_res"], streamed=False)

if question.strip():
    with st.expander(T["ab"]):
        if st.button(T["compare"], key="ab_all"):
            rows = []
            for name in STRATEGIES:
                t0 = time.time()
                try:
                    ds, _w, _h = _run_retrieval(name, question.strip(), top_k, rerank_top, (), (),
                                            corpus["collection"])
                    rows.append({"strategy": name, "docs": len(ds), "s": round(time.time() - t0, 2),
                                 "top score": round(max((float(d[2]) for d in ds), default=0.0), 3),
                                 "top doc": (ds[0][0] if ds else "—")})
                except Exception as e:  # noqa: BLE001
                    rows.append({"strategy": name, "docs": 0, "s": round(time.time() - t0, 2),
                                 "top score": 0.0, "top doc": f"err: {type(e).__name__}"})
            st.dataframe(rows, use_container_width=True, hide_index=True)

    with st.expander(T["trace"]):
        if st.button(T["trace_btn"], key="trace_btn"):
            try:
                from module_5_retrieval import set_collection, trace_hybrid
                set_collection(corpus["collection"])
                tr = trace_hybrid(question.strip(), k=top_k)
                c1, c2, c3 = st.columns(3)
                for col, key, title in ((c1, "dense", "Dense"), (c2, "sparse", "Sparse"), (c3, "fused", "Fused (RRF)")):
                    with col:
                        st.markdown(f"**{title}**")
                        for d in tr[key][:8]:
                            st.caption(f"`{d[0]}` · {round(float(d[2]), 3)}")
                            st.text((d[1] or "")[:120])
            except Exception as e:  # noqa: BLE001
                st.error(f"Trace failed: {e}")


def load_benchmarks() -> dict:
    path = os.path.join(EVAL_DIR, "results_retrieval.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        return {}
    latest = {}
    for run in history:
        for row in run.get("rows", []):
            latest[row["strategy"]] = {**row, "tag": run.get("tag", "")}
    return latest


def load_generation_benchmarks() -> dict:
    path = os.path.join(EVAL_DIR, "results_generation.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def bench_provenance() -> str:
    """Where the static tables come from — so nobody mistakes them for live runs."""
    parts = []
    rpath = os.path.join(EVAL_DIR, "results_retrieval.json")
    if os.path.exists(rpath):
        try:
            with open(rpath, encoding="utf-8") as f:
                hist = json.load(f)
            tags = sorted({r.get("tag", "") for r in hist if r.get("tag")})
            parts.append(f"retrieval `results_retrieval.json` · {len(hist)} runs · tags: {', '.join(tags)}")
        except Exception:
            pass
    g = load_generation_benchmarks()
    if g:
        parts.append(f"generation `results_generation.json` · ts {str(g.get('ts', ''))[:10]} "
                     f"· tag `{g.get('tag', '')}` · n={g.get('n')}")
    parts.append("snapshot from a previous offline run — not computed on this page")
    return " · ".join(parts)


LIVE_BENCH_STRATEGIES = ["dense_only", "sparse_only", "hybrid", "hybrid_diverse",
                         "hybrid_hyde", "dense_hyde", "hybrid_ce", "multi_query"]


def run_live_benchmark(names, limit, collection=None, eval_file="eval_set.json"):
    """Aggregate Hit@K / MRR@10 / NDCG@10 over the eval set, live on this machine."""
    from eval_retrieval import build_strategies, hit_rate_at_k, mrr_at_k, ndcg_at_k
    from module_5_retrieval import set_collection

    if collection:
        set_collection(collection)
    with open(os.path.join(EVAL_DIR, eval_file), encoding="utf-8") as f:
        items = json.load(f)["items"][:limit]

    rows = []
    for name, fn in build_strategies(names):
        h5 = h10 = mrr = ndcg = 0.0
        lat = []
        for it in items:
            t0 = time.time()
            ranked = fn(it["query"], 10)
            lat.append(time.time() - t0)
            h5 += hit_rate_at_k(ranked, it["relevant"], 5)
            h10 += hit_rate_at_k(ranked, it["relevant"], 10)
            mrr += mrr_at_k(ranked, it["relevant"], 10)
            ndcg += ndcg_at_k(ranked, it["relevant"], 10)
        n = len(items)
        lat.sort()
        rows.append({
            "strategy": name, "n": n,
            "Hit@5": round(h5 / n, 3), "Hit@10": round(h10 / n, 3),
            "MRR@10": round(mrr / n, 3), "NDCG@10": round(ndcg / n, 3),
            "avg s": round(sum(lat) / n, 2),
            "p95 s": round(lat[int(n * 0.95) - 1], 2),
        })
    return rows


BENCH_T = {
    "ru": {"sub": "Retrieval benchmarks",
           "cap": "Оффлайн-оценка на 100 вопросах MS MARCO (qrels train.tsv).",
           "none": "Нет результатов — запусти `python hub/eval/eval_retrieval.py`.",
           "gen_sub": "Генерация (LLM-судья)",
           "gen_cap": "Faithfulness / answer relevancy / валидность цитат.",
           "strategy": "Стратегия"},
    "en": {"sub": "Retrieval benchmarks",
           "cap": "Offline evaluation on 100 MS MARCO questions (qrels train.tsv).",
           "none": "No results yet — run `python hub/eval/eval_retrieval.py`.",
           "gen_sub": "Generation (LLM judge)",
           "gen_cap": "Faithfulness / answer relevancy / citation validity.",
           "strategy": "Strategy"},
}[lang]

st.divider()

bench = load_benchmarks()
gen = load_generation_benchmarks()

with st.expander(T["bench_static"], expanded=False):
    st.caption(bench_provenance())

    st.markdown(f"**{T['bench_r']}**")
    st.caption(BENCH_T["cap"])
    if not bench:
        st.info(BENCH_T["none"])
    else:
        order = ["dense_only", "sparse_only", "hybrid", "hybrid_diverse", "dense_hyde",
                 "hybrid_hyde", "hybrid_ce", "w0.0", "w0.25"]
        labels = {"hybrid_ce": "Hybrid + CrossEncoder (best)", "w0.0": "Weighted RRF (w_sparse=0.0)"}
        rows = [{
            BENCH_T["strategy"]: labels.get(k, k),
            "Hit@5": bench[k].get("hit@5"), "Hit@10": bench[k].get("hit@10"),
            "MRR@10": bench[k].get("mrr@10"), "NDCG@10": bench[k].get("ndcg@10"),
            "avg s": bench[k].get("avg_latency_s"),
        } for k in order if k in bench]
        st.dataframe(rows, use_container_width=True, hide_index=True)

    st.markdown(f"**{T['bench_g']}**")
    st.caption(BENCH_T["gen_cap"])
    if not gen:
        st.info(BENCH_T["none"])
    else:
        judge = gen.get("judge", {})
        ans = gen.get("answerer", {})
        s = gen.get("summary", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Faithfulness", f"{s.get('faithfulness', 0):.3f}")
        c2.metric("Answer relevancy", f"{s.get('answer_relevancy', 0):.3f}")
        c3.metric("Citations valid", f"{s.get('citation_valid_rate', 0):.3f}")
        c4.metric("avg", f"{s.get('avg_latency_s', 0):.1f}s")
        st.caption(f"judge `{judge.get('served', '?')}` · answerer `{ans.get('served', '?')}` · n={gen.get('n')}")
        st.dataframe(gen.get("rows", []), use_container_width=True, hide_index=True)

with st.expander(T["live_sub"], expanded=False):
    st.caption(f"{T['live_cap']} · `{corpus['eval_set']}` · {corpus_key}")
    live_strats = st.multiselect(T["live_strats"], LIVE_BENCH_STRATEGIES,
                                 default=["dense_only", "sparse_only", "hybrid"])
    live_limit = st.slider(T["live_limit"], 5, 100, 10, 5)
    st.caption(T["live_note"])
    if st.button(T["live_run"], type="primary", key="live_run"):
        if not live_strats:
            st.warning("—")
        else:
            with st.spinner("..."):
                try:
                    live_rows = run_live_benchmark(live_strats, live_limit,
                                                   corpus["collection"], corpus["eval_set"])
                    st.dataframe(live_rows, use_container_width=True, hide_index=True)
                except Exception as e:  # noqa: BLE001
                    st.error(f"{type(e).__name__}: {e}")
