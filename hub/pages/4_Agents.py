"""Agents & MCP — multi-agent framework and MCP servers (RU/EN)."""

import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HUB)

import streamlit as st
import streamlit.components.v1 as components
from i18n import lang_switcher

st.set_page_config(page_title="Agents & MCP", page_icon="🤖", layout="wide")

lang = lang_switcher()


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


T = {
    "ru": {
        "title": "🤖 Agents & MCP",
        "caption": "Многоагентная система и Model Context Protocol — даём LLM доступ к инструментам и данным.",
        "auto_tab": "AutoAgent (multi-agent)",
        "mcp_tab": "MCP servers",
        "auto_h": "AutoAgent — маршрутизация задач по под-агентам",
        "auto_d": "Форк фреймворка **AutoAgent (HKUDS)**: головной `System Triage Agent` принимает задачу "
                  "на естественном языке и передаёт её профильному под-агенту — **File Surfer** (чтение/анализ "
                  "файлов), **Web Surfer** (поиск в вебе), **Coding** (написание/правка кода). Результаты "
                  "собираются и возвращаются пользователю.",
        "qubax": "**Провайдер — Qubax** (отвязано от OpenCode Zen), base `https://api.qubax.ai/v1`, "
                 "tool-calls включены (`FN_CALL=True`).",
        "arch": "Архитектура",
        "phase_models": "Модели по фазам (multi-model) — `ROLE_MODELS` в `.env`:",
        "role": "Роль",
        "model": "Модель (Qubax)",
        "phase": "Фаза",
        "src": "Исходник",
        "mcp_h": "PostgreSQL MCP Server",
        "mcp_d": "**MCP (Model Context Protocol)** — стандарт, по которому агент вызывает внешние инструменты. "
                 "Реализован сервер к PostgreSQL (Streamable HTTP): агент делает SQL-запросы через чат. "
                 "Используется в n8n **Lead Qualification** для обогащения и записи в CRM.",
        "tools_h": "**Tools (инструменты агента):**",
        "tool": "Tool",
        "desc_col": "Описание",
        "params": "Параметры",
        "res_prompts": "Ресурсы: `postgres://tables`, `postgres://table/{name}` · "
                       "Промпты: `explain_table`, `query_data`. Есть аналогичный сервер для MySQL.",
        "demo_h": "Мини-демо (JSON-RPC вызов инструмента `select`):",
        "req": "Запрос:",
        "resp": "Ответ (сокращённо):",
        "endpoint": "Эндпоинт: `POST http://localhost:9002/mcp` · Auth: `Authorization: Bearer <token>` · "
                    "Туториал: `D:\\AI\\MCP\\mcp_tutorial.md`",
        "task": "Задача (natural language)",
        "triage": "System Triage Agent",
        "file": "File Surfer",
        "web": "Web Surfer",
        "coding": "Coding Agent",
        "result": "Aggregated result",
        "agents_n": "Агентов",
        "modes": "Режимы",
        "provider": "Провайдер",
        "tools_n": "Tools",
        "transport": "Транспорт",
        "port": "Порт",
        "agent": "AI Agent / n8n",
        "client": "MCP Client",
        "server": "MCP Server (pg)",
        "db": "PostgreSQL",
        "phase_rows": [
            {"role": "triage", "model": "qwen3-32b", "phase": "маршрутизация задачи"},
            {"role": "planner", "model": "qwen3-235b-a22b-2507", "phase": "планирование, анализ багов"},
            {"role": "coder", "model": "glm-5.2", "phase": "реализация, фиксы, ревью, тесты"},
            {"role": "reporter", "model": "glm-4.7-flash", "phase": "отчёты, документация"},
        ],
        "tool_rows": [
            {"Tool": "list_tables", "d": "Список таблиц", "p": "—"},
            {"Tool": "describe_table", "d": "Колонки таблицы", "p": "table"},
            {"Tool": "select", "d": "SELECT-запрос", "p": "sql"},
            {"Tool": "insert", "d": "Вставить строку", "p": "table, data"},
            {"Tool": "update", "d": "Обновить строки", "p": "table, set, where"},
            {"Tool": "delete_rows", "d": "Удалить строки", "p": "table, where"},
            {"Tool": "create_table", "d": "Создать таблицу", "p": "sql"},
            {"Tool": "add_column", "d": "Добавить колонку", "p": "table, column_def"},
            {"Tool": "create_index", "d": "Создать индекс", "p": "table, columns"},
            {"Tool": "run_sql", "d": "Любой SQL", "p": "sql"},
        ],
    },
    "en": {
        "title": "🤖 Agents & MCP",
        "caption": "Multi-agent system and Model Context Protocol — giving LLMs access to tools and data.",
        "auto_tab": "AutoAgent (multi-agent)",
        "mcp_tab": "MCP servers",
        "auto_h": "AutoAgent — routing tasks to sub-agents",
        "auto_d": "A fork of the **AutoAgent (HKUDS)** framework: the `System Triage Agent` takes a "
                  "natural-language task and hands it to the right sub-agent — **File Surfer** (reading/analysing "
                  "files), **Web Surfer** (web search), **Coding** (writing/editing code). Results are "
                  "aggregated and returned to the user.",
        "qubax": "**Provider — Qubax** (detached from OpenCode Zen), base `https://api.qubax.ai/v1`, "
                 "tool-calls enabled (`FN_CALL=True`).",
        "arch": "Architecture",
        "phase_models": "Per-phase models (multi-model) — `ROLE_MODELS` in `.env`:",
        "role": "Role",
        "model": "Model (Qubax)",
        "phase": "Phase",
        "src": "Source",
        "mcp_h": "PostgreSQL MCP Server",
        "mcp_d": "**MCP (Model Context Protocol)** — the standard that lets an agent call external tools. "
                 "A PostgreSQL server is implemented over Streamable HTTP: the agent runs SQL through chat. "
                 "Used by the n8n **Lead Qualification** workflow for enrichment and CRM writes.",
        "tools_h": "**Tools (agent tools):**",
        "tool": "Tool",
        "desc_col": "Description",
        "params": "Params",
        "res_prompts": "Resources: `postgres://tables`, `postgres://table/{name}` · "
                       "Prompts: `explain_table`, `query_data`. A MySQL counterpart exists too.",
        "demo_h": "Mini-demo (JSON-RPC call of the `select` tool):",
        "req": "Request:",
        "resp": "Response (abridged):",
        "endpoint": "Endpoint: `POST http://localhost:9002/mcp` · Auth: `Authorization: Bearer <token>` · "
                    "Tutorial: `D:\\AI\\MCP\\mcp_tutorial.md`",
        "task": "Task (natural language)",
        "triage": "System Triage Agent",
        "file": "File Surfer",
        "web": "Web Surfer",
        "coding": "Coding Agent",
        "result": "Aggregated result",
        "agents_n": "Agents",
        "modes": "Modes",
        "provider": "Provider",
        "tools_n": "Tools",
        "transport": "Transport",
        "port": "Port",
        "agent": "AI Agent / n8n",
        "client": "MCP Client",
        "server": "MCP Server (pg)",
        "db": "PostgreSQL",
        "phase_rows": [
            {"role": "triage", "model": "qwen3-32b", "phase": "task routing"},
            {"role": "planner", "model": "qwen3-235b-a22b-2507", "phase": "planning, bug analysis"},
            {"role": "coder", "model": "glm-5.2", "phase": "implementation, fixes, review, testing"},
            {"role": "reporter", "model": "glm-4.7-flash", "phase": "reports, documentation"},
        ],
        "tool_rows": [
            {"Tool": "list_tables", "d": "List all tables", "p": "—"},
            {"Tool": "describe_table", "d": "Show columns of a table", "p": "table"},
            {"Tool": "select", "d": "Run a SELECT query", "p": "sql"},
            {"Tool": "insert", "d": "Insert rows", "p": "table, data"},
            {"Tool": "update", "d": "Update rows", "p": "table, set, where"},
            {"Tool": "delete_rows", "d": "Delete rows", "p": "table, where"},
            {"Tool": "create_table", "d": "Create a table", "p": "sql"},
            {"Tool": "add_column", "d": "Add a column", "p": "table, column_def"},
            {"Tool": "create_index", "d": "Create an index", "p": "table, columns"},
            {"Tool": "run_sql", "d": "Run any SQL", "p": "sql"},
        ],
    },
}[lang]

