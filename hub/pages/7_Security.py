"""Security & Guardrails — defence layers, SQL rules, PII, access and evidence. (RU/EN)"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HUB)

import streamlit as st
from diagrams import render_mermaid
from i18n import lang_switcher

st.set_page_config(page_title="Security & Guardrails", page_icon="🔐", layout="wide")

lang = lang_switcher()

T = {
    "ru": {
        "title": "🔐 Безопасность и Guardrails",
        "caption": "Что именно не даёт агенту писать в прод-базу и уносить PII: слои защиты, правила SQL, "
                   "лимиты, доступы и артефакты — с реальными примерами из этого демо.",
        "lay_h": "**Защита в глубину**",
        "dia": {"q": "Вопрос", "a": "Агент · валидация SQL", "m": "MCP · Bearer + проверки + LIMIT",
                "p": "PostgreSQL · read-only", "x": "Отказ · до обращения к БД"},
        "lay_cap": "Отказ на любом слое — запрос не выполняется. Проверки дублируются: то, что пропустит "
                   "клиент, отсечёт MCP-сервер, а запись не пустит роль в самой БД.",
        "sql_h": "**Read-only SQL: как это выглядит**",
        "sql_cols": ("Запрос", "Что происходит", "Слой"),
        "sql_rows": [
            ("SELECT COUNT(*) FROM leads_leads", "Выполняется; сервер добавляет LIMIT 100, если его нет", "MCP"),
            ("WITH x AS (SELECT 1) SELECT * FROM x", "Разрешено: WITH относится к read-only", "Агент"),
            ("DELETE FROM leads_leads", "Отказ: «only SELECT / WITH statements are allowed»", "Агент"),
            ("SELECT 1; DROP TABLE leads_leads", "Отказ: «multiple statements are not allowed»", "Агент"),
            ("SELECT * FROM auth_users", "Отказ: «table not in allowlist»", "Агент"),
            ("…INSERT… внутри SELECT", "Отказ по стоп-словам (insert, update, delete, drop…)", "Агент"),
        ],
        "sql_note": "Белый список таблиц: leads_leads, leads_contacts, leads_companies, llm_usage, llm_pricing. "
                    "На MCP-сервере — свой слой: Bearer-токен (иначе 401), валидация имён таблиц, "
                    "жёсткий READ_ONLY-режим по флагу и аудит-лог вызовов.",
        "pii_h": "**PII не уходит в модель**",
        "pii_b": "E-mail и телефоны маскируются в результатах инструментов до того, как данные попадут "
                 "в языковую модель — переключатель в демо. Модель физически не видит реальный адрес.",
        "pii_code": "Вопрос: What is the e-mail of the highest-scoring lead?\n"
                    "Ответ:  The email of the highest-scoring lead is [email] [DB].\n\n"
                    "sundar@google.com       → [email]\n"
                    "+7 999 123-45-67        → [phone]",
        "pii_ver": "Проверено живым прогоном (27.10): при включённом переключателе в ответе [email], "
                   "реальный адрес не появился ни в ответе, ни в трейсе.",
        "acc_h": "**Доступы и секреты**",
        "acc": [
            ("Bearer-токен на MCP", "Запрос без токена получает 401. Секрет лежит в файле вне "
                                     "репозитория (~/mcp_token.env) или в переменной окружения."),
            ("Секреты — только в .env", "Ключи моделей и БД в .gitignore; в публичном репозитории "
                                        "ключей нет (токен бота в примере заменён заглушкой)."),
            ("Демо-база — синтетическая", "CRM в демо наполнена вымышленными данными; ваши данные "
                                          "сюда не передаются."),
            ("Доступы — по согласованию", "Пароли и ключи не отправляются в переписке: для доступов "
                                          "используем защищённый канал."),
        ],
        "lim_h": "**Лимиты и устойчивость**",
        "lim": [
            ("Лимит шагов и таймауты", "Не больше 4 шагов и таймауты на вызовы — агент не зацикливается "
                                       "на сбое инструмента."),
            ("Честный отказ при сбое", "Если CRM-сервер недоступен, агент говорит об этом и отвечает по "
                                       "базе знаний — без выдуманных цифр."),
            ("Перекрёстная проверка данных", "Если в диалоге уже был факт из БД, агент обязан перезапросить "
                                             "БД перед повторным ответом — иначе ответ не принимается."),
            ("Стоп-слова и allowlist", "Двойной слой: на клиенте и на MCP-сервере."),
        ],
        "trace_h": "**Прозрачность и аудит**",
        "trace": [
            "Трейс каждого вызова: инструмент, аргументы, время, результат — прямо в интерфейсе демо.",
            "Токены, латентность и стоимость на каждый ответ; трейс скачивается в JSON.",
            "Аудит-лог на MCP-сервере: вызовы инструментов и HTTP-события (включается файлом AUDIT_FILE).",
        ],
        "ev_h": "**Что проверено на этом демо**",
        "ev": [
            "«Удали все строки из leads_leads» → отказ, ноль вызовов инструментов, данные целы.",
            "Живой CRM-запрос → реальный SELECT, SQL виден в трейсе.",
            "Повторный вопрос в диалоге → принудительный повторный запрос в БД (фикс устаревших ответов).",
            "PII-переключатель включён → в ответе [email], реальный адрес не утёк.",
            "MCP-сервер выключен → честное сообщение о недоступности и ответ по базе знаний.",
        ],
        "scope_h": "**Границы**",
        "scope": "Это защита внутри продукта, а не пентест, нагрузочное тестирование или DLP-система. "
                 "Для compliance-требований (SOC 2, ISO, аудит) — отдельный разговор и отдельные проверки.",
        "see_h": "**Смотрите также**",
        "see": [
            ("pages/7_Unified_Agent.py", "🧭 Unified Agent: guardrails в работе"),
            ("pages/4_MCP.py", "🔌 MCP-серверы: auth и инструменты"),
            ("pages/9_Testing.py", "🧪 Тестирование: метрики и аудит качества"),
        ],
        "foot": "Описанные проверки реализованы в этом репозитории: hub/agents/unified_agent.py и "
                "projects/mcp-servers/pg-mcp-server.",
    },
    "en": {
        "title": "🔐 Security & Guardrails",
        "caption": "What exactly stops the agent from writing to a production database and leaking PII: "
                   "defence layers, SQL rules, limits, access and artefacts — with real examples from "
                   "this demo.",
        "lay_h": "**Defence in depth**",
        "dia": {"q": "Question", "a": "Agent · SQL validation", "m": "MCP · Bearer + checks + LIMIT",
                "p": "PostgreSQL · read-only", "x": "Refusal · before the DB is touched"},
        "lay_cap": "A refusal at any layer means the query never runs. The checks are duplicated: whatever "
                   "the client misses, the MCP server catches, and the database role refuses writes.",
        "sql_h": "**Read-only SQL in practice**",
        "sql_cols": ("Query", "What happens", "Layer"),
        "sql_rows": [
            ("SELECT COUNT(*) FROM leads_leads", "Runs; the server adds LIMIT 100 if missing", "MCP"),
            ("WITH x AS (SELECT 1) SELECT * FROM x", "Allowed: WITH is read-only", "Agent"),
            ("DELETE FROM leads_leads", "Refused: \"only SELECT / WITH statements are allowed\"", "Agent"),
            ("SELECT 1; DROP TABLE leads_leads", "Refused: \"multiple statements are not allowed\"", "Agent"),
            ("SELECT * FROM auth_users", "Refused: \"table not in allowlist\"", "Agent"),
            ("…INSERT… inside a SELECT", "Refused by stop-words (insert, update, delete, drop…)", "Agent"),
        ],
        "sql_note": "Table allowlist: leads_leads, leads_contacts, leads_companies, llm_usage, llm_pricing. "
                    "The MCP server has its own layer: Bearer token (401 otherwise), identifier validation, "
                    "a hard READ_ONLY mode behind a flag, and an audit log of calls.",
        "pii_h": "**PII never reaches the model**",
        "pii_b": "E-mails and phone numbers are masked in tool results before the data reaches the language "
                 "model — a toggle in the demo. The model never sees the real address.",
        "pii_code": "Question: What is the e-mail of the highest-scoring lead?\n"
                    "Answer:   The email of the highest-scoring lead is [email] [DB].\n\n"
                    "sundar@google.com       → [email]\n"
                    "+7 999 123-45-67        → [phone]",
        "pii_ver": "Verified with a live run (27 Oct): with the toggle on the answer contains [email] and "
                   "the real address appears neither in the answer nor in the trace.",
        "acc_h": "**Access and secrets**",
        "acc": [
            ("Bearer token on MCP", "A request without the token gets 401. The secret lives outside the "
                                    "repository (~/mcp_token.env) or in an environment variable."),
            ("Secrets only in .env", "Model and DB keys are gitignored; the public repository contains no "
                                     "keys (the bot token in the sample is a placeholder)."),
            ("Synthetic demo database", "The demo CRM is filled with made-up data; your data is never "
                                        "pushed here."),
            ("Access by agreement", "Passwords and keys are never sent in chat: we use a secure channel "
                                    "for access."),
        ],
        "lim_h": "**Limits and resilience**",
        "lim": [
            ("Step limit and timeouts", "No more than 4 steps and per-call timeouts — the agent cannot "
                                        "loop on a failing tool."),
            ("Honest failure", "If the CRM server is down, the agent says so and answers from the knowledge "
                               "base — no invented numbers."),
            ("Cross-check of facts", "If a DB fact already appeared in the dialog, the agent must re-query "
                                     "the DB before restating it — otherwise the answer is rejected."),
            ("Stop-words and allowlist", "Two layers: on the client and on the MCP server."),
        ],
        "trace_h": "**Transparency and audit**",
        "trace": [
            "A trace of every call: tool, arguments, latency, result — right in the demo UI.",
            "Tokens, latency and cost per answer; the trace downloads as JSON.",
            "Audit log on the MCP server: tool calls and HTTP events (enabled via AUDIT_FILE).",
        ],
        "ev_h": "**Verified on this demo**",
        "ev": [
            "\"Delete every row from leads_leads\" → refusal, zero tool calls, data intact.",
            "Live CRM question → a real SELECT, with the SQL visible in the trace.",
            "Repeat question in a dialog → a forced fresh DB query (stale-answer fix).",
            "PII toggle on → the answer shows [email], the real address never leaks.",
            "MCP server down → an honest message plus an answer from the knowledge base.",
        ],
        "scope_h": "**Boundaries**",
        "scope": "This is in-product protection, not a pentest, load test or DLP system. For compliance "
                 "requirements (SOC 2, ISO, audit) there is a separate conversation and separate checks.",
        "see_h": "**See also**",
        "see": [
            ("pages/7_Unified_Agent.py", "🧭 Unified Agent: guardrails at work"),
            ("pages/4_MCP.py", "🔌 MCP servers: auth and tools"),
            ("pages/9_Testing.py", "🧪 Testing: quality metrics and audit"),
        ],
        "foot": "The checks described here live in this repository: hub/agents/unified_agent.py and "
                "projects/mcp-servers/pg-mcp-server.",
    },
}[lang]

st.title(T["title"])
st.caption(T["caption"])


def gap(px: int = 12) -> None:
    st.markdown(f"<div style='height:{px}px'></div>", unsafe_allow_html=True)


def table(cols, rows) -> None:
    head = "| " + " | ".join(cols) + " |\n|" + "|".join(["---"] * len(cols)) + "|\n"
    body = "".join("| " + " | ".join(f"`{c}`" if i == 0 else c for i, c in enumerate(r)) + " |\n"
                   for r in rows)
    st.markdown(head + body)


gap()
st.markdown(T["lay_h"])
D_ = T["dia"]
render_mermaid(
    "flowchart LR\n"
    f'  Q[["{D_["q"]}"]] --> A["{D_["a"]}"]\n'
    f'  A --> M["{D_["m"]}"]\n'
    f'  M --> P[("{D_["p"]}")]\n'
    f'  A -.-> X[["{D_["x"]}"]]',
    height=210,
    max_width=820,
    font_size=13,
)
st.caption(T["lay_cap"])

gap()
st.markdown(T["sql_h"])
table(T["sql_cols"], T["sql_rows"])
st.caption(T["sql_note"])

gap()
st.markdown(T["pii_h"])
st.write(T["pii_b"])
st.code(T["pii_code"], language=None)
st.success(T["pii_ver"])

gap()
st.markdown(T["acc_h"])
for col, (t, d) in zip(st.columns(4), T["acc"]):
    with col:
        st.markdown(f"**{t}**")
        st.caption(d)

gap()
st.markdown(T["lim_h"])
for col, (t, d) in zip(st.columns(4), T["lim"]):
    with col:
        with st.container(border=True):
            st.markdown(f"**{t}**")
            st.write(d)

gap()
st.markdown(T["trace_h"])
for line in T["trace"]:
    st.markdown(f"- {line}")

gap()
st.markdown(T["ev_h"])
for line in T["ev"]:
    st.markdown(f"- ✅ {line}")

gap()
st.markdown(T["scope_h"])
st.info(T["scope"])

gap()
st.markdown(T["see_h"])
for page, label in T["see"]:
    st.page_link(page, label=label)

gap()
st.caption(T["foot"])
