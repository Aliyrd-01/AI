"""Benchmarks — RAG retrieval/generation metrics + LLM model comparison (RU/EN)."""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, ".."))
EVAL_DIR = os.path.join(HUB, "eval")
sys.path.insert(0, HUB)

import streamlit as st
from i18n import lang_switcher

st.set_page_config(page_title="Benchmarks", page_icon="📊", layout="wide")

lang = lang_switcher()


def _load(name):
    path = os.path.join(EVAL_DIR, name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


T = {
    "ru": {
        "title": "📊 Benchmarks",
        "caption": "Измеряемое качество: retrieval, генерация и сравнение LLM по бенчмаркам.",
        "rag_tab": "RAG (retrieval + generation)",
        "llm_tab": "LLM models",
        "rag_sub": "Retrieval — 100 вопросов MS MARCO",
        "none": "Нет `results_retrieval.json`.",
        "gen_sub": "Generation — LLM-судья",
        "gen_none": "Нет `results_generation.json`.",
        "judge": "Судья",
        "answerer": "Отвечающий",
        "llm_sub": "LLM Benchmark Suite",
        "llm_d": "TruthfulQA (галлюцинации), GSM8K (математика), BBH (логика) — сравнение моделей.",
        "llm_none": "Нет `bench_free_results.json`.",
        "model": "Model",
        "src": "Источник",
        "concl": "Ключевой вывод: основной прирост даёт **CrossEncoder**; HyDE и multi-query "
                 "на этом корпусе не помогают.",
    },
    "en": {
        "title": "📊 Benchmarks",
        "caption": "Measured quality: retrieval, generation and LLM comparison on benchmarks.",
        "rag_tab": "RAG (retrieval + generation)",
        "llm_tab": "LLM models",
        "rag_sub": "Retrieval — 100 MS MARCO questions",
        "none": "No `results_retrieval.json`.",
        "gen_sub": "Generation — LLM judge",
        "gen_none": "No `results_generation.json`.",
        "judge": "Judge",
        "answerer": "Answerer",
        "llm_sub": "LLM Benchmark Suite",
        "llm_d": "TruthfulQA (hallucinations), GSM8K (math), BBH (logic) — model comparison.",
        "llm_none": "No `bench_free_results.json`.",
        "model": "Model",
        "src": "Source",
        "concl": "Key finding: the main gain comes from the **CrossEncoder**; HyDE and multi-query "
                 "do not help on this corpus.",
    },
}[lang]

st.title(T["title"])
st.caption(T["caption"])

tab_rag, tab_llm = st.tabs([T["rag_tab"], T["llm_tab"]])

with tab_rag:
    st.subheader(T["rag_sub"])
    hist = _load("results_retrieval.json")
    if not hist:
        st.info(T["none"])
    else:
        latest = {}
        for run in hist:
            for row in run.get("rows", []):
                latest[row["strategy"]] = row
        order = ["dense_only", "sparse_only", "hybrid", "hybrid_diverse", "dense_hyde",
                 "hybrid_hyde", "hybrid_ce", "w0.0", "w0.25"]
        labels = {"hybrid_ce": "Hybrid + CrossEncoder (best)"}
        rows = [{
            "Strategy": labels.get(k, k),
            "Hit@5": latest[k].get("hit@5"), "Hit@10": latest[k].get("hit@10"),
            "MRR@10": latest[k].get("mrr@10"), "NDCG@10": latest[k].get("ndcg@10"),
            "avg s": latest[k].get("avg_latency_s"),
        } for k in order if k in latest]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.caption(T["concl"])

    st.subheader(T["gen_sub"])
    gen = _load("results_generation.json")
    if not gen:
        st.info(T["gen_none"])
    else:
        s = gen.get("summary", {})
        judge = gen.get("judge", {})
        ans = gen.get("answerer", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Faithfulness", f"{s.get('faithfulness', 0):.3f}")
        c2.metric("Answer relevancy", f"{s.get('answer_relevancy', 0):.3f}")
        c3.metric("Citations valid", f"{s.get('citation_valid_rate', 0):.3f}")
        c4.metric("avg", f"{s.get('avg_latency_s', 0):.1f}s")
        st.caption(f"{T['judge']}: `{judge.get('served', '?')}` · {T['answerer']}: "
                   f"`{ans.get('served', '?')}` · n={gen.get('n')}")
        st.dataframe(gen.get("rows", []), use_container_width=True, hide_index=True)

with tab_llm:
    st.subheader(T["llm_sub"])
    st.write(T["llm_d"])
    bench = _load("bench_free_results.json")
    if not bench:
        st.info(T["llm_none"])
    else:
        tqa = bench.get("tqa", {})
        gb = bench.get("gsm_bbh", {})
        names = sorted(set(tqa) | set(gb))
        rows = []
        for n in names:
            rows.append({
                T["model"]: n,
                "TruthfulQA acc %": tqa.get(n, {}).get("acc"),
                "GSM8K %": gb.get(n, {}).get("gsm8k"),
                "BBH %": gb.get(n, {}).get("bbh"),
                "Total %": gb.get(n, {}).get("total"),
            })
        rows.sort(key=lambda r: (r["Total %"] or 0), reverse=True)
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.caption(T["src"] + ": `projects/hallucination-benchmark`")
