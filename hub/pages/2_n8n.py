"""n8n automation workflows — visual showcase (RU/EN)."""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, ".."))
ASSETS = os.path.join(HUB, "assets", "n8n")
sys.path.insert(0, HUB)

import streamlit as st
from diagrams import render_mermaid
from i18n import lang_switcher

st.set_page_config(page_title="n8n Automations", page_icon="🔗", layout="wide")

lang = lang_switcher()

T = {
    "ru": {
        "caption": "Три production-пайплайна: контент, продажи, поддержка. "
                   "Редактор наружу не публикуется — диаграмма воркфлоу + JSON + демо-запись.",
        "nodes": "Nodes",
        "conns": "Connections",
        "diagram": "Диаграмма воркфлоу",
        "json": "Показать / скачать JSON",
        "download": "⬇️ Download workflow JSON",
        "demo": "Демо-запись",
        "foot": "Диаграммы генерируются из экспортированных JSON во время запуска. "
                "Живой n8n-редактор и креды наружу не публикуются.",
        "notfound": "Файл не найден: assets/n8n/{f}",
        "tech": "Технологии",
    },
    "en": {
        "caption": "Three production pipelines: content, sales, support. "
                   "No live editor exposed — workflow diagram + JSON + demo recording.",
        "nodes": "Nodes",
        "conns": "Connections",
        "diagram": "Workflow diagram",
        "json": "Show / download JSON",
        "download": "⬇️ Download workflow JSON",
        "demo": "Demo recording",
        "foot": "Diagrams are generated from the exported JSON at runtime. "
                "The live n8n editor and credentials are never exposed.",
        "notfound": "File not found: assets/n8n/{f}",
        "tech": "Tech",
    },
}[lang]

FLOWS = [
    {
        "key": "news_content_publisher",
        "file": "news_content_publisher.json",
        "title": "Automated AI Content Publisher",
        "short": {"ru": "Автономная новостная редакция", "en": "Autonomous news desk"},
        "desc": {
            "ru": "Собирает свежие статьи из десятков RSS (Forklog, Habr, …), извлекает полный "
                  "текст и обложку (og:image), затем LLM переводит, сокращает и стилизует материал "
                  "и автоматически публикует готовый пост в Telegram-канал — без участия человека.",
            "en": "Pulls fresh articles from dozens of RSS feeds (Forklog, Habr, …), extracts the "
                  "full text and og:image cover, then an LLM translates, condenses and styles the "
                  "piece and automatically publishes the finished post to a Telegram channel — "
                  "with no human in the loop.",
        },
        "tech": "n8n · RSS/HTTP · HTML Parsing · LLM (OpenRouter) · Telegram",
        "video": "news_demo.mp4",
        "images": [],
    },
    {
        "key": "lead_qualification",
        "file": "lead_qualification.json",
        "title": "Lead Qualification & Scoring",
        "short": {"ru": "B2B-квалификация лидов с A/B-тестом промптов",
                  "en": "B2B lead qualification with A/B prompt testing"},
        "desc": {
            "ru": "Лид приходит с веб-формы (webhook) → валидация email/телефона → обогащение через "
                  "MCP-сервер (Postgres CRM: контакт/компания) → A/B два промпта скорринга "
                  "(conservative vs aggressive) → JSON-score (0–100, tier, next action) → "
                  "ветка «hot > 70» → Telegram-алерт + upsert лида в CRM.",
            "en": "A lead arrives from a web form (webhook) → email/phone validation → enrichment "
                  "via an MCP server (Postgres CRM: contact/company) → A/B testing of two scoring "
                  "prompts (conservative vs aggressive) → JSON score (0–100, tier, next action) → "
                  "hot > 70 branch → Telegram alert + lead upsert into the CRM.",
        },
        "tech": "n8n · Webhook · MCP (Postgres CRM) · A/B prompt testing · OpenRouter · Telegram",
        "video": "leadqual_demo.mp4",
        "images": [],
    },
    {
        "key": "ai_support_escalation",
        "file": "ai_support_escalation.json",
        "title": "AI Support & Escalation",
        "short": {"ru": "Интеллектуальная техподдержка с передачей оператору",
                  "en": "Smart support desk with human handoff"},
        "desc": {
            "ru": "Принимает сообщения в Telegram, LLM-классификатором определяет тип обращения. "
                  "Типовые вопросы закрывает AI-агент с сохранением контекста диалога; сложные "
                  "тикеты (оплаты, жалобы) маршрутизирует на живого оператора с полной историей.",
            "en": "Accepts Telegram messages and classifies each one with an LLM. Common questions "
                  "are answered by an AI agent that keeps conversation context; complex tickets "
                  "(payments, complaints) are routed to a human operator with the full history.",
        },
        "tech": "n8n · Telegram API · LLM classification · dialog memory · human handoff",
        "video": "support_demo.mp4",
        "images": [],
    },
]


