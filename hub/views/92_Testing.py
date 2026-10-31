"""Testing service page — RAG & Agent quality assurance as a standalone offer. (RU/EN)"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HUB)

import streamlit as st
from i18n import lang_switcher

st.set_page_config(page_title="RAG & Agent Testing", page_icon="🧪", layout="wide")

lang = lang_switcher()

T = {
    "ru": {
        "title": "🧪 Тестирование RAG и Agents",
        "caption": "Измеряем качество RAG-систем и агентов: метрики, баз-линия, отчёт с приоритетами. "
                   "Подключается до внедрения, после доработок и на каждом релизе.",
        "offer_h": "**Что вы получаете**",
        "offer_b": "1) Набор тестов на ваши данные: вопросы с эталонными ответами или сценарии для агентов. "
                   "2) Метрики качества с прозрачной методикой: retrieval (Hit@K, MRR, NDCG), генерация "
                   "(faithfulness, answer relevancy, валидность цитат), агенты (правильность вызовов "
                   "инструментов, завершение задачи, лимиты шагов). 3) Зафиксированную баз-линию — "
                   "чтобы любая деградация после правок была видна сразу. 4) Отчёт: где падает, почему, "
                   "что чинить в первую очередь.",
        "cta": "Есть RAG или агент в проде? Прогоним его по нашей методике и отдадим pass/fail-баз-линию. "
               "Напишите нам.",
        "what_h": "**Что тестируем**",
        "rag_h": "RAG-системы",
        "rag_b": "Поиск: Hit@5/10, MRR@10, NDCG@10, латентность по стратегиям (dense / sparse / hybrid / rerank). "
                 "Генерация: faithfulness, answer relevancy (RAGAS), корректность отказов, валидность цитат — "
                 "каждая ссылка [n] сверяется с реально извлечённым чанком.",
        "ag_h": "AI-агенты",
        "ag_b": "Правильность выбора и аргументов инструментов, завершение задачи на сценариях, "
                "устойчивость к битым входам, лимиты шагов и петель, стоимость и латентность на задачу, "
                "поведение при отказе инструмента.",
        "how_h": "**Как это устроено**",
        "s1": "1 · Eval-набор",
        "s1d": "Собираем golden-вопросы / сценарии на ваших данных и домене.",
        "s2": "2 · Прогон",
        "s2d": "Харнесс гоняет систему одинаковыми промптами, логирует каждый шаг.",
        "s3": "3 · Судья",
        "s3d": "LLM-судья, независимый от отвечающей модели, + структурные проверки цитат и вызовов.",
        "s4": "4 · Отчёт и CI",
        "s4d": "Цифры, примеры падений, приоритеты. Баз-линия встраивается в CI как quality gate.",
        "proof_h": "**Наши собственные измерения**",
        "proof_b": "Retrieval-бенчмарки на MS MARCO (Hit@K / MRR / NDCG: dense / sparse / hybrid, HyDE, "
                   "CrossEncoder-rerank, multi-query), RAGAS-оценка генерации с кросс-модельным судьёй, "
                   "замер честности — refusal rate на OOD-вопросах (страница Benchmarks), сравнение 8 LLM "
                   "на MMLU / TruthfulQA / GSM8K / BBH / HumanEval — всё открыто и воспроизводится скриптами.",
        "proof_cta": "Посмотреть цифры → вкладка Benchmarks",
        "contact_l": "Обсудить тестирование → Контакты",
        "fmt_h": "**Форматы работы**",
        "f1_t": "Оценка до внедрения",
        "f1_d": "Разовый прогон по методике: баз-линия и отчёт с приоритетами. Около недели.",
        "f2_t": "Регресс после доработок",
        "f2_d": "Тот же набор после правок: дельта к баз-линии и список сломанного. Один день.",
        "f3_t": "Quality gate в CI",
        "f3_d": "Автопрогон на каждый релиз: падение метрик блокирует merge. Настройка 2–3 дня.",
        "rep_h": "**Пример отчёта**",
        "rep_cap": "Фрагмент последнего полного прогона (после мержа, 100 вопросов, MS MARCO): сводная "
                   "таблица стратегий из отчёта. Реранк-вариант hybrid_ce на этом же наборе — "
                   "Hit@5 0.86 / NDCG@10 0.73 (прогон final-ce). Полные JSON, примеры падений "
                   "и приоритеты передаются вместе с баз-линией.",
        "faq_h": "**Частые вопросы**",
        "faq": [
            ("Сколько данных нужно для старта?",
             "Хватит 30–50 вопросов с эталонными ответами. Собираем вместе: по вашей документации, "
             "тикетам и логам реальных запросов."),
            ("Нужен ли доступ к прод-данным?",
             "Нет. Достаточно репрезентативной выборки корпуса и доступа к API тестируемой системы; "
             "секреты и PII нам не передаются."),
            ("Чем это отличается от «прогнать RAGAS»?",
             "RAGAS — только часть пайплайна. Главное — golden-набор на вашем домене, воспроизводимый "
             "харнесс и баз-линия, встроенная в CI."),
            ("Сколько это занимает?",
             "Первая оценка — около недели. Регресс после доработок — день. Quality gate в CI — "
             "настройка 2–3 дня."),
            ("Насколько объективен судья?",
             "LLM-судья — не та модель, которая отвечает, плюс структурные проверки (цитаты, вызовы "
             "инструментов), которые от судьи не зависят."),
        ],
    },
    "en": {
        "title": "🧪 RAG & Agent Testing",
        "caption": "Measured quality for RAG systems and agents: metrics, a baseline, and a report with "
                   "priorities. Fits before rollout, after changes, and on every release.",
        "offer_h": "**What you get**",
        "offer_b": "1) A test set on your data: questions with reference answers, or scenarios for agents. "
                   "2) Quality metrics with a transparent method: retrieval (Hit@K, MRR, NDCG), generation "
                   "(faithfulness, answer relevancy, citation validity), agents (tool-call correctness, task "
                   "completion, step limits). 3) A fixed baseline, so any regression after changes is visible "
                   "immediately. 4) A report: where it fails, why, and what to fix first.",
        "cta": "Have a RAG system or an agent in production? We will run it through our methodology and hand "
               "you a pass/fail baseline. Get in touch.",
        "what_h": "**What we test**",
        "rag_h": "RAG systems",
        "rag_b": "Retrieval: Hit@5/10, MRR@10, NDCG@10, latency per strategy (dense / sparse / hybrid / rerank). "
                 "Generation: faithfulness, answer relevancy (RAGAS), correct refusals, citation validity — "
                 "every [n] citation is checked against a chunk that was actually retrieved.",
        "ag_h": "AI agents",
        "ag_b": "Tool selection and argument correctness, task completion on scenarios, robustness to broken "
                "input, step and loop limits, cost and latency per task, behaviour when a tool fails.",
        "how_h": "**How it works**",
        "s1": "1 · Eval set",
        "s1d": "We build golden questions / scenarios on your data and domain.",
        "s2": "2 · Run",
        "s2d": "The harness runs the system with identical prompts and logs every step.",
        "s3": "3 · Judge",
        "s3d": "A judge LLM independent from the answering model, plus structural checks of citations and calls.",
        "s4": "4 · Report & CI",
        "s4d": "Numbers, failure examples, priorities. The baseline becomes a CI quality gate.",
        "proof_h": "**Our own measurements**",
        "proof_b": "Retrieval benchmarks on MS MARCO (Hit@K / MRR / NDCG across dense / sparse / hybrid, "
                   "HyDE, CrossEncoder rerank, multi-query), RAGAS generation scoring with a cross-model "
                   "judge, an OOD refusal-rate benchmark (honesty on questions outside the corpus — see "
                   "the Benchmarks page), and an 8-model comparison on MMLU / TruthfulQA / GSM8K / BBH / "
                   "HumanEval — all open and reproducible with scripts.",
        "proof_cta": "See the numbers → Benchmarks tab",
        "contact_l": "Discuss a test run → Contacts",
        "fmt_h": "**Engagement formats**",
        "f1_t": "Pre-rollout assessment",
        "f1_d": "One-shot run through our method: a baseline and a prioritised report. About a week.",
        "f2_t": "Regression after changes",
        "f2_d": "The same set after edits: delta vs baseline and the list of what broke. One day.",
        "f3_t": "CI quality gate",
        "f3_d": "Automatic run on every release: metric drops block the merge. Setup in 2–3 days.",
        "rep_h": "**Sample report**",
        "rep_cap": "A fragment of the latest full run (post-merge, 100 questions, MS MARCO): the strategy "
                   "summary table from the report. The rerank variant hybrid_ce scores Hit@5 0.86 / "
                   "NDCG@10 0.73 on the same set (final-ce run). Full JSONs, failure examples and "
                   "priorities are delivered together with the baseline.",
        "faq_h": "**FAQ**",
        "faq": [
            ("How much data do you need to start?",
             "30–50 questions with reference answers is enough. We build the set together: from your "
             "docs, tickets and real query logs."),
            ("Do you need production data access?",
             "No. A representative corpus sample and API access to the system under test is enough; "
             "secrets and PII are never handed over."),
            ("How is this different from \"running RAGAS\"?",
             "RAGAS is one part of the pipeline. What matters is a golden set on your domain, a "
             "reproducible harness, and a baseline wired into CI."),
            ("How long does it take?",
             "The first assessment is about a week. Regression after changes is a day. A CI quality "
             "gate takes 2–3 days to set up."),
            ("How objective is the judge?",
             "The judge LLM is not the answering model, plus structural checks (citations, tool calls) "
             "that do not depend on the judge at all."),
        ],
    },
}[lang]

st.title(T["title"])
st.caption(T["caption"])

with st.container(border=True):
    st.markdown(T["offer_h"])
    st.write(T["offer_b"])
    st.info(T["cta"])
    st.page_link("views/93_Contacts.py", label=T["contact_l"], icon="✉️")

st.subheader(T["what_h"])
c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        st.markdown(f"**{T['rag_h']}**")
        st.write(T["rag_b"])
with c2:
    with st.container(border=True):
        st.markdown(f"**{T['ag_h']}**")
        st.write(T["ag_b"])

st.subheader(T["how_h"])
c1, c2, c3, c4 = st.columns(4)
for col, h, d in ((c1, T["s1"], T["s1d"]), (c2, T["s2"], T["s2d"]),
                  (c3, T["s3"], T["s3d"]), (c4, T["s4"], T["s4d"])):
    with col:
        with st.container(border=True):
            st.markdown(f"**{h}**")
            st.write(d)

st.subheader(T["fmt_h"].strip("*"))
fc1, fc2, fc3 = st.columns(3)
for col, t_k, d_k in ((fc1, "f1_t", "f1_d"), (fc2, "f2_t", "f2_d"), (fc3, "f3_t", "f3_d")):
    with col:
        with st.container(border=True):
            st.markdown(f"**{T[t_k]}**")
            st.write(T[d_k])


def _sample_rows():
    path = os.path.join(HUB, "eval", "results_retrieval.json")
    try:
        with open(path, encoding="utf-8") as fh:
            tags = json.load(fh)
        for tag in tags:
            if tag.get("tag") != "after-merge":
                continue
            keep = ("dense_only", "sparse_only", "hybrid", "hybrid_diverse")
            keys = ("hit@5", "hit@10", "mrr@10", "ndcg@10", "avg_latency_s")
            return [{k: round(r[k], 3) for k in keys} | {"strategy": r["strategy"]}
                    for r in tag["rows"] if r["strategy"] in keep]
    except Exception:  # noqa: BLE001
        return []
    return []


with st.container(border=True):
    st.markdown(T["proof_h"])
    st.write(T["proof_b"])
    sample = _sample_rows()
    if sample:
        st.markdown(T["rep_h"])
        st.dataframe(sample, hide_index=True, use_container_width=True,
                     column_config={
                         "hit@5": st.column_config.NumberColumn(format="%.2f"),
                         "hit@10": st.column_config.NumberColumn(format="%.2f"),
                         "mrr@10": st.column_config.NumberColumn(format="%.3f"),
                         "ndcg@10": st.column_config.NumberColumn(format="%.2f"),
                         "avg_latency_s": st.column_config.NumberColumn(format="%.1f s"),
                     })
        st.caption(T["rep_cap"])
    st.page_link("views/6_Benchmarks.py", label=T["proof_cta"], icon="📊")

st.subheader(T["faq_h"].strip("*"))
for q, a in T["faq"]:
    with st.expander(q):
        st.write(a)
