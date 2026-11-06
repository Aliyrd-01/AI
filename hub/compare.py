"""Shared comparison block: Agents (multi-agent framework) vs Unified Agent (single tool-calling)."""

import streamlit as st

T = {
    "ru": {
        "h": "**Чем Agents отличается от Unified Agent**",
        "short": "Коротко: **Agents** — «сделай работу за меня» (многошагово, офлайн-кейсы). "
                 "**Unified Agent** — «ответь на вопрос по моим данным» (диалог, онлайн).",
        "cols": ("", "🤖 Agents", "🧭 Unified Agent"),
        "rows": [
            ("Что это",
             "Мультиагентный фреймворк AutoAgent: агент-диспетчер + специализированные агенты "
             "(файлы, веб, код)",
             "Один агент с инструментами: база знаний и CRM"),
            ("Как работает",
             "Дробит задачу на подзадачи, раздаёт роли, собирает артефакты; модели подбираются по фазам",
             "Сам выбирает инструмент под вопрос: поиск по документам или SQL в CRM"),
            ("Что на выходе",
             "Отчёт с источниками, исправленный код + тесты, таблица + SQL — готовые артефакты прогонов",
             "Ответ в чате с пометками [KB]/[DB], трейс вызовов, токены и стоимость"),
            ("Как посмотреть",
             "Офлайн-кейсы: артефакты в репозитории, запуск из CLI",
             "Интерактивное демо на сайте: спросите что угодно"),
            ("Когда выбирать",
             "Нужен автономный исполнитель сложной многошаговой задачи",
             "Нужны ответы по вашим документам и данным CRM в диалоге"),
        ],
        "to_agents": "Перейти в Agents →",
        "to_ua": "Перейти в Unified Agent →",
    },
    "en": {
        "h": "**How Agents differs from Unified Agent**",
        "short": "In short: **Agents** is \"do the work for me\" (multi-step, offline cases). "
                 "**Unified Agent** is \"answer a question from my data\" (dialog, online).",
        "cols": ("", "🤖 Agents", "🧭 Unified Agent"),
        "rows": [
            ("What it is",
             "Multi-agent AutoAgent framework: a dispatcher agent plus specialised agents "
             "(files, web, code)",
             "A single agent with tools: knowledge base and CRM"),
            ("How it works",
             "Splits the task into subtasks, assigns roles, collects artefacts; models are picked per phase",
             "Picks the tool for the question itself: document search or SQL against the CRM"),
            ("What you get",
             "A report with sources, fixed code plus tests, a table plus SQL — ready run artefacts",
             "A chat answer tagged [KB]/[DB], a call trace, tokens and cost"),
            ("How to look",
             "Offline cases: artefacts in the repository, run from the CLI",
             "An interactive demo on this site: just ask"),
            ("When to choose",
             "You need an autonomous executor for a complex multi-step task",
             "You need answers over your documents and CRM data in a dialog"),
        ],
        "to_agents": "Go to Agents →",
        "to_ua": "Go to Unified Agent →",
    },
}


def agents_vs_unified(lang: str, current: str) -> None:
    """Render the comparison table; `current` is "agents" or "unified"."""
    t = T[lang]
    with st.container(border=True):
        st.markdown(t["h"])
        st.caption(t["short"])
        head = "| " + " | ".join(t["cols"]) + " |\n|" + "|".join(["---"] * 3) + "|\n"
        body = "".join(f"| **{r[0]}** | {r[1]} | {r[2]} |\n" for r in t["rows"])
        st.markdown(head + body)
        if current == "agents":
            st.page_link("views/7_Unified_Agent.py", label=t["to_ua"], icon="🧭")
        else:
            st.page_link("views/3_Agents.py", label=t["to_agents"], icon="🤖")