st.title(T["title"])
st.caption(T["caption"])

tab_agent, tab_mcp = st.tabs([T["auto_tab"], T["mcp_tab"]])

with tab_agent:
    st.subheader(T["auto_h"])
    st.write(T["auto_d"])
    st.info(T["qubax"])
    c1, c2, c3 = st.columns(3)
    c1.metric(T["agents_n"], "1 + 3")
    c2.metric(T["modes"], "user / editor / workflow")
    c3.metric(T["provider"], "Qubax")
    with st.expander(T["arch"], expanded=True):
        render_mermaid(
            "flowchart TD\n"
            f'  U["{T["task"]}"] --> T["{T["triage"]}"]\n'
            f'  T --> F["{T["file"]}"]\n'
            f'  T --> W["{T["web"]}"]\n'
            f'  T --> C["{T["coding"]}"]\n'
            f'  F --> R["{T["result"]}"]\n'
            f'  W --> R\n'
            f'  C --> R'
        )

    st.markdown(f"**{T['phase_models']}**")
    st.dataframe(T["phase_rows"], use_container_width=True, hide_index=True)
    st.caption(f"{T['src']}: `D:\\AI\\AutoAgent` → `projects/autoagent` · CLI: `auto main` (`auto_zen.py`)")

with tab_mcp:
    st.subheader(T["mcp_h"])
    st.write(T["mcp_d"])
    c1, c2, c3 = st.columns(3)
    c1.metric(T["tools_n"], "10")
    c2.metric(T["transport"], "Streamable HTTP")
    c3.metric(T["port"], "9002")
    with st.expander(T["arch"], expanded=True):
        render_mermaid(
            "flowchart LR\n"
            f'  A["{T["agent"]}"] --> C["{T["client"]}"]\n'
            f'  C --> S["{T["server"]}"]\n'
            f'  S --> D[("{T["db"]}")]'
        )

    st.markdown(T["tools_h"])
    st.dataframe(T["tool_rows"], use_container_width=True, hide_index=True)
    st.caption(T["res_prompts"])

    st.markdown(f"**{T['demo_h']}**")
    st.markdown(T["req"])
    st.code(json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "select", "arguments": {"sql": "SELECT COUNT(*) FROM leads_leads"}}
    }, ensure_ascii=False, indent=2), language="json")
    st.markdown(T["resp"])
    st.code(json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "result": {"content": [{"type": "text", "text": "[{\"count\": \"142\"}]"}]}
    }, ensure_ascii=False, indent=2), language="json")
    st.caption(T["endpoint"])
