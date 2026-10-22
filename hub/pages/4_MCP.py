"""MCP — our own PostgreSQL MCP server (Node.js) + deployment paths (RU/EN)."""

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

TOOLS_SNIPPET = """mcpServer.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    { name: "list_tables", description: "List all tables" },
    { name: "describe_table", description: "Show columns of a table" },
    { name: "select", description: "Run a SELECT query",
      inputSchema: { type: "object", properties: { sql: { type: "string" } } } },
    { name: "insert", description: "Insert into a table",
      inputSchema: { type: "object", properties: { table: { type: "string" }, data: { type: "object" } } } },
    { name: "update", description: "Update rows" },
    { name: "delete_rows", description: "Delete rows by condition" },
    { name: "create_table", description: "Create a new table" },
    { name: "add_column", description: "Add a column (schema migration)" },
    { name: "create_index", description: "Create an index" },
    { name: "run_sql", description: "Run any SQL statement" },
  ],
}));"""

INSERT_SNIPPET = """case "insert": {
  const cols = Object.keys(args.data);
  const vals = Object.values(args.data);
  const ph = vals.map((_, i) => `$${i + 1}`).join(",");
  const sql = `INSERT INTO ${args.table} (${cols.join(",")}) VALUES (${ph}) RETURNING *`;
  const rows = await runSql(sql, vals);
  return mcpText(rows);
}"""

AUTH_SNIPPET = """app.post("/mcp", async (req, res) => {
  const auth = req.headers["authorization"];
  if (SECRET_KEY && (!auth || auth !== `Bearer ${SECRET_KEY}`)) {
    return res.status(401).json({ error: "Unauthorized" });
  }
  // Streamable HTTP transport per request
  ...
});"""

N8N_SNIPPET = """Name:       PostgreSQL MCP
Transport:  Streamable HTTP
URL:        http://localhost:9002/mcp
Headers:    Authorization: Bearer <token>"""

