"""Agents — AutoAgent multi-agent framework + 3 implementation flows (RU/EN)."""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HUB)

import pandas as pd
import streamlit as st
from diagrams import render_mermaid
from i18n import lang_switcher

ASSETS = os.path.join(HUB, "assets", "agents")

st.set_page_config(page_title="Agents", page_icon="🤖", layout="wide")

lang = lang_switcher()

T = {
    "ru": {
        "title": "🤖 Agents",
        "caption": "Автономные агенты: AutoAgent (multi-agent) и 3 практических флоу.",
        "auto_h": "AutoAgent — маршрутизация задач по под-агентам",
        "auto_d": "Open-source фреймворк **AutoAgent (HKUDS)**: головной **System Triage Agent** "
                  "принимает задачу на естественном языке и делегирует её под-агентам — "
                  "**File Surfer** (локальные файлы и документы), **Web Surfer** (поиск в интернете) "
                  "и **Coding Agent** (код, рефакторинг, тесты). Результаты собираются в один ответ.",
        "arch": "Архитектура",
        "agents_n": "Агентов",
        "flows_n": "Флоу",
        "models_n": "Модели",
        "phase_models": "Модели по ролям (multi-model):",
        "role": "Роль",
        "model": "Модель",
        "phase": "Фаза",
        "models_note": "Модели настраиваются под конкретный флоу: цена, скорость, качество.",
        "task": "Задача",
        "triage": "System Triage Agent",
        "file": "File Surfer",
        "web": "Web Surfer",
        "coding": "Coding Agent",
        "planner": "Planner",
        "compiler": "Compiler",
        "tester": "Tester",
        "reporter": "Reporter",
        "extract": "Extraction",
        "validate": "Validation",
        "mcp": "MCP PostgreSQL",
        "result": "Итог",
        "ex_h": "3 флоу",
        "flow_h": "Флоу",
        "result_h": "Результат прогона",
        "artifacts_h": "Артефакты",
        "run_h": "Запуск",
        "ex1_t": "📄 1 · Research-ассистент",
        "ex1_goal": "**Задача:** по теме собрать факты из интернета и локальных документов, "
                    "выдать отчёт со ссылками на источники.",
        "ex1_flow": "**Флоу:**\n"
                    "- `Planner` — 2–4 подзадачи + поисковые запросы\n"
                    "- `Web Surfer` — DuckDuckGo, дедупликация домена, текст страниц\n"
                    "- `File Surfer` — локальные `sources/` по совпадению ключевых слов\n"
                    "- `Compiler` — отчёт с ссылками `[n]`, расхождениями и ограничениями",
        "ex1_value": "**Ценность:** отчёт с цитатами и проверкой источников; вход — вопрос, "
                     "выход — `report.md` и `report.docx`.",
        "subtasks": "Подзадач",
        "sources_n": "Источников",
        "local_web": "Локальные / web",
        "report_h": "Отчёт",
        "sources_h": "Источники",
        "sample_ru": "Фрагмент реального отчёта (вход на русском).",
        "ex2_t": "🛠 2 · Агент по репозиторию",
        "ex2_goal": "**Задача:** найти баги в репозитории, исправить их и подтвердить тестами, "
                    "собрать отчёт с diff.",
        "ex2_flow": "**Флоу:**\n"
                    "- `Planner` — читает код и вывод pytest, находит причины падений\n"
                    "- `Coding Agent` — правит каждый файл, проверяет синтаксис\n"
                    "- `Tester` — pytest на копии, до 3 итераций\n"
                    "- `Reporter` — баги, diff, результат тестов",
        "ex2_value": "**Ценность:** baseline → фикс → проверка тестами. Тесты агент менять не может.",
        "baseline": "Baseline",
        "after_fix": "После правок",
        "files_changed": "Файлов изменено",
        "baseline_out": "Baseline pytest",
        "final_out": "Финальный pytest",
        "diff_h": "Diff",
        "ex3_t": "🗂 3 · Документы → данные",
        "ex3_goal": "**Задача:** пачка входящих файлов → извлечь поля → таблица CSV и запись в БД.",
        "ex3_flow": "**Флоу:**\n"
                    "- `File Surfer` — txt / md / docx / pdf\n"
                    "- `Extraction` — строгий JSON по схеме, повтор при невалидном ответе\n"
                    "- `Validation` — pandas: пропуски, арифметика, сумма позиций, дубликаты\n"
                    "- `Output` — CSV, JSON, сводка и SQL; в SQL только строки OK",
        "ex3_value": "**Ценность:** входящие документы → таблица и готовый SQL; "
                     "CHECK-строки уходят на ручную проверку.",
        "docs_n": "Документов",
        "ok_check": "OK / CHECK",
        "valid_total": "Сумма OK",
        "invoices_h": "Счета",
        "items_h": "Позиции",
        "sql_h": "SQL для PostgreSQL (через MCP)",
        "rules_h": "Правила валидации",
        "rule_1": "обязательные поля не пустые",
        "rule_2": "total > 0",
        "rule_3": "subtotal + tax = total",
        "rule_4": "сумма позиций = subtotal",
        "rule_5": "invoice_no уникален",
        "check_note": "Строки CHECK в SQL не попадают.",
        "download": "Скачать",
        "src_case1": "Реализация: `case1_research.py`",
        "src_case2": "Реализация: `case2_repo.py`",
        "src_case3": "Реализация: `case3_docs_to_data.py`",
        "run_note": "Из корня проекта AutoAgent:",
        "gh_repo": "GitHub: репозиторий",
        "gh_cases": "Исходники трёх флоу",
        "stack": "Стек: Python · httpx · BeautifulSoup · pandas · pytest · python-docx · MCP",
    },
    "en": {
        "title": "🤖 Agents",
        "caption": "Autonomous agents: AutoAgent (multi-agent) and 3 hands-on flows.",
        "auto_h": "AutoAgent — Autonomous Task Orchestration",
        "auto_d": "Open-source **AutoAgent (HKUDS)** framework: the **System Triage Agent** "
                  "accepts a natural-language task and delegates it to specialized sub-agents — "
                  "**File Surfer** (local files and documents), **Web Surfer** (web search) "
                  "and **Coding Agent** (code, refactoring, tests). Results are aggregated.",
        "arch": "Architecture",
        "agents_n": "Agents",
        "flows_n": "Flows",
        "models_n": "Models",
        "phase_models": "Per-role models (multi-model):",
        "role": "Role",
        "model": "Model",
        "phase": "Phase",
        "models_note": "Models are configurable per flow: cost, speed, quality.",
        "task": "Task",
        "triage": "System Triage Agent",
        "file": "File Surfer",
        "web": "Web Surfer",
        "coding": "Coding Agent",
        "planner": "Planner",
        "compiler": "Compiler",
        "tester": "Tester",
        "reporter": "Reporter",
        "extract": "Extraction",
        "validate": "Validation",
        "mcp": "MCP PostgreSQL",
        "result": "Result",
        "ex_h": "3 flows",
        "flow_h": "Flow",
        "result_h": "Run result",
        "artifacts_h": "Artifacts",
        "run_h": "Run",
        "ex1_t": "📄 1 · Research assistant",
        "ex1_goal": "**Task:** gather facts from the web and local documents on a topic, "
                    "produce a report with source citations.",
        "ex1_flow": "**Flow:**\n"
                    "- `Planner` — 2–4 subtasks + search queries\n"
                    "- `Web Surfer` — DuckDuckGo, domain de-duplication, page text\n"
                    "- `File Surfer` — local `sources/` by keyword overlap\n"
                    "- `Compiler` — report with `[n]` citations, discrepancies and limitations",
        "ex1_value": "**Value:** a cited report with source checks; input — a question, "
                     "output — `report.md` and `report.docx`.",
        "subtasks": "Subtasks",
        "sources_n": "Sources",
        "local_web": "Local / web",
        "report_h": "Report",
        "sources_h": "Sources",
        "sample_ru": "Excerpt from the real run (input in Russian).",
        "ex2_t": "🛠 2 · Repository agent",
        "ex2_goal": "**Task:** find bugs in a repository, fix them, verify with tests, "
                    "produce a report with the diff.",
        "ex2_flow": "**Flow:**\n"
                    "- `Planner` — reads code and pytest output, finds failure causes\n"
                    "- `Coding Agent` — fixes each file, validates syntax\n"
                    "- `Tester` — pytest on the fixed copy, up to 3 iterations\n"
                    "- `Reporter` — bugs, diff, test result",
        "ex2_value": "**Value:** baseline → fix → test verification. The agent cannot edit tests.",
        "baseline": "Baseline",
        "after_fix": "After fixes",
        "files_changed": "Files changed",
        "baseline_out": "Baseline pytest",
        "final_out": "Final pytest",
        "diff_h": "Diff",
        "ex3_t": "🗂 3 · Documents → data",
        "ex3_goal": "**Task:** a batch of inbound files → extract fields → CSV table and DB rows.",
        "ex3_flow": "**Flow:**\n"
                    "- `File Surfer` — txt / md / docx / pdf\n"
                    "- `Extraction` — strict JSON schema, retry on invalid output\n"
                    "- `Validation` — pandas: missing fields, arithmetic, item sum, duplicates\n"
                    "- `Output` — CSV, JSON, summary and SQL; only OK rows reach SQL",
        "ex3_value": "**Value:** inbound documents → a table and ready SQL; "
                     "CHECK rows go to manual review.",
        "docs_n": "Documents",
        "ok_check": "OK / CHECK",
        "valid_total": "Valid total",
        "invoices_h": "Invoices",
        "items_h": "Line items",
        "sql_h": "SQL for PostgreSQL (via MCP)",
        "rules_h": "Validation rules",
        "rule_1": "required fields are present",
        "rule_2": "total > 0",
        "rule_3": "subtotal + tax = total",
        "rule_4": "sum of line items = subtotal",
        "rule_5": "invoice_no is unique",
        "check_note": "CHECK rows never reach the SQL file.",
        "download": "Download",
        "src_case1": "Implementation: `case1_research.py`",
        "src_case2": "Implementation: `case2_repo.py`",
        "src_case3": "Implementation: `case3_docs_to_data.py`",
        "run_note": "From the AutoAgent project root:",
        "gh_repo": "GitHub: repository",
        "gh_cases": "Three-flow source",
        "stack": "Stack: Python · httpx · BeautifulSoup · pandas · pytest · python-docx · MCP",
    },
}[lang]


