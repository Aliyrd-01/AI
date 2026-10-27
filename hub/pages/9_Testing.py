"""Testing service page — RAG & Agent quality assurance as a standalone offer. (RU/EN)"""

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
        "caption": "Не «у нас работает» — а измеренное качество с цифрами и баз-линией. "
                   "Тестирование как отдельная услуга: до внедрения, после доработок и на каждом релизе.",
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
        "proof_h": "**Это не слайды — это наши же метрики**",
        "proof_b": "Retrieval-бенчмарки на MS MARCO (Hit@K / MRR / NDCG по 8 стратегиям), RAGAS-оценка "
                   "генерации с кросс-модельным судьёй, сравнение 8 LLM на MMLU / TruthfulQA / GSM8K / BBH / "
                   "HumanEval — всё открыто на странице Benchmarks и воспроизводится скриптами.",
        "proof_cta": "Посмотреть цифры → вкладка Benchmarks",
    },
    "en": {
        "title": "🧪 RAG & Agent Testing",
        "caption": "Not \"it works for us\" — measured quality with numbers and a baseline. "
                   "Testing as a standalone service: before rollout, after changes, and on every release.",
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
        "proof_h": "**Not slides — our own metrics**",
        "proof_b": "Retrieval benchmarks on MS MARCO (Hit@K / MRR / NDCG across 8 strategies), RAGAS generation "
                   "scoring with a cross-model judge, an 8-model comparison on MMLU / TruthfulQA / GSM8K / BBH / "
                   "HumanEval — all open on the Benchmarks page and reproducible with scripts.",
        "proof_cta": "See the numbers → Benchmarks tab",
    },
}[lang]

st.title(T["title"])
st.caption(T["caption"])

with st.container(border=True):
    st.markdown(T["offer_h"])
    st.write(T["offer_b"])
    st.info(T["cta"])

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

with st.container(border=True):
    st.markdown(T["proof_h"])
    st.write(T["proof_b"])
    st.markdown(f"[{T['proof_cta']}](Benchmarks)")