T = {
    "ru": {
        "title": "🔌 Собственный MCP-сервер",
        "caption": "PostgreSQL MCP-сервер собственной разработки: 10 инструментов, Streamable HTTP, "
                   "Bearer-аутентификация. Работает в прод-сценариях n8n и Unified Agent.",
        "mcp_h": "PostgreSQL MCP Server",
        "mcp_d": "Собственная реализация MCP-сервера на Node.js (официальный SDK): 10 инструментов, "
                 "ресурсы и промпты, транспорт Streamable HTTP, проверка Bearer-токена на каждом запросе. "
                 "Агент работает с базой через стандартный протокол — строит SQL из запроса пользователя "
                 "и возвращает результат в чат, без SQL в коде воркфлоу. "
                 "В проде обслуживает создание и обогащение CRM-записей в воркфлоу **Lead Qualification** "
                 "и инструментарий **Unified Agent**.",
        "code_h": "Фрагменты кода",
        "code_caption": "Полный код: `projects/mcp-servers/pg-mcp-server/server.js` (325 строк, v1.0.0) — "
                        "регистрация инструментов с JSON Schema, параметризованные SQL-запросы, авторизация.",
        "arch": "Архитектура",
        "tools_n": "Инструментов",
        "transport": "Транспорт",
        "port": "Порт",
        "auth_n": "Авторизация",
        "agent": "AI Agent / n8n",
        "client": "MCP Client",
        "server": "MCP Server (pg)",
        "db": "PostgreSQL",
        "tools_h": "**Все 10 инструментов агента:**",
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
        "tool": "Tool",
        "desc_col": "Описание",
        "params": "Параметры",
        "res_prompts": "Resources: `postgres://tables`, `postgres://table/{name}` · "
                       "Промпты: `explain_table`, `query_data`.",
        "demo_h": "Мини-демо (JSON-RPC вызов инструмента `select`):",
        "req": "Запрос:",
        "resp": "Ответ (сокращённо):",
        "endpoint": "Эндпоинт: `POST http://localhost:9002/mcp` · Auth: `Authorization: Bearer <token>`",
        "paths_h": "Свой MCP-сервер или готовый: три способа запуска",
        "paths_d": "Протокол один — вариантов, как стоять сервер, три. Наш Node.js-сервер работает "
                   "как отдельный процесс: к нему подключается любой агент — в наших воркфлоу "
                   "(Lead Qualification, Unified Agent) или воркфлоу клиента — через ноду MCP Client. "
                   "Пакет для MySQL — когда функционала коробочного достаточно. Вариант на нодах n8n — "
                   "прототип без деплоя.",
        "path_cols": ["Путь", "Код", "Где применён у нас", "Когда брать"],
        "path_rows": [
            {"Путь": "Свой Node.js-сервер (этот)", "Код": "325 строк, официальный SDK",
             "Где применён у нас": "Lead Qualification, Unified Agent (порт 9002)",
             "Когда брать": "Прод: контроль прав, авторизация, свои инструменты"},
            {"Путь": "Готовый npm-пакет (MySQL)", "Код": "Без кода, env-конфиг",
             "Где применён у нас": "Мониторинг новостей: запросы к MySQL (порт 9001)",
             "Когда брать": "Быстро дать агенту доступ к существующей БД"},
            {"Путь": "MCP Server Trigger в n8n", "Код": "Только ноды",
             "Где применён у нас": "Прототип PostgreSQL MCP (Postgres Tool + Agent Tool)",
             "Когда брать": "Zero-deploy прототипы из базовых нод"},
        ],
        "n8n_h": "Подключение к агенту в n8n",
        "n8n_d": "Нода **MCP Client** включается в **AI Agent** как источник инструментов: агент видит "
                 "все 10 tools, сам решает, к каким обратиться, и по схеме передаёт аргументы. "
                 "Полный туториал с тремя сценариями запуска сервера (ngrok / локально / custom): "
                 "`projects/mcp-servers/mcp_tutorial.md`.",
    },
    "en": {
        "title": "🔌 Own MCP Server",
        "caption": "PostgreSQL MCP server of our own build: 10 tools, Streamable HTTP, "
                   "Bearer authentication. Runs in production n8n scenarios and the Unified Agent.",
        "mcp_h": "PostgreSQL MCP Server",
        "mcp_d": "An MCP server implemented from scratch in Node.js (official SDK): 10 tools, "
                 "resources and prompts, Streamable HTTP transport, Bearer-token check on every request. "
                 "The agent works with the database through the standard protocol — it builds SQL from the "
                 "user's question and returns the result to chat, with no SQL hardcoded in the workflow. "
                 "In production it serves CRM record creation and enrichment in the **Lead Qualification** "
                 "workflow and powers the **Unified Agent** toolset.",
        "code_h": "Code fragments",
        "code_caption": "Full code: `projects/mcp-servers/pg-mcp-server/server.js` (325 lines, v1.0.0) — "
                        "tool registration with JSON Schema, parameterized SQL queries, authorization.",
        "arch": "Architecture",
        "tools_n": "Tools",
        "transport": "Transport",
        "port": "Port",
        "auth_n": "Auth",
        "agent": "AI Agent / n8n",
        "client": "MCP Client",
        "server": "MCP Server (pg)",
        "db": "PostgreSQL",
        "tools_h": "**All 10 agent tools:**",
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
        "tool": "Tool",
        "desc_col": "Description",
        "params": "Parameters",
        "res_prompts": "Resources: `postgres://tables`, `postgres://table/{name}` · "
                       "Prompts: `explain_table`, `query_data`.",
        "demo_h": "Mini-demo (JSON-RPC call of the `select` tool):",
        "req": "Request:",
        "resp": "Response (abridged):",
        "endpoint": "Endpoint: `POST http://localhost:9002/mcp` · Auth: `Authorization: Bearer <token>`",
        "paths_h": "Custom server or off-the-shelf: three ways to run MCP",
        "paths_d": "One protocol, three ways to run a server. Our Node.js server works as a standalone "
                   "process: any agent connects to it — in our workflows (Lead Qualification, Unified Agent) "
                   "or in a client's workflow — via the MCP Client node. The MySQL package is for cases "
                   "where the off-the-shelf feature set is enough. The nodes-only n8n variant covers "
                   "zero-deploy prototypes.",
        "path_cols": ["Path", "Code", "Applied in our project", "Pick when"],
        "path_rows": [
            {"Path": "Own Node.js server (this page)", "Code": "325 lines, official SDK",
             "Applied in our project": "Lead Qualification, Unified Agent (port 9002)",
             "Pick when": "Production: access control, authentication, custom tools"},
            {"Path": "Ready npm package (MySQL)", "Code": "No code, env config",
             "Applied in our project": "News monitor: queries to MySQL (port 9001)",
             "Pick when": "Quickly bridge an agent to an existing database"},
            {"Path": "MCP Server Trigger in n8n", "Code": "Nodes only",
             "Applied in our project": "PostgreSQL MCP prototype (Postgres Tool + Agent Tool)",
             "Pick when": "Zero-deploy prototypes from base nodes"},
        ],
        "n8n_h": "Connecting to an n8n agent",
        "n8n_d": "The **MCP Client** node plugs into an **AI Agent** as a tool source: the agent sees all "
                 "10 tools, decides which to call, and passes arguments per JSON Schema. Full tutorial with "
                 "three server launch scenarios (ngrok / local / custom): "
                 "`projects/mcp-servers/mcp_tutorial.md`.",
    },
}[lang]

st.title(T["title"])
st.caption(T["caption"])

st.subheader(T["mcp_h"])
st.write(T["mcp_d"])
c1, c2, c3, c4 = st.columns(4)
c1.metric(T["tools_n"], "10")
c2.metric(T["transport"], "Streamable HTTP")
c3.metric(T["port"], "9002")
c4.metric(T["auth_n"], "Bearer")
st.markdown(f"**{T['arch']}**")
render_mermaid(
    "flowchart LR\n"
    f'  A["{T["agent"]}"] --> C["{T["client"]}"]\n'
    f'  C --> S["{T["server"]}"]\n'
    f'  S --> D[("{T["db"]}")]',
    height=200,
    font_size=13
)

st.subheader(T["code_h"])
st.caption(T["code_caption"])
st.code(TOOLS_SNIPPET, language="javascript")
st.code(INSERT_SNIPPET, language="javascript")
st.code(AUTH_SNIPPET, language="javascript")

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

st.markdown("---")
st.subheader(T["paths_h"])
st.write(T["paths_d"])
st.dataframe(T["path_rows"], use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader(T["n8n_h"])
st.write(T["n8n_d"])
st.code(N8N_SNIPPET, language="bash")



