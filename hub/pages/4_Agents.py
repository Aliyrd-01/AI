"""Agents & MCP — multi-agent framework and Model Context Protocol servers."""

import html
import os

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Agents & MCP", page_icon="🤖", layout="wide")


def render_mermaid(code: str, height: int = 420):
    components.html(
        f"""
        <div class="mermaid">{html.escape(code)}</div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{ startOnLoad: true, theme: "base" }});</script>
        """,
        height=height,
        scrolling=True,
    )


st.title("🤖 Agents & MCP")
st.caption("Многоагентная система и Model Context Protocol — даём LLM доступ к инструментам и данным.")

tab_agent, tab_mcp = st.tabs(["AutoAgent (multi-agent)", "MCP servers"])

with tab_agent:
    st.subheader("AutoAgent — маршрутизация задач по под-агентам")
    st.write(
        "Форк фреймворка **AutoAgent (HKUDS)**: головной `System Triage Agent` принимает задачу "
        "на естественном языке и передаёт её профильному под-агенту — **File Surfer** (чтение/анализ "
        "файлов), **Web Surfer** (поиск в вебе), **Coding** (написание/правка кода). Результаты "
        "собираются и возвращаются пользователю."
    )
    st.info(
        "**Отвязано от OpenCode Zen.** Раньше работало на `big-pickle` + `FN_CALL=False` "
        "(без tool-calls). Переводим на **Qubax** с моделью, поддерживающей function calling."
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Агентов", "1 + 3")
    c2.metric("Режимы", "user / editor / workflow")
    c3.metric("Провайдер", "Qubax")
    with st.expander("Архитектура", expanded=True):
        render_mermaid(
            "flowchart TD\n"
            '  U["Task (natural language)"] --> T["System Triage Agent"]\n'
            '  T --> F["File Surfer"]\n'
            '  T --> W["Web Surfer"]\n'
            '  T --> C["Coding Agent"]\n'
            '  F --> R["Aggregated result"]\n'
            '  W --> R\n'
            '  C --> R'
        )
    st.caption("Исходник: `D:\\AI\\AutoAgent` · CLI: `auto main` (или `auto_zen.py`).")

with tab_mcp:
    st.subheader("MCP servers — инструменты для агента")
    st.write(
        "**MCP (Model Context Protocol)** — стандарт, по которому агент вызывает внешние "
        "инструменты. Реализованы серверы к БД: "
        "**PostgreSQL** и **MySQL** (инструмент SQL-запроса). Используются в n8n Lead Qualification "
        "для обогащения и записи в CRM."
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Серверы", "2 (pg, mysql)")
    c2.metric("Транспорт", "SSE / HTTP")
    c3.metric("Инструмент", "SQL query")
    with st.expander("Схема", expanded=True):
        render_mermaid(
            "flowchart LR\n"
            '  A["AI Agent / n8n"] --> C["MCP Client"]\n'
            '  C --> S["MCP Server (pg / mysql)"]\n'
            '  S --> D[("PostgreSQL / MySQL")]'
        )
    st.markdown(
        "- Туториал: `D:\\AI\\MCP\\mcp_tutorial.md`\n"
        "- Запуск: `start-pg-mcp-server.ps1`, `start-mysql-mcp-server.ps1`\n"
        "- Пример: «покажи последние 10 заказов» → агент вызывает `query_database`."
    )
