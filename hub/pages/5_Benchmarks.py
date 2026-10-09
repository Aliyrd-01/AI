"""Benchmarks — RAG retrieval/generation metrics + LLM model comparison."""

import json
import os

import streamlit as st

st.set_page_config(page_title="Benchmarks", page_icon="📊", layout="wide")

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL_DIR = os.path.abspath(os.path.join(HERE, "..", "eval"))


def _load(name):
    path = os.path.join(EVAL_DIR, name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


st.title("📊 Benchmarks")
st.caption("Измеряемое качество: retrieval, генерация и сравнение LLM по бенчмаркам.")

tab_rag, tab_llm = st.tabs(["RAG (retrieval + generation)", "LLM models"])

with tab_rag:
    st.subheader("Retrieval — 100 вопросов MS MARCO")
    hist = _load("results_retrieval.json")
    if not hist:
        st.info("Нет `results_retrieval.json`.")
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
        st.caption("Ключевой вывод: основной прирост даёт **CrossEncoder**; HyDE и multi-query "
                   "на этом корпусе не помогают.")

    st.subheader("Generation — LLM-судья")
    gen = _load("results_generation.json")
    if not gen:
        st.info("Нет `results_generation.json`.")
    else:
        s = gen.get("summary", {})
        j = gen.get("judge", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Faithfulness", f"{s.get('faithfulness', 0):.3f}")
        c2.metric("Answer relevancy", f"{s.get('answer_relevancy', 0):.3f}")
        c3.metric("Citations valid", f"{s.get('citation_valid_rate', 0):.3f}")
        c4.metric("avg", f"{s.get('avg_latency_s', 0):.1f}s")
        st.caption(f"Судья: `{j.get('served', '?')}` · отвечающий: "
                   f"`{gen.get('answerer', {}).get('served', '?')}` · n={gen.get('n')}")

with tab_llm:
    st.subheader("LLM Benchmark Suite")
    st.write("TruthfulQA (галлюцинации), GSM8K (математика), BBH (логика) — сравнение моделей.")
    bench = _load("bench_free_results.json")
    if not bench:
        st.info("Нет `bench_free_results.json`.")
    else:
        tqa = bench.get("tqa", {})
        gb = bench.get("gsm_bbh", {})
        names = sorted(set(tqa) | set(gb))
        rows = []
        for n in names:
            rows.append({
                "Model": n,
                "TruthfulQA acc %": tqa.get(n, {}).get("acc"),
                "GSM8K %": gb.get(n, {}).get("gsm8k"),
                "BBH %": gb.get(n, {}).get("bbh"),
                "Total %": gb.get(n, {}).get("total"),
            })
        rows.sort(key=lambda r: (r["Total %"] or 0), reverse=True)
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.caption("Источник: `D:\\AI\\hallucination-benchmark`. Значения — доли корректных ответов.")
