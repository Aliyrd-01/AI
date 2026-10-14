"""Unified Agent — one agent that routes between RAG and the CRM (MCP). (RU/EN)"""

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HUB, "rag"))
sys.path.insert(0, os.path.join(HUB, "agents"))
sys.path.insert(0, HUB)

import streamlit as st
from diagrams import render_mermaid
from i18n import lang_switcher

st.set_page_config(page_title="Unified Agent", page_icon="🧭", layout="wide")

lang = lang_switcher()


T = {
    "ru": {
        "title": "🧭 Unified Agent",
        "caption": "Один агент с инструментами: сам решает — искать в базе знаний (RAG) "
                   "или запросить CRM (PostgreSQL через MCP).",
        "how": "Как это работает",
        "task": "Вопрос",
        "agent": "Unified Agent (Qubax, tool-calling)",
        "kb_tool": "search_knowledge_base · Qdrant hybrid",
        "db_tool": "query_database · MCP → PostgreSQL",
        "answer": "Ответ с [KB] / [DB]",
        "note": "Агент вызывает нужные инструменты (может несколько), затем отвечает "
                "с пометками [KB] (база знаний) и [DB] (CRM).",
        "q": "Вопрос",
        "run": "Запустить агента",
        "thinking": "Агент выбирает инструменты...",
        "answer": "Ответ",
        "empty": "_(пусто)_",
        "model": "модель",
        "tools_n": "вызовов инструментов",
        "trace": "Трейс инструментов:",
        "failed": "Агент упал:",
        "no_tools": "Инструменты не понадобились — модель ответила сама.",
        "foot": "Инструмент CRM ходит в PostgreSQL MCP-сервер (`POST /mcp`); если он не запущен, "
                "агент честно сообщит и ответит по базе знаний. RAG-инструмент работает всегда (Qdrant Cloud).",
        "task_label": "Задача (natural language)",
        "triage_label": "Unified Agent (Qubax, tool-calling)",
        "kb_label": "search_knowledge_base · Qdrant hybrid",
        "db_label": "query_database · MCP → PostgreSQL",
        "ans_label": "Ответ с [KB] / [DB]",
    },
    "en": {
        "title": "🧭 Unified Agent",
        "caption": "One tool-calling agent: it decides whether to search the knowledge base (RAG) "
                   "or query the CRM (PostgreSQL via MCP).",
        "how": "How it works",
        "task": "Question",
        "agent": "Unified Agent (Qubax, tool-calling)",
        "kb_tool": "search_knowledge_base · Qdrant hybrid",
        "db_tool": "query_database · MCP → PostgreSQL",
        "answer": "Answer with [KB] / [DB]",
        "note": "The agent calls the tools it needs (possibly several), then answers with "
                "[KB] (knowledge base) and [DB] (CRM) tags.",
        "q": "Question",
        "run": "Run agent",
        "thinking": "The agent is choosing tools...",
        "answer": "Answer",
        "empty": "_(empty)_",
        "model": "model",
        "tools_n": "tool calls",
        "trace": "Tool trace:",
        "failed": "Agent failed:",
        "no_tools": "No tools were needed — the model answered directly.",
        "foot": "The CRM tool talks to the PostgreSQL MCP server (`POST /mcp`); if it is not running, "
                "the agent says so honestly and answers from the knowledge base. The RAG tool always "
                "works (Qdrant Cloud).",
        "task_label": "Question",
        "triage_label": "Unified Agent (Qubax, tool-calling)",
        "kb_label": "search_knowledge_base · Qdrant hybrid",
        "db_label": "query_database · MCP → PostgreSQL",
        "ans_label": "Answer with [KB] / [DB]",
    },
}[lang]

st.title(T["title"])
st.caption(T["caption"])

st.markdown(f"**{T['how']}**")
render_mermaid(
    "flowchart TD\n"
    f'  U["{T["task_label"]}"] --> A["{T["triage_label"]}"]\n'
    f'  A -->|tool| R["{T["kb_label"]}"]\n'
    f'  A -->|tool| D["{T["db_label"]}"]\n'
    f'  R --> A\n'
    f'  D --> A\n'
    f'  A --> Ans["{T["ans_label"]}"]',
    height=320
)
st.caption(T["note"])

EXAMPLES = {
    "ru": [
        "What color is amber urine?",
        "How many leads are in the CRM and what's the hottest one?",
    ],
    "en": [
        "What color is amber urine?",
        "How many leads are in the CRM and what's the hottest one?",
    ],
}[lang]

st.markdown("**Try:**  " + " · ".join(f"`{e}`" for e in EXAMPLES[:2]))
question = st.text_input(T["q"], key="ua_q", placeholder="Ask anything (KB or CRM)")

if st.button(T["run"], type="primary", disabled=not question.strip()):
    q = question.strip()
    with st.spinner(T["thinking"]):
        try:
            import unified_agent as ua
            t0 = time.time()
            res = ua.run(q)
            dt = time.time() - t0
            err = None
        except Exception as e:  # noqa: BLE001
            res, dt, err = None, 0, f"{type(e).__name__}: {e}"

    if err:
        st.error(f"{T['failed']} {err}")
    else:
        st.markdown(f"### {T['answer']}")
        st.markdown(res["answer"] or T["empty"])
        st.caption(f"{T['model']} `{res['model']}` · {dt:.1f}s · "
                   f"{T['tools_n']}: {len(res['steps'])}")

        if res["steps"]:
            st.markdown(f"**{T['trace']}**")
            for i, s in enumerate(res["steps"], 1):
                args = json.dumps(s["args"], ensure_ascii=False)
                with st.expander(f"🔧 {i}. {s['tool']}  ·  {args[:90]}"):
                    st.code(s["result"], language=None)
        else:
            st.info(T["no_tools"])

st.divider()
st.caption(T["foot"])
