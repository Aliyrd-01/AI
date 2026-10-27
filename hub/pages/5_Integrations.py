"""Integrations — data sources and targets with protocols, demo status and requirements. (RU/EN)"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HUB)

import streamlit as st
from i18n import lang_switcher

st.set_page_config(page_title="Integrations", page_icon="🔌", layout="wide")

lang = lang_switcher()

T = {
    "ru": {
        "title": "🔌 Интеграции",
        "caption": "С чем соединяемся: источники данных на входе и приёмники на выходе. Для каждой связи — "
                   "протокол, статус в демо и что нужно, чтобы её подключить.",
        "legend": "✅ включено в демо  ·  ⚪ есть в репозитории, к демо не подключено",
        "how": "Схема",
        "note": "Обработка посередине — это RAG-индекс (Qdrant), MCP-мост к SQL и n8n-воркфлоу; "
                "все связи на схеме реальные, без мокапов.",
        "in_h": "**Источники (вход)**",
        "out_h": "**Приёмники (выход)**",
        "cols_in": ("Источник", "Протокол", "Куда идёт", "Статус", "Что нужно для подключения"),
        "cols_out": ("Приёмник", "Протокол", "Что делает", "Статус", "Что нужно для подключения"),
        "in_rows": [
            ("Документы (txt, md, docx, pdf)", "Файлы → чанки",
             "RAG-индекс · Qdrant", "✅ в демо", "Папка/архив, правила чанкинга"),
            ("Веб-страницы", "HTTP + парсинг",
             "Web Surfer · research-флоу", "✅ в демо", "Список доменов, лимиты глубины"),
            ("PostgreSQL (CRM)", "SQL read-only · MCP",
             "Unified Agent, n8n", "✅ в демо", "Хост/порт/БД, read-only-роль, MCP_TOKEN"),
            ("MySQL", "SQL · MCP",
             "MCP MySQL-сервер", "⚪ в репо", "Хост/порт/БД, креды"),
            ("Telegram (входящие)", "Long polling / webhook",
             "n8n Support & Escalation", "✅ в демо", "Bot token, chat id оператора"),
            ("Web-форма лида", "Webhook · Basic Auth",
             "n8n Lead Qualification", "✅ в демо", "URL вебхука, креды формы"),
            ("RSS-ленты", "RSS / Atom",
             "n8n Content Publisher", "✅ в демо", "URL фида, расписание запуска"),
        ],
        "out_rows": [
            ("Qdrant Cloud", "REST · vector DB",
             "Хранит индекс и выдаёт чанки", "✅ в демо", "QDRANT_URL, API-ключ, коллекция"),
            ("PostgreSQL (CRM)", "SQL · native nodes / MCP",
             "Чтение и upsert лидов", "✅ в демо", "Креды, схема таблиц"),
            ("Telegram (ответы, алерты)", "Bot API",
             "Ответ клиенту, алерт оператору", "✅ в демо", "Bot token"),
            ("LLM API (OpenAI-совместимый)", "HTTPS · chat completions",
             "RAG-генерация, агент, LLM-судья", "✅ в демо", "API-ключ, base URL, модель"),
            ("MCP-клиенты (Claude, Inspector)", "MCP · Streamable HTTP",
             "Ходят в наши MCP-серверы", "✅ в демо", "URL /mcp + Bearer-токен"),
            ("Любой HTTP/REST сервис", "HTTP · n8n node",
             "CRM, ERP, внутренние API", "⚪ в репо", "URL, метод, авторизация"),
            ("Файлы результатов (CSV, SQL, DOCX)", "Файлы",
             "Выгрузка отчётов и данных", "✅ в демо", "—"),
        ],
        "llm_h": "**LLM-провайдеры**",
        "llm": [
            ("Qubax", "Основная модель демо: qwen3-235b-a22b (tool-calling)", "✅ в демо"),
            ("8 моделей в бенчмарке", "Grok, Gemini, GLM, Kimi, Qwen, DeepSeek, Mistral, MiniMax", "✅ в демо"),
            ("Любой OpenAI-совместимый API", "Меняется base URL и модель в .env", "✅ поддержано"),
        ],
        "steps_h": "**Как подключить новый источник**",
        "steps": [
            ("1 · Контракт", "Описываем, как получаем данные: API/файл/вебхук, авторизация, "
                             "частота, объём."),
            ("2 · Связка", "Tool в агенте, нода в n8n или ингест в RAG-индекс — в зависимости от "
                           "сценария."),
            ("3 · Проверка", "Прогон на eval-наборе или сценариях: метрики до/после, трейс вызовов."),
        ],
        "see_h": "**Смотрите также**",
        "see": [
            ("pages/4_MCP.py", "🔌 MCP-серверы: SQL через чат"),
            ("pages/1_RAG.py", "🔎 RAG-система: retrieval и цитаты"),
            ("pages/2_N8N.py", "🔗 n8n-пайплайны"),
            ("pages/7_Unified_Agent.py", "🧭 Unified Agent: RAG + CRM"),
        ],
        "dia": {"docs": "Документы", "web": "Веб / RSS", "form": "Web-форма", "tg": "Telegram",
                "rag": "RAG-индекс · Qdrant", "n8n": "n8n-воркфлоу", "agent": "Агент · LLM",
                "crm": "PostgreSQL CRM", "mcp": "MCP-мост", "out": "Ответ / отчёт"},
        "foot": "Статус «в демо» означает, что связь реально работает на этом сайте; «в репо» — код есть "
                "в репозитории, подключение выполняется под задачу.",
    },
    "en": {
        "title": "🔌 Integrations",
        "caption": "What we connect to: data sources on the way in and targets on the way out. For every "
                   "link — protocol, demo status and what it takes to wire it up.",
        "legend": "✅ wired into the demo  ·  ⚪ in the repository, not wired to the demo",
        "how": "Architecture",
        "note": "Processing in the middle is the RAG index (Qdrant), the MCP bridge to SQL and n8n "
                "workflows; every link on the diagram is real, no mockups.",
        "in_h": "**Sources (input)**",
        "out_h": "**Targets (output)**",
        "cols_in": ("Source", "Protocol", "Goes to", "Status", "What it takes to connect"),
        "cols_out": ("Target", "Protocol", "What it does", "Status", "What it takes to connect"),
        "in_rows": [
            ("Documents (txt, md, docx, pdf)", "Files → chunks",
             "RAG index · Qdrant", "✅ in demo", "Folder/archive, chunking rules"),
            ("Web pages", "HTTP + parsing",
             "Web Surfer · research flow", "✅ in demo", "Domain list, depth limits"),
            ("PostgreSQL (CRM)", "read-only SQL · MCP",
             "Unified Agent, n8n", "✅ in demo", "Host/port/db, read-only role, MCP_TOKEN"),
            ("MySQL", "SQL · MCP",
             "MCP MySQL server", "⚪ in repo", "Host/port/db, credentials"),
            ("Telegram (incoming)", "Long polling / webhook",
             "n8n Support & Escalation", "✅ in demo", "Bot token, operator chat id"),
            ("Lead web form", "Webhook · Basic Auth",
             "n8n Lead Qualification", "✅ in demo", "Webhook URL, form credentials"),
            ("RSS feeds", "RSS / Atom",
             "n8n Content Publisher", "✅ in demo", "Feed URL, schedule"),
        ],
        "out_rows": [
            ("Qdrant Cloud", "REST · vector DB",
             "Stores the index, serves chunks", "✅ in demo", "QDRANT_URL, API key, collection"),
            ("PostgreSQL (CRM)", "SQL · native nodes / MCP",
             "Reads and upserts leads", "✅ in demo", "Credentials, table schema"),
            ("Telegram (answers, alerts)", "Bot API",
             "Customer reply, operator alert", "✅ in demo", "Bot token"),
            ("LLM API (OpenAI-compatible)", "HTTPS · chat completions",
             "RAG generation, agent, LLM judge", "✅ in demo", "API key, base URL, model"),
            ("MCP clients (Claude, Inspector)", "MCP · Streamable HTTP",
             "Call our MCP servers", "✅ in demo", "URL /mcp + Bearer token"),
            ("Any HTTP/REST service", "HTTP · n8n node",
             "CRM, ERP, internal APIs", "⚪ in repo", "URL, method, auth"),
            ("Result files (CSV, SQL, DOCX)", "Files",
             "Report and data exports", "✅ in demo", "—"),
        ],
        "llm_h": "**LLM providers**",
        "llm": [
            ("Qubax", "Primary demo model: qwen3-235b-a22b (tool-calling)", "✅ in demo"),
            ("8 models in the benchmark", "Grok, Gemini, GLM, Kimi, Qwen, DeepSeek, Mistral, MiniMax", "✅ in demo"),
            ("Any OpenAI-compatible API", "Switch base URL and model in .env", "✅ supported"),
        ],
        "steps_h": "**How to wire a new source**",
        "steps": [
            ("1 · Contract", "Describe how we get the data: API/file/webhook, auth, rate, volume."),
            ("2 · Wiring", "A tool in the agent, a node in n8n, or ingestion into the RAG index — "
                           "whichever the scenario needs."),
            ("3 · Verification", "Run the eval set or scenarios: metrics before/after, a trace of calls."),
        ],
        "see_h": "**See also**",
        "see": [
            ("pages/4_MCP.py", "🔌 MCP servers: SQL through chat"),
            ("pages/1_RAG.py", "🔎 RAG system: retrieval and citations"),
            ("pages/2_N8N.py", "🔗 n8n pipelines"),
            ("pages/7_Unified_Agent.py", "🧭 Unified Agent: RAG + CRM"),
        ],
        "dia": {"docs": "Documents", "web": "Web / RSS", "form": "Lead form", "tg": "Telegram",
                "rag": "RAG index · Qdrant", "n8n": "n8n workflows", "agent": "Agent · LLM",
                "crm": "PostgreSQL CRM", "mcp": "MCP bridge", "out": "Answer / report"},
        "foot": "\"In demo\" means the link really works on this site; \"in repo\" means the code is in the "
                "repository and the connection is wired per project.",
    },
}[lang]

st.title(T["title"])
st.caption(T["caption"])
st.caption(T["legend"])


def gap(px: int = 12) -> None:
    st.markdown(f"<div style='height:{px}px'></div>", unsafe_allow_html=True)


def table(cols, rows) -> None:
    head = "| " + " | ".join(cols) + " |\n|" + "|".join(["---"] * len(cols)) + "|\n"
    body = "".join("| " + " | ".join(r) + " |\n" for r in rows)
    st.markdown(head + body)


gap()
st.markdown(f"**{T['how']}**")
from diagrams import render_mermaid

D_ = T["dia"]
render_mermaid(
    "flowchart LR\n"
    f'  D[["{D_["docs"]}"]] --> R["{D_["rag"]}"]\n'
    f'  W[["{D_["web"]}"]] --> N["{D_["n8n"]}"]\n'
    f'  F[["{D_["form"]}"]] --> N\n'
    f'  TG[["{D_["tg"]}"]] <--> N\n'
    f'  R <--> A["{D_["agent"]}"]\n'
    f'  S[("{D_["crm"]}")] <--> M["{D_["mcp"]}"]\n'
    f'  M <--> A\n'
    f'  A --> O[["{D_["out"]}"]]\n'
    f'  N --> S',
    height=250,
    max_width=820,
    font_size=13,
)
st.caption(T["note"])

gap()
st.markdown(T["in_h"])
table(T["cols_in"], T["in_rows"])

gap()
st.markdown(T["out_h"])
table(T["cols_out"], T["out_rows"])

gap()
st.markdown(T["llm_h"])
for col, (name, desc, status) in zip(st.columns(3), T["llm"]):
    with col:
        with st.container(border=True):
            st.markdown(f"**{name}** — {status}")
            st.caption(desc)

gap()
st.markdown(T["steps_h"])
for col, (t, d) in zip(st.columns(3), T["steps"]):
    with col:
        with st.container(border=True):
            st.markdown(f"**{t}**")
            st.write(d)

gap()
st.markdown(T["see_h"])
for page, label in T["see"]:
    st.page_link(page, label=label)

gap()
st.caption(T["foot"])