@st.cache_data(show_spinner=False)
def _text(rel: str) -> str:
    with open(os.path.join(ASSETS, rel), "r", encoding="utf-8") as f:
        return f.read()


@st.cache_data(show_spinner=False)
def _bytes(rel: str) -> bytes:
    with open(os.path.join(ASSETS, rel), "rb") as f:
        return f.read()


@st.cache_data(show_spinner=False)
def _csv(rel: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(ASSETS, rel), encoding="utf-8-sig")


@st.cache_data(show_spinner=False)
def _json(rel: str) -> dict:
    return json.loads(_text(rel))


def _exists(rel: str) -> bool:
    return os.path.exists(os.path.join(ASSETS, rel))


def _download(label: str, rel: str, mime: str):
    if not _exists(rel):
        return
    st.download_button(
        label,
        data=_bytes(rel),
        file_name=os.path.basename(rel),
        mime=mime,
        key=rel,
        width="stretch",
    )


def _excerpt(text: str, limit: int = 1600) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit("\n", 1)[0] + "\n\n…"


st.title(T["title"])
st.caption(T["caption"])

st.subheader(T["auto_h"])
st.write(T["auto_d"])

c1, c2, c3 = st.columns(3)
c1.metric(T["flows_n"], "3")
c2.metric(T["models_n"], "4")
c3.metric(T["agents_n"], "1 + 3")

