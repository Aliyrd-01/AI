"""Other projects — portfolio cards with links to code."""

import streamlit as st

st.set_page_config(page_title="Projects", page_icon="🧩", layout="wide")

# Заполните url реальными ссылками на репозитории/демо.
GITHUB = "https://github.com/Aliyrd-01"

PROJECTS = [
    {
        "title": "Production RAG (это демо)",
        "desc": "Гибридный retrieval (dense+sparse RRF), CrossEncoder-реранкинг, HyDE, "
                "multi-query, цитаты, честный отказ, LLM-пул. Оффлайн-метрики: Hit@5 0.86 / "
                "NDCG@10 0.73 для hybrid+CrossEncoder. Eval и CI включены.",
        "tech": "Python · Streamlit · Qdrant · FastEmbed · LangChain",
        "url": f"{GITHUB}/production-rag-demo",
        "badge": "🔎 RAG",
    },
    {
        "title": "n8n automations (3 воркфлоу)",
        "desc": "Content Publisher (RSS→LLM→Telegram), Lead Qualification (MCP + A/B промптов "
                "+ Postgres CRM), AI Support & Escalation. Разобраны на странице n8n.",
        "tech": "n8n · PostgreSQL · MCP · LLM",
        "url": None,
        "badge": "🔗 Automation",
    },
    {
        "title": "GraphRAG / LightRAG",
        "desc": "Граф-ориентированный retrieval и LightRAG-пайплайн; сравнение с векторным "
                "поиском на многошаговых вопросах.",
        "tech": "Python · LightRAG · Graph DB · LLM",
        "url": None,
        "badge": "🕸️ GraphRAG",
    },
    {
        "title": "AutoAgent",
        "desc": "Автономный агент планирования задач: декомпозиция цели, вызов инструментов, "
                "самопроверка результата.",
        "tech": "Python · LLM agents · Tools",
        "url": None,
        "badge": "🤖 Agent",
    },
    {
        "title": "MCP server (Postgres)",
        "desc": "MCP-сервер с инструментом SQL-запроса к Postgres — используется в Lead "
                "Qualification для обогащения и записи в CRM.",
        "tech": "MCP · Python · PostgreSQL",
        "url": None,
        "badge": "🔌 MCP",
    },
    {
        "title": "Hallucination benchmark",
        "desc": "Бенчмарк галлюцинаций LLM: набор провокационных вопросов и метрики "
                "достоверности ответов.",
        "tech": "Python · LLM eval",
        "url": None,
        "badge": "📊 Eval",
    },
    {
        "title": "LLM-уроки (metrics / costs / LlamaIndex)",
        "desc": "Учебные модули: метрики качества LLM, расчёт стоимости токенов, построение "
                "пайплайнов на LlamaIndex.",
        "tech": "Python · LlamaIndex · LLM ops",
        "url": None,
        "badge": "📚 Learn",
    },
    {
        "title": "Telegram LightRAG bot",
        "desc": "Telegram-бот с LightRAG-памятью: отвечает по базе знаний, ведёт диалог.",
        "tech": "Python · Telegram · LightRAG",
        "url": None,
        "badge": "💬 Bot",
    },
]

st.title("🧩 Projects")
st.caption("Наработки вне основного демо. Ссылки на код — уточняются.")

cols = st.columns(2)
for i, p in enumerate(PROJECTS):
    with cols[i % 2]:
        with st.container(border=True):
            st.markdown(f"**{p['badge']}  {p['title']}**")
            st.write(p["desc"])
            st.caption(p["tech"])
            if p["url"]:
                st.link_button("Код на GitHub →", p["url"])
            else:
                st.caption("_ссылка на репозиторий: добавить_")

st.divider()
st.subheader("Контакты")
st.markdown(
    "**GitHub:** [Aliyrd-01](https://github.com/Aliyrd-01)  \n"
    "Готов обсудить архитектуру, метрики и продакшн-детали любого из проектов."
)
