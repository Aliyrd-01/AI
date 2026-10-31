"""Contacts — one place for the call to action. (RU/EN)"""

import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

import streamlit as st
from i18n import lang_switcher

st.set_page_config(page_title="Contacts", page_icon="✉️", layout="wide")

lang = lang_switcher()

EMAIL = "aliyrd.com@gmail.com"
TELEGRAM = "https://t.me/pranson01"
TELEGRAM_HANDLE = "@pranson01"

T = {
    "ru": {
        "title": "✉️ Контакты",
        "caption": "Пилот агента, RAG-система, аудит качества или автоматизация на n8n — "
                   "напишите, обсудим задачу и сроки.",
        "write_h": "**Написать**",
        "email_l": "Почта — для задач и документов",
        "tg_l": "Telegram — быстрый вопрос",
        "reply": "Отвечаем в течение рабочего дня (Пн–Пт).",
        "help_h": "**С чем помогаем**",
        "help": [
            ("🔎 RAG-системы", "Поиск по вашим документам: гибридный retrieval, реранкинг, цитаты, "
                                "честные отказы, метрики качества."),
            ("🧭 Unified Agent", "Агент с инструментами: база знаний + CRM, read-only SQL, guardrails, "
                                 "трейс каждого шага."),
            ("🔗 n8n-автоматизации", "Контент-пайплайны, квалификация лидов, поддержка с эскалацией — "
                                     "от идеи до продакшена."),
            ("🧪 Аудит качества", "Прогон существующего RAG или агента по методике: baseline, "
                                  "узкие места, план правок."),
        ],
        "send_h": "**Что написать в первом сообщении**",
        "send": [
            "Задачу в одном абзаце: что должно происходить и для кого.",
            "Что уже есть: стек, данные, объём, текущий процесс.",
            "Желаемый срок и формат: пилот, прод, аудит.",
            "Как удобнее связаться и в каком часовом поясе вы работаете.",
        ],
        "steps_h": "**Как проходит старт**",
        "s1_t": "1 · Знакомство",
        "s1_d": "30 минут: разбираем задачу, данные и ограничения. Без презентаций.",
        "s2_t": "2 · План и оценка",
        "s2_d": "Сценарий пилота, объём работ, сроки и стоимость — в одном документе.",
        "s3_t": "3 · Пилот",
        "s3_d": "Работающий прототип на ваших данных + метрики и решение о продолжении.",
        "note": "Не отправляйте пароли, ключи и персональные данные в первом сообщении — "
                "для доступов используем защищённый канал.",
        "more_h": "**Полезно перед разговором**",
        "more": [
            ("views/7_Unified_Agent.py", "🧭 Unified Agent — демо и guardrails"),
            ("views/1_RAG.py", "🔎 RAG-система — retrieval и цитаты"),
            ("views/92_Testing.py", "🧪 Тестирование RAG и агентов"),
            ("views/2_N8N.py", "🔗 n8n-пайплайны"),
        ],
    },
    "en": {
        "title": "✉️ Contacts",
        "caption": "Agent pilot, RAG system, quality audit or n8n automation — write to us and we "
                   "will discuss the task and the timeline.",
        "write_h": "**Get in touch**",
        "email_l": "E-mail — for tasks and documents",
        "tg_l": "Telegram — for a quick question",
        "reply": "We reply within one business day (Mon–Fri).",
        "help_h": "**What we help with**",
        "help": [
            ("🔎 RAG systems", "Search over your documents: hybrid retrieval, reranking, citations, "
                               "honest refusals, quality metrics."),
            ("🧭 Unified Agent", "A tool-calling agent: knowledge base + CRM, read-only SQL, "
                                 "guardrails, a trace for every step."),
            ("🔗 n8n automations", "Content pipelines, lead qualification, support with escalation — "
                                   "from idea to production."),
            ("🧪 Quality audit", "We run your existing RAG or agent through our method: baseline, "
                                 "bottlenecks, a fix plan."),
        ],
        "send_h": "**What to include in your first message**",
        "send": [
            "The task in one paragraph: what should happen and for whom.",
            "What you already have: stack, data, volume, current process.",
            "The timeline and format you want: pilot, production, audit.",
            "How to reach you and your time zone.",
        ],
        "steps_h": "**How a project starts**",
        "s1_t": "1 · Intro call",
        "s1_d": "30 minutes: we go through the task, the data and the constraints. No slideware.",
        "s2_t": "2 · Plan and estimate",
        "s2_d": "Pilot scope, effort, timeline and price in a single document.",
        "s3_t": "3 · Pilot",
        "s3_d": "A working prototype on your data plus metrics and a go/no-go decision.",
        "note": "Do not send passwords, keys or personal data in the first message — "
                "we use a secure channel for access.",
        "more_h": "**Useful before we talk**",
        "more": [
            ("views/7_Unified_Agent.py", "🧭 Unified Agent — demo and guardrails"),
            ("views/1_RAG.py", "🔎 RAG system — retrieval and citations"),
            ("views/92_Testing.py", "🧪 RAG & Agent testing"),
            ("views/2_N8N.py", "🔗 n8n pipelines"),
        ],
    },
}[lang]

st.title(T["title"])
st.caption(T["caption"])


def gap(px: int = 12) -> None:
    st.markdown(f"<div style='height:{px}px'></div>", unsafe_allow_html=True)


gap()
with st.container(border=True):
    st.markdown(T["write_h"])
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.caption(T["email_l"])
        st.link_button(f"✉️ {EMAIL}", f"mailto:{EMAIL}", use_container_width=True)
    with c2:
        st.caption(T["tg_l"])
        st.link_button(f"✈️ {TELEGRAM_HANDLE}", TELEGRAM, use_container_width=True)
    st.caption(T["reply"])

gap()
st.markdown(T["help_h"])
for col, (title, desc) in zip(st.columns(4), T["help"]):
    with col:
        st.markdown(f"**{title}**")
        st.caption(desc)

gap()
st.markdown(T["send_h"])
for line in T["send"]:
    st.markdown(f"- {line}")

gap()
st.markdown(T["steps_h"])
for col, (t, d) in zip(st.columns(3), [
    (T["s1_t"], T["s1_d"]), (T["s2_t"], T["s2_d"]), (T["s3_t"], T["s3_d"]),
]):
    with col:
        with st.container(border=True):
            st.markdown(f"**{t}**")
            st.write(d)

gap()
st.info(T["note"])

gap()
st.markdown(T["more_h"])
for page, label in T["more"]:
    st.page_link(page, label=label)
