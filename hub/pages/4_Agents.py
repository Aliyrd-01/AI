"""Agents & MCP — multi-agent framework and MCP servers (RU/EN)."""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HUB)

import streamlit as st
from diagrams import render_mermaid
from i18n import lang_switcher

st.set_page_config(page_title="Agents & MCP", page_icon="🤖", layout="wide")

lang = lang_switcher()




T = {
    "ru": {
        "title": "🤖 Agents & MCP",
        "caption": "Многоагентная система и Model Context Protocol — даём LLM доступ к инструментам и данным.",
        "auto_tab": "AutoAgent (multi-agent)",
        "mcp_tab": "MCP servers",
        "auto_h": "AutoAgent — маршрутизация задач по под-агентам",
        "auto_d": "Головной диспетчер **System Triage Agent** принимает задачу на естественном языке "
                  "и делегирует её выполнение специализированным субагентам: **File Surfer** (анализ структуры "
                  "и чтение локальных файлов), **Web Surfer** (поиск в интернете), **Coding** (написание и рефакторинг кода). "
                  "Архитектура поддерживает вызовы функций (function calling) и параллельное выполнение подзадач.",
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
            {"Инструмент (Tool)": "list_tables", "Описание": "Получение списка всех таблиц в базе данных", "Параметры": "—"},
            {"Инструмент (Tool)": "describe_table", "Описание": "Схема и типы колонок целевой таблицы", "Параметры": "table"},
            {"Инструмент (Tool)": "select", "Описание": "Выполнение безопасного чтения данных (SELECT)", "Параметры": "sql"},
            {"Инструмент (Tool)": "insert", "Описание": "Создание новых записей в таблице", "Параметры": "table, data"},
            {"Инструмент (Tool)": "update", "Описание": "Модификация существующих записей", "Параметры": "table, set, where"},
            {"Инструмент (Tool)": "delete_rows", "Описание": "Удаление строк по условию", "Параметры": "table, where"},
            {"Инструмент (Tool)": "create_table", "Описание": "Создание новой реляционной таблицы", "Параметры": "sql"},
            {"Инструмент (Tool)": "add_column", "Описание": "Миграция схемы: добавление новой колонки", "Параметры": "table, column_def"},
            {"Инструмент (Tool)": "create_index", "Описание": "Создание индексов для ускорения выборок", "Параметры": "table, columns"},
            {"Инструмент (Tool)": "run_sql", "Описание": "Комплексные SQL-транзакции", "Параметры": "sql"},
        ],
    },
    "en": {
        "title": "🤖 Agents & MCP",
        "caption": "Multi-agent system and Model Context Protocol — giving LLMs access to tools and data.",
        "auto_tab": "AutoAgent (multi-agent)",
        "mcp_tab": "MCP servers",
        "auto_h": "AutoAgent — Autonomous Task Orchestration",
        "auto_d": "The **System Triage Agent** orchestrates multi-agent workflows by delegating "
                  "complex natural language instructions to specialized sub-agents: **File Surfer** (file tree and source parsing), "
                  "**Web Surfer** (real-time web search), and **Coding** (code generation and refactoring). "
                  "The architecture supports native function calling and parallel task execution.",
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
            {"Tool": "list_tables", "Description": "List all tables in the database", "Parameters": "—"},
            {"Tool": "describe_table", "Description": "Show schema and column types of a table", "Parameters": "table"},
            {"Tool": "select", "Description": "Execute safe read-only SQL SELECT queries", "Parameters": "sql"},
            {"Tool": "insert", "Description": "Insert new rows into a table", "Parameters": "table, data"},
            {"Tool": "update", "Description": "Update existing rows by condition", "Parameters": "table, set, where"},
            {"Tool": "delete_rows", "Description": "Delete rows by condition", "Parameters": "table, where"},
            {"Tool": "create_table", "Description": "Create a new database table", "Parameters": "sql"},
            {"Tool": "add_column", "Description": "Schema migration: add a new column", "Parameters": "table, column_def"},
            {"Tool": "create_index", "Description": "Create database index for fast lookups", "Parameters": "table, columns"},
            {"Tool": "run_sql", "Description": "Execute complex SQL transactions", "Parameters": "sql"},
        ],
    },
}[lang]

st.title(T["title"])
st.caption(T["caption"])

tab_agent, tab_mcp = st.tabs([T["auto_tab"], T["mcp_tab"]])

with tab_agent:
    st.subheader(T["auto_h"])
    st.write(T["auto_d"])
    c1, c2, c3 = st.columns(3)
    c1.metric(T["agents_n"], "1 + 3")
    c2.metric(T["modes"], "user / editor / workflow")
    c3.metric(T["provider"], "Qubax")
    st.markdown(f"**{T['arch']}**")
    render_mermaid(
        "flowchart TD\n"
        f'  U["{T["task"]}"] --> T["{T["triage"]}"]\n'
        f'  T --> F["{T["file"]}"]\n'
        f'  T --> W["{T["web"]}"]\n'
        f'  T --> C["{T["coding"]}"]\n'
        f'  F --> R["{T["result"]}"]\n'
        f'  W --> R\n'
        f'  C --> R',
        height=320
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
    st.markdown(f"**{T['arch']}**")
    render_mermaid(
        "flowchart LR\n"
        f'  A["{T["agent"]}"] --> C["{T["client"]}"]\n'
        f'  C --> S["{T["server"]}"]\n'
        f'  S --> D[("{T["db"]}")]',
        height=220
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
