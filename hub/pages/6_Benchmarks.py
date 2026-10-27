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
        "caption": "Мы строим RAG-системы и доказываем качество цифрами: retrieval, генерация и сравнение LLM на публичных бенчмарках.",
        "rag_tab": "RAG (retrieval + generation)",
        "llm_tab": "LLM models",
        "rag_sub": "Retrieval — 100 вопросов MS MARCO",
        "none": "Нет `results_retrieval.json`.",
        "gen_sub": "Generation — LLM-судья",
        "gen_none": "Нет `results_generation.json`.",
        "ref_sub": "Отказы (OOD) — честность системы",
        "ref_none": "Нет `results_refusal.json` — прогони `python hub/eval/eval_refusal.py`.",
        "ref_rate": "Refusal rate (OOD)", "ref_target": "цель ≥",
        "ref_false": "Ложные отказы (in-corpus)", "ref_false_max": "не больше",
        "ref_verdict": "Вердикт", "ref_rows_cap": "refusal_rate по N вопросам вне корпуса + "
                         "контроль на in-corpus вопросах; сигналы: нет валидной цитаты / "
                         "модель сама отказалась / низкая уверенность retrieval.",
        "ref_run": "Прогнать заново: `python hub/eval/eval_refusal.py`",
        "judge": "Судья",
        "answerer": "Отвечающий",
        "llm_sub": "LLM Benchmark Suite",
        "llm_d": "MMLU (knowledge), TruthfulQA (hallucinations), GSM8K (math), BBH (logic), HumanEval (code) — 8 models of the same class, one prompt set and one grader.",
        "llm_none": "Нет `bench_free_results.json`.",
        "llm_meta": "n на датасет: MMLU 100 · TruthfulQA 60 · GSM8K 50 · BBH 25 · HumanEval 30. "
                    "Одинаковые промпты и грейдеры; латентность и ошибки логируются.",
        "model": "Model",
        "avg_col": "Среднее",
        "src": "Источник",
        "chart_cap": "Средний балл по 5 тестам: выше — лучше.",
        "dl": "Скачать данные (JSON)",
        "meth_h": "Методология",
        "meth_b": "Датасеты: MMLU (knowledge), TruthfulQA (hallucinations), GSM8K (math), "
                  "BBH (logic), HumanEval (code). Для всех моделей — одни и те же промпты, "
                  "temperature 0 и автоматический грейдер. Accuracy = верных / отвеченных. "
                  "`err` — сетевые ошибки после ретраев (на отвеченном подмножестве accuracy не занижается). "
                  "Латентность — среднее время одного запроса, секунды.",
        "err_note": "С ошибками транспорта: {x} — accuracy считается по отвеченным.",
        "testing_link": "Что мы проверяем в RAG и агентах — страница Testing",
        "concl": "Ключевой вывод: основной прирост даёт **CrossEncoder**; HyDE и multi-query "
                 "на этом корпусе не помогают.",
        "offer_h": "**RAG как услуга: что вы получаете**",
        "offer_b": "Этот дашборд — не «мы что-то померили», а часть поставки. Заказывая у нас RAG-систему, "
                   "вы получаете: 1) работающий поиск по вашим данным; 2) выбор retrieval-стратегии по "
                   "цифрам (Hit@5/10, MRR@10, NDCG@10, латентность); 3) контроль качества генерации — "
                   "faithfulness, answer relevancy, валидность цитат по каждому вопросу; 4) зафиксированную "
                   "баз-линию, чтобы после доработок и пополнения базы доказать, что качество не упало.",
        "offer_cta": "Хотите такой же дашборд на своих данных — напишите нам: pipeline, judge и графики поставляются вместе с системой.",
    },
    "en": {
        "title": "📊 Benchmarks",
        "caption": "We build RAG systems and prove quality with numbers: retrieval, generation and LLM comparison on public benchmarks.",
        "rag_tab": "RAG (retrieval + generation)",
        "llm_tab": "LLM models",
        "rag_sub": "Retrieval — 100 MS MARCO questions",
        "none": "No `results_retrieval.json`.",
        "gen_sub": "Generation — LLM judge",
        "gen_none": "No `results_generation.json`.",
        "ref_sub": "Refusals (OOD) — system honesty",
        "ref_none": "No `results_refusal.json` — run `python hub/eval/eval_refusal.py`.",
        "ref_rate": "Refusal rate (OOD)", "ref_target": "target ≥",
        "ref_false": "False refusals (in-corpus)", "ref_false_max": "max",
        "ref_verdict": "Verdict", "ref_rows_cap": "refusal_rate over questions outside the corpus "
                         "plus an in-corpus control; signals: no valid citation / model refused / "
                         "low retrieval confidence.",
        "ref_run": "Re-run: `python hub/eval/eval_refusal.py`",
        "judge": "Judge",
        "answerer": "Answerer",
        "llm_sub": "LLM Benchmark Suite",
        "llm_d": "MMLU (knowledge), TruthfulQA (hallucinations), GSM8K (math), BBH (logic), HumanEval (code) — 8 models of the same class, one prompt set and one grader.",
        "llm_none": "No `bench_free_results.json`.",
        "llm_meta": "n per dataset: MMLU 100 · TruthfulQA 60 · GSM8K 50 · BBH 25 · HumanEval 30. "
                    "Same prompts and graders; latency and errors are logged.",
        "model": "Model",
        "avg_col": "Average",
        "src": "Source",
        "chart_cap": "Average score across all 5 tests: higher is better.",
        "dl": "Download data (JSON)",
        "meth_h": "Methodology",
        "meth_b": "Datasets: MMLU (knowledge), TruthfulQA (hallucinations), GSM8K (math), "
                  "BBH (logic), HumanEval (code). Every model gets the same prompts, "
                  "temperature 0 and an automatic grader. Accuracy = correct / answered. "
                  "`err` = transport errors after retries (accuracy is not penalized on the answered subset). "
                  "Latency = average seconds per request.",
        "err_note": "Transport errors on: {x} — accuracy is computed on answered items only.",
        "testing_link": "What we test in RAG and agents — Testing page",
        "concl": "Key finding: the main gain comes from the **CrossEncoder**; HyDE and multi-query "
                 "do not help on this corpus.",
        "offer_h": "**RAG as a service: what you get**",
        "offer_b": "This dashboard is not \"we measured something\" — it is part of the delivery. When we "
                   "build a RAG system for you, you get: 1) working search over your data; 2) the "
                   "retrieval strategy chosen by numbers (Hit@5/10, MRR@10, NDCG@10, latency); "
                   "3) measured generation quality — faithfulness, answer relevancy and citation "
                   "validity per question; 4) a fixed baseline so future re-indexing and data growth "
                   "are provably not degrading your answer quality.",
        "offer_cta": "Want the same dashboard on your data — get in touch: pipeline, judge and charts ship with the system.",
    },
}[lang]