st.markdown(f"**{T['arch']}**")
render_mermaid(
    "flowchart LR\n"
    f'  U(["{T["task"]}"]) --> TR["{T["triage"]}"]\n'
    f'  TR --> CD["{T["coding"]}"]\n'
    f'  TR --> WS["{T["web"]}"]\n'
    f'  TR --> FS["{T["file"]}"]\n'
    f'  FS --> R(["{T["result"]}"])\n'
    f'  WS --> R\n'
    f'  CD --> R',
    height=420,
    font_size=12,
    max_width=760,
)

st.markdown(f"**{T['phase_models']}**")
phase_table = pd.DataFrame([
    {T["role"]: "triage", T["model"]: "qwen3-32b", T["phase"]: "task routing" if lang == "en" else "маршрутизация задачи"},
    {T["role"]: "planner", T["model"]: "qwen3-235b-a22b-2507", T["phase"]: "planning, bug analysis" if lang == "en" else "планирование, анализ багов"},
    {T["role"]: "coder", T["model"]: "glm-5.2", T["phase"]: "implementation, fixes, tests" if lang == "en" else "реализация, фиксы, тесты"},
    {T["role"]: "reporter", T["model"]: "glm-4.7-flash", T["phase"]: "reports, docs" if lang == "en" else "отчёты, документация"},
])
st.dataframe(phase_table, hide_index=True, width="stretch")
st.caption(T["models_note"])

