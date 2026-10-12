"""Projects — portfolio cards (RU/EN), links to source folders in this repo."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HUB)

import streamlit as st
from i18n import lang_switcher

st.set_page_config(page_title="Projects", page_icon="🧩", layout="wide")

lang = lang_switcher()
REPO = "https://github.com/Aliyrd-01/AI"

T = {
    "ru": {
        "title": "🧩 Projects",
        "caption": "Наработки, включённые в репозиторий рядом с хабом (папка `projects/`).",
        "repo": "Репозиторий",
        "code": "Код на GitHub →",
    },
    "en": {
        "title": "🧩 Projects",
        "caption": "Work included in the repository alongside the hub (`projects/` folder).",
        "repo": "Repository",
        "code": "Code on GitHub →",
    },
}[lang]

PROJECTS = [
    {
        "title": "Production RAG (это демо / this demo)",
        "badge": "🔎 RAG",
        "tech": "Python · Streamlit · Qdrant · FastEmbed · LangChain",
        "url": f"{REPO}/tree/main/hub/rag",
        "desc": {
            "ru": "Гибридный retrieval (dense+sparse RRF), CrossEncoder-реранкинг, HyDE, "
                  "multi-query, цитаты, честный отказ, LLM-пул. Метрики: Hit@5 0.86 / NDCG@10 0.73 "
                  "для hybrid+CrossEncoder. Eval и CI включены.",
            "en": "Hybrid retrieval (dense+sparse RRF), CrossEncoder reranking, HyDE, multi-query, "
                  "citations, honest refusal, LLM pool. Metrics: Hit@5 0.86 / NDCG@10 0.73 for "
                  "hybrid+CrossEncoder. Eval and CI included.",
        },
    },
    {
        "title": "n8n automations (3 воркфлоу / 3 workflows)",
        "badge": "🔗 Automation",
        "tech": "n8n · PostgreSQL · MCP · LLM",
        "url": f"{REPO}/tree/main/hub/assets/n8n",
        "desc": {
            "ru": "Content Publisher (RSS→LLM→Telegram), Lead Qualification (MCP + A/B промптов "
                  "+ Postgres CRM), AI Support & Escalation. Разобраны на странице n8n.",
            "en": "Content Publisher (RSS→LLM→Telegram), Lead Qualification (MCP + A/B prompt "
                  "testing + Postgres CRM), AI Support & Escalation. Broken down on the n8n page.",
        },
    },
    {
        "title": "AutoAgent (multi-agent)",
        "badge": "🤖 Agent",
        "tech": "Python · LLM agents · Qubax",
        "url": f"{REPO}/tree/main/projects/autoagent",
        "desc": {
            "ru": "Форк HKUDS AutoAgent: Triage → File/Web/Coding, multi-model по фазам "
                  "(triage/planner/coder/reporter), CLI. Переведён на Qubax.",
            "en": "HKUDS AutoAgent fork: Triage → File/Web/Coding, multi-model per phase "
                  "(triage/planner/coder/reporter), CLI. Switched to Qubax.",
        },
    },
    {
        "title": "MCP servers (PostgreSQL)",
        "badge": "🔌 MCP",
        "tech": "MCP · Node.js · PostgreSQL",
        "url": f"{REPO}/tree/main/projects/mcp-servers",
        "desc": {
            "ru": "MCP-сервер с 10 инструментами SQL (list_tables, select, run_sql, …), "
                  "ресурсы и промпты; используется в Lead Qualification для CRM.",
            "en": "MCP server with 10 SQL tools (list_tables, select, run_sql, …), resources and "
                  "prompts; used by Lead Qualification for the CRM.",
        },
    },
    {
        "title": "LLM Benchmark Suite",
        "badge": "📊 Eval",
        "tech": "Python · LLM eval",
        "url": f"{REPO}/tree/main/projects/hallucination-benchmark",
        "desc": {
            "ru": "TruthfulQA (галлюцинации), GSM8K (математика), BBH (логика) — сравнение "
                  "моделей. Результаты — на вкладке Benchmarks.",
            "en": "TruthfulQA (hallucinations), GSM8K (math), BBH (logic) — model comparison. "
                  "Results are on the Benchmarks tab.",
        },
    },
    {
        "title": "GraphRAG / LightRAG",
        "badge": "🕸️ GraphRAG",
        "tech": "Python · LightRAG · Graph DB",
        "url": f"{REPO}/tree/main/projects/graphrag-lightrag",
        "desc": {
            "ru": "Граф-ориентированный retrieval на LightRAG: ингест документов и ответы "
                  "по базе знаний.",
            "en": "Graph-oriented retrieval on LightRAG: document ingestion and "
                  "knowledge-base answering.",
        },
    },
    {
        "title": "Telegram LightRAG bot",
        "badge": "💬 Bot",
        "tech": "Python · Telegram · LightRAG",
        "url": f"{REPO}/tree/main/projects/telegram-bot",
        "desc": {
            "ru": "Telegram-бот с LightRAG-памятью: отвечает по базе знаний, ведёт диалог.",
            "en": "Telegram bot with LightRAG memory: answers from a knowledge base and "
                  "keeps the dialogue going.",
        },
    },
]

st.title(T["title"])
st.caption(T["caption"])

cols = st.columns(2)
for i, p in enumerate(PROJECTS):
    with cols[i % 2]:
        with st.container(border=True):
            st.markdown(f"**{p['badge']}  {p['title']}**")
            st.write(p["desc"][lang])
            st.caption(p["tech"])
            st.link_button(T["code"], p["url"])

st.divider()
gh = {"ru": f"**Репозиторий:** [{REPO}]({REPO})  \n**GitHub:** [Aliyrd-01](https://github.com/Aliyrd-01)",
      "en": f"**Repository:** [{REPO}]({REPO})  \n**GitHub:** [Aliyrd-01](https://github.com/Aliyrd-01)"}
st.markdown(gh[lang])