st.title(T["title"])
st.caption(T["caption"])

tab_rag, tab_llm = st.tabs([T["rag_tab"], T["llm_tab"]])

with tab_rag:
    st.subheader(T["rag_sub"])
    with st.container(border=True):
        st.markdown(T["offer_h"])
        st.write(T["offer_b"])
        st.info(T["offer_cta"])
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
        c4.metric("avg eval, s", f"{s.get('avg_latency_s', 0):.1f}s")
        st.caption(f"{T['judge']}: `{judge.get('served', '?')}` · {T['answerer']}: "
                   f"`{ans.get('served', '?')}` · n={gen.get('n')}")
        st.dataframe(gen.get("rows", []), use_container_width=True, hide_index=True)

    st.subheader(T["ref_sub"])
    ref = _load("results_refusal.json")
    if not ref:
        st.info(T["ref_none"])
    else:
        rs = ref.get("summary", {})
        params = ref.get("params", {})
        c1, c2, c3 = st.columns(3)
        c1.metric(T["ref_rate"], f"{rs.get('refusal_rate', 0):.3f}",
                  f"{T['ref_target']} {params.get('target', 0.7):.2f}")
        c2.metric(T["ref_false"], f"{rs.get('false_refusal_rate', 0):.3f}",
                  f"{T['ref_false_max']} {params.get('max_false_refusal', 0.1):.2f}")
        c3.metric(T["ref_verdict"], "PASS ✅" if rs.get("passed") else "FAIL ❌")
        st.caption(T["ref_rows_cap"] + f" · {ref.get('ts', '')}")
        st.dataframe(ref.get("rows", []), use_container_width=True, hide_index=True)
        st.code(T["ref_run"], language=None)

with tab_llm:
    st.subheader(T["llm_sub"])
    st.write(T["llm_d"])
    bench = _load("bench_free_results.json")
    if not bench:
        st.info(T["llm_none"])
    else:
        meta = bench.get("meta", {})
        res = bench.get("results", {})
        if res:
            ds_order = meta.get("datasets") or ["mmlu", "truthfulqa", "gsm8k", "bbh", "humaneval"]
            ds_names = {
                "mmlu": "MMLU", "truthfulqa": "TruthfulQA", "gsm8k": "GSM8K",
                "bbh": "BBH", "humaneval": "HumanEval",
            }
            rows = []
            errs = []
            for m, cell in res.items():
                row = {T["model"]: cell.get("label", m)}
                lats = []
                for ds in ds_order:
                    v = cell.get(ds, {}).get("acc")
                    row[ds_names[ds]] = round(v * 100, 1) if v is not None else None
                    d = cell.get(ds, {})
                    if d.get("latency_s") is not None:
                        lats.append(d["latency_s"])
                    if d.get("err"):
                        errs.append(f"{cell.get('label', m)} · {ds_names[ds]}: "
                                    f"{d['err']} err / {d.get('answered', '?')} answered")
                row["s"] = round(sum(lats) / len(lats), 2) if lats else None
                row[T["avg_col"]] = round(cell["avg"] * 100, 1) if cell.get("avg") is not None else None
                rows.append(row)
            rows.sort(key=lambda r: (r[T["avg_col"]] or 0), reverse=True)
            st.dataframe(rows, use_container_width=True, hide_index=True)
            st.caption(T["llm_meta"])
            if errs:
                st.caption(T["err_note"].format(x="; ".join(errs)))
            st.caption(T["chart_cap"])
            chart_rows = [{T["model"]: r[T["model"]], T["avg_col"]: r[T["avg_col"]]} for r in rows]
            st.dataframe(
                chart_rows,
                use_container_width=True,
                hide_index=True,
                column_config={
                    T["avg_col"]: st.column_config.ProgressColumn(
                        T["avg_col"], min_value=0, max_value=100, format="%.1f"
                    )
                },
            )
            with st.expander(T["meth_h"]):
                st.write(T["meth_b"])
                if meta.get("generated"):
                    st.caption(f"run: {meta['generated']}")
            st.download_button(
                T["dl"],
                data=json.dumps(bench, ensure_ascii=False, indent=2),
                file_name="llm_benchmarks.json",
                mime="application/json",
            )
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

    st.page_link("pages/9_Testing.py", label=T["testing_link"], icon="🧪")
