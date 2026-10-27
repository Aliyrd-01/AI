"""Portfolio hub — landing page (RU/EN).

Streamlit multi-page entrypoint. Sidebar navigation is generated from ./pages/.
Run locally:  streamlit run hub/Home.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import streamlit as st
from i18n import lang_switcher

st.set_page_config(page_title="AI Portfolio — RAG + n8n", page_icon="🧠", layout="wide")

lang = lang_switcher()

T = {
    "ru": {
        "title": "🧠 AI Portfolio",
        "caption": "RAG-система, n8n-автоматизации и агенты: интерактивное демо + разборы пайплайнов.",
        "rag_t": "🔎 RAG",
        "rag_d": "Гибридный retrieval (dense+sparse RRF), CrossEncoder-реранкинг, цитаты, "
                 "честный отказ, 11 стратегий, замеренные метрики.",
        "rag_l": "Открыть демо →",
        "n8n_t": "🔗 n8n",
        "n8n_d": "3 воркфлоу: Content Publisher (RSS→LLM→Telegram), Lead Qualification "
                 "(MCP + A/B промптов + CRM), AI Support & Escalation.",
        "n8n_l": "Пайплайны →",
        "agents_t": "🤖 Agents",
        "agents_d": "Многоагентная система AutoAgent (triage → File/Web/Coding, "
                    "multi-model по фазам) и 3 примера реализации.",
        "agents_l": "Агенты →",
        "mcp_t": "🔌 MCP",
        "mcp_d": "MCP-серверы к PostgreSQL/MySQL (Streamable HTTP): агент делает SQL "
                 "через чат. Используются в n8n Lead Qualification и Unified Agent.",
        "mcp_l": "MCP серверы →",
        "int_t": "🔌 Интеграции",
        "int_d": "Матрица связей: источники данных и приёмники — протокол, статус в демо "
                 "и что нужно для подключения.",
        "int_l": "Матрица интеграций →",
        "sec_t": "🔐 Безопасность",
        "sec_d": "Read-only SQL, белый список таблиц, PII-маскирование, Bearer-авторизация, лимиты — "
                 "слои защиты и примеры.",
        "sec_l": "Guardrails →",
        "bench_t": "📊 Benchmarks",
        "bench_d": "Метрики retrieval/генерации (Hit@5, NDCG@10, faithfulness) и сравнение LLM "
                   "по TruthfulQA / GSM8K / BBH.",
        "bench_l": "Метрики →",
        "projects_t": "🧩 Проекты",
        "projects_d": "GraphRAG/LightRAG, Telegram-LightRAG-бот, учебные модули — карточки и ссылки.",
        "projects_l": "Все проекты →",
        "ua_t": "🧭 Unified Agent",
        "ua_d": "Один tool-calling агент: сам выбирает RAG-поиск или CRM (PostgreSQL через MCP). "
                "Read-only SQL, белый список таблиц, PII-маскирование, трейс и eval-базлайн.",
        "ua_l": "Открыть агента →",
        "stack": "Стек: Python · Streamlit · Qdrant · FastEmbed · LangChain · n8n · PostgreSQL · MCP · Docker",
        "testing_l": "Тестирование — quality gates и evalы",
        "video_h": "🎬 Демо-видео",
        "video_ru": "Русская озвучка",
        "video_en": "English voiceover",
        "contact_l": "✉️ Контакты — обсудить задачу",
    },
    "en": {
        "title": "🧠 AI Portfolio",
        "caption": "RAG system, n8n automations and agents: interactive demo + pipeline breakdowns.",
        "rag_t": "🔎 RAG",
        "rag_d": "Hybrid retrieval (dense+sparse RRF), CrossEncoder reranking, citations, "
                 "honest refusal, 11 strategies, measured metrics.",
        "rag_l": "Open the demo →",
        "n8n_t": "🔗 n8n",
        "n8n_d": "3 workflows: Content Publisher (RSS→LLM→Telegram), Lead Qualification "
                 "(MCP + A/B prompt testing + CRM), AI Support & Escalation.",
        "n8n_l": "Pipelines →",
        "agents_t": "🤖 Agents",
        "agents_d": "Multi-agent AutoAgent system (triage → File/Web/Coding, multi-model per phase) "
                    "and 3 implementation examples.",
        "agents_l": "Agents →",
        "mcp_t": "🔌 MCP",
        "mcp_d": "MCP servers for PostgreSQL/MySQL (Streamable HTTP): the agent runs SQL through chat. "
                 "Used by n8n Lead Qualification and the Unified Agent.",
        "mcp_l": "MCP servers →",
        "int_t": "🔌 Integrations",
        "int_d": "Connection matrix: data sources and targets — protocol, demo status "
                 "and what it takes to wire them up.",
        "int_l": "Integration matrix →",
        "sec_t": "🔐 Security",
        "sec_d": "Read-only SQL, table allowlist, PII masking, Bearer auth, step limits — "
                 "defence layers with examples.",
        "sec_l": "Guardrails →",
        "bench_t": "📊 Benchmarks",
        "bench_d": "Retrieval/generation metrics (Hit@5, NDCG@10, faithfulness) and LLM comparison "
                   "on TruthfulQA / GSM8K / BBH.",
        "bench_l": "Metrics →",
        "projects_t": "🧩 Projects",
        "projects_d": "GraphRAG/LightRAG, Telegram-LightRAG bot, learning modules — cards and links.",
        "projects_l": "All projects →",
        "ua_t": "🧭 Unified Agent",
        "ua_d": "One tool-calling agent: decides between RAG search and a CRM query "
                "(PostgreSQL via MCP). Read-only SQL, table allowlist, PII masking, trace and eval baseline.",
        "ua_l": "Open the agent →",
        "stack": "Stack: Python · Streamlit · Qdrant · FastEmbed · LangChain · n8n · PostgreSQL · MCP · Docker",
        "testing_l": "Testing — quality gates and evals",
        "video_h": "🎬 Demo video",
        "video_ru": "Russian voiceover",
        "video_en": "English voiceover",
        "contact_l": "✉️ Contacts — discuss a task",
    },
}[lang]

st.title(T["title"])
st.caption(T["caption"])

st.write("")

row1 = st.columns(3, gap="large")
with row1[0]:
    st.subheader(T["rag_t"])
    st.write(T["rag_d"])
    st.page_link("pages/1_RAG.py", label=T["rag_l"])

with row1[1]:
    st.subheader(T["n8n_t"])
    st.write(T["n8n_d"])
    st.page_link("pages/2_N8N.py", label=T["n8n_l"])

with row1[2]:
    st.subheader(T["agents_t"])
    st.write(T["agents_d"])
    st.page_link("pages/3_Agents.py", label=T["agents_l"])

st.write("")
row1b = st.columns(3, gap="large")
with row1b[0]:
    st.subheader(T["mcp_t"])
    st.write(T["mcp_d"])
    st.page_link("pages/4_MCP.py", label=T["mcp_l"])

with row1b[1]:
    st.subheader(T["int_t"])
    st.write(T["int_d"])
    st.page_link("pages/5_Integrations.py", label=T["int_l"])

with row1b[2]:
    st.subheader(T["sec_t"])
    st.write(T["sec_d"])
    st.page_link("pages/7_Security.py", label=T["sec_l"])

st.write("")
row2 = st.columns(3, gap="large")
with row2[0]:
    st.subheader(T["bench_t"])
    st.write(T["bench_d"])
    st.page_link("pages/6_Benchmarks.py", label=T["bench_l"])

with row2[1]:
    st.subheader(T["projects_t"])
    st.write(T["projects_d"])
    st.page_link("pages/8_Projects.py", label=T["projects_l"])

with row2[2]:
    st.subheader(T["ua_t"])
    st.write(T["ua_d"])
    st.page_link("pages/7_Unified_Agent.py", label=T["ua_l"])

st.divider()
st.subheader(T["video_h"])
import os as _os
c_ru, c_en = st.columns(2)
with c_ru:
    st.caption(T["video_ru"])
    _v = _os.path.join(HERE, "..", "docs", "hub-demo-ru.mp4")
    if _os.path.exists(_v):
        st.video(_v)
    else:
        st.info("docs/hub-demo-ru.mp4 — не найден (собери: `python make_demo_video.py`)")
with c_en:
    st.caption(T["video_en"])
    _v = _os.path.join(HERE, "..", "docs", "hub-demo-en.mp4")
    if _os.path.exists(_v):
        st.video(_v)
    else:
        st.info("docs/hub-demo-en.mp4 — not found (run: `python make_demo_video.py`)")

st.caption(T["stack"])
st.write("")
st.page_link("pages/9_Testing.py", label=T["testing_l"], icon="🧪")
st.page_link("pages/10_Contacts.py", label=T["contact_l"], icon="✉️")