def to_mermaid(wf: dict) -> str:
    nodes = wf.get("nodes", [])
    conns = wf.get("connections", {})
    ids, lines = {}, ["flowchart TD"]
    for i, n in enumerate(nodes):
        nid = f"n{i}"
        ids[n.get("name", f"node{i}")] = nid
        label = str(n.get("name", f"node{i}")).replace('"', "'")
        lines.append(f'  {nid}["{label}"]')
    for src, outs in conns.items():
        if src not in ids:
            continue
        for branch in outs.get("main", []) or []:
            for tgt in (branch or []):
                t = tgt.get("node") if isinstance(tgt, dict) else None
                if t in ids:
                    lines.append(f"  {ids[src]} --> {ids[t]}")
    return "\n".join(lines)


def load_flow(fname: str):
    path = os.path.join(ASSETS, fname)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


st.title("🔗 n8n Automation Workflows")
st.caption(T["caption"])

# Select active workflow
selected_flow = st.radio(
    "Workflow",
    options=[f["title"] for f in FLOWS],
    horizontal=True,
    label_visibility="collapsed"
)

meta = next(f for f in FLOWS if f["title"] == selected_flow)
wf = load_flow(meta["file"])

st.subheader(meta["short"][lang])
st.write(meta["desc"][lang])
st.caption(f"**{T['tech']}:** {meta['tech']}")

if not wf:
    st.warning(T["notfound"].format(f=meta["file"]))
else:
    n_nodes = len(wf.get("nodes", []))
    n_conns = sum(
        len([t for b in outs.get("main", []) or [] for t in (b or [])])
        for outs in (wf.get("connections", {}) or {}).values()
    )
    c1, c2, c3 = st.columns(3)
    c1.metric(T["nodes"], n_nodes)
    c2.metric(T["conns"], n_conns)
    c3.metric("Workflow", wf.get("name", "—"))

    if meta.get("video"):
        vpath = os.path.join(ASSETS, meta["video"])
        if os.path.exists(vpath):
            st.markdown(f"**{T['demo']}**")
            st.video(vpath)

    if meta.get("key") == "ai_support_escalation":
        hd_canvas = os.path.join(ASSETS, "support_canvas_hd.png")
        if os.path.exists(hd_canvas):
            st.markdown("**Полотно воркфлоу в n8n**" if lang == "ru" else "**n8n Workflow Canvas**")
            st.image(hd_canvas, use_container_width=True)

    st.markdown(f"**{T['diagram']}**")
    render_mermaid(to_mermaid(wf), height=460)

    for img in meta.get("images", []):
        ipath = os.path.join(ASSETS, img)
        if os.path.exists(ipath):
            st.image(ipath, caption=img)

    with st.expander(T["json"]):
        st.download_button(
            T["download"],
            data=json.dumps(wf, ensure_ascii=False, indent=2),
            file_name=meta["file"],
            mime="application/json",
            key=f"dl_{meta['key']}_{lang}",
        )
        st.json(wf, expanded=False)

st.divider()
st.caption(T["foot"])
