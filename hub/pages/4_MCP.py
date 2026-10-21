"""MCP servers — Model Context Protocol servers for Postgres/MySQL (RU/EN)."""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HUB)

import streamlit as st
from diagrams import render_mermaid
from i18n import lang_switcher

st.set_page_config(page_title="MCP", page_icon="🔌", layout="wide")

lang = lang_switcher()




T = {
    "ru": {
        "title": "🔌 MCP servers",
        "caption": "Model Context Protocol — даём агентам доступ к базам данных через стандартизированные инструменты.",
        "mcp_h": "PostgreSQL MCP Server",
        "mcp_d": "**MCP (Model Context Protocol)** — стандарт, по которому агент вызывает внешние инструменты "
                 "(Anthropic, 2024). MCP-клиент в чат-агенте подключается к MCP-серверу и получает его инструменты, "
                 "ресурсы и промпты. Реализован сервер к **PostgreSQL** (Streamable HTTP): агент делает SQL-запросы "
                 "напрямую через чат, без SQL в коде воркфлоу. Используется в n8n **Lead Qualification** "
                 "для обогащения и записи в CRM, а также в **Unified Agent** (страница 7).",
        "arch": "Архитектура",
        "tools_n": "Инструментов",
        "transport": "Транспорт",
        "port": "Порт",
        "agent": "AI Agent / n8n",
        "client": "MCP Client",
        "server": "MCP Server (pg)",
        "db": "PostgreSQL",
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
                    "Туториал: `projects/mcp-servers/mcp_tutorial.md`",
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
        "title": "🔌 MCP servers",
        "caption": "Model Context Protocol — giving agents access to databases through standardized tools.",
        "mcp_h": "PostgreSQL MCP Server",
        "mcp_d": "**MCP (Model Context Protocol)** — the standard that lets an agent call external tools "
                 "(Anthropic, 2024). An MCP client inside a chat agent connects to an MCP server and gets its "
                 "tools, resources and prompts. A **PostgreSQL** server is implemented over Streamable HTTP: "
                 "the agent runs SQL directly through chat, without SQL hardcoded in the workflow. "
                 "Used by the n8n **Lead Qualification** workflow for enrichment and CRM writes, "
                 "and by the **Unified Agent** (page 7).",
        "arch": "Architecture",
        "tools_n": "Tools",
        "transport": "Transport",
        "port": "Port",
        "agent": "AI Agent / n8n",
        "client": "MCP Client",
        "server": "MCP Server (pg)",
        "db": "PostgreSQL",
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
                    "Tutorial: `projects/mcp-servers/mcp_tutorial.md`",
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
    height=200,
    font_size=13
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
