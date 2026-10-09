"""Other projects — portfolio cards with links to the source in this repo."""

import streamlit as st

st.set_page_config(page_title="Projects", page_icon="🧩", layout="wide")

REPO = "https://github.com/Aliyrd-01/AI"

PROJECTS = [
    {
        "title": "Production RAG (это демо)",
        "desc": "Гибридный retrieval (dense+sparse RRF), CrossEncoder-реранкинг, HyDE, "
                "multi-query, цитаты, честный отказ, LLM-пул. Оффлайн-метрики: Hit@5 0.86 / "
                "NDCG@10 0.73 для hybrid+CrossEncoder. Eval и CI включены.",
        "tech": "Python · Streamlit · Qdrant · FastEmbed · LangChain",
        "url": f"{REPO}/tree/main/hub/rag",
        "badge": "🔎 RAG",
    },
    {
        "title": "n8n automations (3 воркфлоу)",
        "desc": "Content Publisher (RSS→LLM→Telegram), Lead Qualification (MCP + A/B промптов "
                "+ Postgres CRM), AI Support & Escalation. Разобраны на странице n8n.",
        "tech": "n8n · PostgreSQL · MCP · LLM",
        "url": f"{REPO}/tree/main/hub/assets/n8n",
        "badge": "🔗 Automation",
    },
    {
        "title": "AutoAgent (multi-agent)",
        "desc": "Форк HKUDS AutoAgent: Triage → File/Web/Coding, multi-model по фазам "
                "(triage/planner/coder/reporter), CLI. Переведён на Qubax.",
        "tech": "Python · LLM agents · Qubax",
        "url": f"{REPO}/tree/main/projects/autoagent",
        "badge": "🤖 Agent",
    },
    {
        "title": "MCP servers (PostgreSQL)",
        "desc": "MCP-сервер с 10 инструментами SQL (list_tables, select, run_sql, …), "
                "ресурсы и промпты; используется в Lead Qualification для CRM.",
        "tech": "MCP · Node.js · PostgreSQL",
        "url": f"{REPO}/tree/main/projects/mcp-servers",
        "badge": "🔌 MCP",
    },
    {
        "title": "LLM Benchmark Suite",
        "desc": "TruthfulQA (галлюцинации), GSM8K (математика), BBH (логика) — сравнение "
                "моделей. Результаты — на вкладке Benchmarks.",
        "tech": "Python · LLM eval",
        "url": f"{REPO}/tree/main/projects/hallucination-benchmark",
        "badge": "📊 Eval",
    },
    {
        "title": "GraphRAG / LightRAG",
        "desc": "Граф-ориентированный retrieval на LightRAG: ингест документов и ответы "
                "по базе знаний.",
        "tech": "Python · LightRAG · Graph DB",
        "url": f"{REPO}/tree/main/projects/graphrag-lightrag",
        "badge": "🕸️ GraphRAG",
    },
    {
        "title": "Telegram LightRAG bot",
        "desc": "Telegram-бот с LightRAG-памятью: отвечает по базе знаний, ведёт диалог.",
        "tech": "Python · Telegram · LightRAG",
        "url": f"{REPO}/tree/main/projects/telegram-bot",
        "badge": "💬 Bot",
    },
]

st.title("🧩 Projects")
st.caption("Наработки, включённые в репозиторий рядом с хабом (папка `projects/`).")

cols = st.columns(2)
for i, p in enumerate(PROJECTS):
    with cols[i % 2]:
        with st.container(border=True):
            st.markdown(f"**{p['badge']}  {p['title']}**")
            st.write(p["desc"])
            st.caption(p["tech"])
            st.link_button("Код на GitHub →", p["url"])

st.divider()
st.markdown(
    f"**Репозиторий:** [{REPO}]({REPO})  \n"
    "**GitHub:** [Aliyrd-01](https://github.com/Aliyrd-01)"
)
