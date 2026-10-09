"""Portfolio hub — landing page.

Streamlit multi-page entrypoint. Sidebar navigation is generated from ./pages/.
Run locally:  streamlit run hub/Home.py
"""

import streamlit as st

st.set_page_config(page_title="AI Portfolio", page_icon="🧠", layout="wide")

st.title("🧠 AI Portfolio")
st.caption("RAG-система, n8n-автоматизации и агенты: интерактивное демо + разборы пайплайнов.")

st.markdown(
    "Один проект, который собирает ключевые наработки. Всё запускается локально "
    "одной командой и позже разворачивается на VPS."
)
st.write("")

row1 = st.columns(3, gap="large")
with row1[0]:
    st.subheader("🔎 RAG")
    st.write("Гибридный retrieval (dense+sparse RRF), CrossEncoder-реранкинг, цитаты, "
             "честный отказ, 11 стратегий, замеренные метрики.")
    st.page_link("pages/1_RAG.py", label="Открыть демо →")

with row1[1]:
    st.subheader("🔗 n8n")
    st.write("3 воркфлоу: Content Publisher (RSS→LLM→Telegram), Lead Qualification "
             "(MCP + A/B промптов + CRM), AI Support & Escalation.")
    st.page_link("pages/2_n8n.py", label="Пайплайны →")

with row1[2]:
    st.subheader("🤖 Agents & MCP")
    st.write("Многоагентная система AutoAgent (triage → File/Web/Coding) и MCP-серверы "
             "к Postgres/MySQL.")
    st.page_link("pages/4_Agents.py", label="Агенты →")

st.write("")
row2 = st.columns(3, gap="large")
with row2[0]:
    st.subheader("📊 Benchmarks")
    st.write("Метрики retrieval/генерации (Hit@5, NDCG@10, faithfulness) и сравнение LLM "
             "по TruthfulQA / GSM8K / BBH.")
    st.page_link("pages/5_Benchmarks.py", label="Метрики →")

with row2[1]:
    st.subheader("🧩 Проекты")
    st.write("GraphRAG/LightRAG, Telegram-LightRAG-бот, учебные модули — карточки и ссылки.")
    st.page_link("pages/3_Projects.py", label="Все проекты →")

with row2[2]:
    st.subheader("ℹ️ Стек")
    st.write("Python · Streamlit · Qdrant · FastEmbed · LangChain · n8n · PostgreSQL · "
             "MCP · Docker")
