"""Agents & MCP — multi-agent framework and Model Context Protocol servers."""

import html
import json

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
        "**Провайдер — Qubax** (отвязано от OpenCode Zen), base `https://api.qubax.ai/v1`, "
        "tool-calls включены (`FN_CALL=True`)."
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

    st.markdown("**Модели по фазам (multi-model)** — `ROLE_MODELS` в `.env`:")
    st.dataframe(
        [
            {"Роль": "triage", "Модель (Qubax)": "qwen3-32b", "Фаза": "маршрутизация задачи"},
            {"Роль": "planner", "Модель (Qubax)": "qwen3-235b-a22b-2507", "Фаза": "планирование, анализ багов"},
            {"Роль": "coder", "Модель (Qubax)": "glm-5.2", "Фаза": "реализация, фиксы, ревью, тесты"},
            {"Роль": "reporter", "Модель (Qubax)": "glm-4.7-flash", "Фаза": "отчёты, документация"},
        ],
        use_container_width=True, hide_index=True,
    )
    st.caption("Роль определяется по системному промпту (`_infer_role`); проверено — все 4 роли отвечают. "
               "Исходник: `D:\\AI\\AutoAgent`, CLI: `auto main` (или `auto_zen.py`).")

with tab_mcp:
    st.subheader("PostgreSQL MCP Server")
    st.write(
        "**MCP (Model Context Protocol)** — стандарт, по которому агент вызывает внешние инструменты. "
        "Реализован сервер к PostgreSQL (Streamable HTTP): агент делает SQL-запросы через чат. "
        "Используется в n8n **Lead Qualification** для обогащения и записи в CRM."
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Tools", "10")
    c2.metric("Транспорт", "Streamable HTTP")
    c3.metric("Порт", "9002")
    with st.expander("Схема", expanded=True):
        render_mermaid(
            "flowchart LR\n"
            '  A["AI Agent / n8n"] --> C["MCP Client"]\n'
            '  C --> S["MCP Server (pg)"]\n'
            '  S --> D[("PostgreSQL")]'
        )

    st.markdown("**Tools (инструменты агента):**")
    st.dataframe(
        [
            {"Tool": "list_tables", "Описание": "Список таблиц", "Параметры": "—"},
            {"Tool": "describe_table", "Описание": "Колонки таблицы", "Параметры": "table"},
            {"Tool": "select", "Описание": "SELECT-запрос", "Параметры": "sql"},
            {"Tool": "insert", "Описание": "Вставить строку", "Параметры": "table, data"},
            {"Tool": "update", "Описание": "Обновить строки", "Параметры": "table, set, where"},
            {"Tool": "delete_rows", "Описание": "Удалить строки", "Параметры": "table, where"},
            {"Tool": "create_table", "Описание": "Создать таблицу", "Параметры": "sql"},
            {"Tool": "add_column", "Описание": "Добавить колонку", "Параметры": "table, column_def"},
            {"Tool": "create_index", "Описание": "Создать индекс", "Параметры": "table, columns"},
            {"Tool": "run_sql", "Описание": "Любой SQL", "Параметры": "sql"},
        ],
        use_container_width=True, hide_index=True,
    )
    st.caption("Ресурсы: `postgres://tables`, `postgres://table/{name}` · "
               "Промпты: `explain_table`, `query_data`. Есть аналогичный сервер для MySQL.")

    st.markdown("**Мини-демо (JSON-RPC вызов инструмента `select`):**")
    st.markdown("Запрос:")
    st.code(json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "select", "arguments": {"sql": "SELECT COUNT(*) FROM leads_leads"}}
    }, ensure_ascii=False, indent=2), language="json")
    st.markdown("Ответ (сокращённо):")
    st.code(json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "result": {"content": [{"type": "text", "text": "[{\"count\": \"142\"}]"}]}
    }, ensure_ascii=False, indent=2), language="json")
    st.caption("Эндпоинт: `POST http://localhost:9002/mcp` · Auth: `Authorization: Bearer <token>` · "
               "Туториал: `D:\\AI\\MCP\\mcp_tutorial.md`")