st.divider()
st.subheader(T["ex_h"])

tab1, tab2, tab3 = st.tabs([T["ex1_t"], T["ex2_t"], T["ex3_t"]])

with tab1:
    st.write(T["ex1_goal"])
    st.write(T["ex1_flow"])
    st.write(T["ex1_value"])

    st.markdown(f"**{T['flow_h']}**")
    render_mermaid(
        "flowchart LR\n"
        f'  Q(["{T["task"]}"]) --> P["{T["planner"]}"]\n'
        f'  P --> W["{T["web"]}"]\n'
        f'  P --> F["{T["file"]}"]\n'
        f'  W --> C["{T["compiler"]}"]\n'
        f'  F --> C\n'
        f'  C --> O(["report.md / .docx"])',
        height=340,
        font_size=13,
        max_width=0,
    )

    st.markdown(f"**{T['result_h']}**")
    m1, m2, m3 = st.columns(3)
    m1.metric(T["subtasks"], "4")
    m2.metric(T["sources_n"], "8")
    m3.metric(T["local_web"], "2 / 6")

    with st.expander(T["report_h"], expanded=True):
        st.caption(T["sample_ru"])
        st.markdown(_excerpt(_text("research/report.md")))

    with st.expander(T["sources_h"], expanded=False):
        for s in _json("research/sources.json")["sources"]:
            line = f"- **[{s['id']}]** {s['title']}"
            if s.get("url"):
                line += f" — <{s['url']}>"
            st.markdown(line)

    st.markdown(f"**{T['artifacts_h']}**")
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        _download("report.md", "research/report.md", "text/markdown")
    with d2:
        _download("report.docx", "research/report.docx",
                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    with d3:
        _download("sources.json", "research/sources.json", "application/json")
    with d4:
        _download("sources.zip", "research/sources.zip", "application/zip")
    st.caption(T["src_case1"])

with tab2:
    st.write(T["ex2_goal"])
    st.write(T["ex2_flow"])
    st.write(T["ex2_value"])

    st.markdown(f"**{T['flow_h']}**")
    render_mermaid(
        "flowchart LR\n"
        f'  R(["{T["task"]}"]) --> B["Baseline pytest"]\n'
        f'  B --> P["{T["planner"]}"]\n'
        f'  P --> C["{T["coding"]}"]\n'
        f'  C --> T["pytest"]\n'
        f'  T -->|fail, max 3| C\n'
        f'  T -->|pass| RP["{T["reporter"]}"]\n'
        f'  RP --> O(["report + diff"])',
        height=340,
        font_size=13,
        max_width=0,
    )

    st.markdown(f"**{T['result_h']}**")
    m1, m2, m3 = st.columns(3)
    m1.metric(T["baseline"], "3 failed / 4 passed")
    m2.metric(T["after_fix"], "7 passed")
    m3.metric(T["files_changed"], "2")

    with st.expander(T["baseline_out"], expanded=False):
        st.code(_text("repo/baseline_pytest.txt").strip(), language="text")
    with st.expander(T["final_out"], expanded=True):
        st.code(_text("repo/final_pytest.txt").strip(), language="text")
    with st.expander(T["diff_h"], expanded=False):
        st.code(_text("repo/diff.patch").strip(), language="diff")

    st.markdown(f"**{T['artifacts_h']}**")
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        _download("report.md", "repo/report.md", "text/markdown")
    with d2:
        _download("run_info.json", "repo/run_info.json", "application/json")
    with d3:
        _download("diff.patch", "repo/diff.patch", "text/x-diff")
    with d4:
        _download("repo_fixed.zip", "repo/repo_fixed.zip", "application/zip")
    st.caption(T["src_case2"])

with tab3:
    st.write(T["ex3_goal"])
    st.write(T["ex3_flow"])
    st.write(T["ex3_value"])

    st.markdown(f"**{T['flow_h']}**")
    render_mermaid(
        "flowchart LR\n"
        f'  D(["{T["docs_n"]}"]) --> F["{T["file"]}"]\n'
        f'  F --> E["{T["extract"]}"]\n'
        f'  E --> V["{T["validate"]}"]\n'
        f'  V --> C(["CSV / summary"])\n'
        f'  V --> S["insert.sql"]\n'
        f'  S --> M["{T["mcp"]}"]',
        height=340,
        font_size=13,
        max_width=0,
    )

    st.markdown(f"**{T['result_h']}**")
    m1, m2, m3 = st.columns(3)
    m1.metric(T["docs_n"], "4")
    m2.metric(T["ok_check"], "2 / 2")
    m3.metric(T["valid_total"], "$2,959.60")

    with st.expander(T["invoices_h"], expanded=True):
        st.dataframe(_csv("docs/invoices.csv"), hide_index=True, width="stretch")
    with st.expander(T["items_h"], expanded=False):
        st.dataframe(_csv("docs/items.csv"), hide_index=True, width="stretch")

    st.markdown(f"**{T['rules_h']}**")
    st.markdown(
        f"- {T['rule_1']}\n- {T['rule_2']}\n- {T['rule_3']}\n"
        f"- {T['rule_4']}\n- {T['rule_5']}"
    )
    st.caption(T["check_note"])

    with st.expander(T["sql_h"], expanded=False):
        st.code(_text("docs/insert.sql").strip(), language="sql")

    st.markdown(f"**{T['artifacts_h']}**")
    d1, d2, d3 = st.columns(3)
    with d1:
        _download("summary.md", "docs/summary.md", "text/markdown")
        _download("invoices.csv", "docs/invoices.csv", "text/csv")
    with d2:
        _download("items.csv", "docs/items.csv", "text/csv")
        _download("extracted.json", "docs/extracted.json", "application/json")
    with d3:
        _download("insert.sql", "docs/insert.sql", "application/sql")
        _download("documents.zip", "docs/documents.zip", "application/zip")
    st.caption(T["src_case3"])

st.divider()
st.subheader(T["run_h"])
st.caption(T["run_note"])
st.code(
    "python cases/case1_research.py \"<question>\" --pages 8\n"
    "python cases/case2_repo.py\n"
    "python cases/case3_docs_to_data.py",
    language="powershell",
)

REPO_URL = "https://github.com/Aliyrd-01/AI"
l1, l2 = st.columns(2)
with l1:
    st.link_button(T["gh_repo"], REPO_URL, width="stretch")
with l2:
    st.link_button(T["gh_cases"], f"{REPO_URL}/tree/main/projects/autoagent/cases", width="stretch")

st.caption(T["stack"])
