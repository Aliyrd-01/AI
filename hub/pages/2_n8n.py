"""n8n automation workflows — visual showcase.

Shows three production workflows: diagrams generated from the exported JSON,
demo videos/screenshots, and downloadable workflow files. No live n8n editor
is exposed.
"""

import html
import json
import os

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="n8n Automations", page_icon="🔗", layout="wide")

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.abspath(os.path.join(HERE, "..", "assets", "n8n"))

st.title("🔗 n8n Automation Workflows")
st.caption("Три production-пайплайна: контент, продажи, поддержка. "
           "Редактор наружу не публикуется — диаграмма воркфлоу + JSON + демо-запись.")

FLOWS = [
    {
        "key": "news_content_publisher",
        "file": "news_content_publisher.json",
        "title": "Automated AI Content Publisher",
        "short": "Автономная новостная редакция",
        "ru": "Собирает свежие статьи из десятков RSS (Forklog, Habr, …), извлекает полный "
              "текст и обложку (og:image), затем LLM переводит, сокращает и стилизует материал "
              "и автоматически публикует готовый пост в Telegram-канал — без участия человека.",
        "tech": "n8n · RSS/HTTP · HTML Parsing · LLM (OpenRouter) · Telegram",
        "video": "news_demo.mp4",
        "images": [],
    },
    {
        "key": "lead_qualification",
        "file": "lead_qualification.json",
        "title": "Lead Qualification & Scoring",
        "short": "B2B-квалификация лидов с A/B-тестом промптов",
        "ru": "Лид приходит с веб-формы (webhook) → валидация email/телефона → обогащение через "
              "MCP-сервер (Postgres CRM: контакт/компания) → A/B два промпта скорринга "
              "(conservative vs aggressive) → JSON-score (0–100, tier, next action) → "
              "ветка «hot > 70» → Telegram-алерт + upsert лида в CRM.",
        "tech": "n8n · Webhook · MCP (Postgres CRM) · A/B prompt testing · OpenRouter · Telegram",
        "video": "leadqual_demo.mp4",
        "images": ["n8n_workflow.png"],
    },
    {
        "key": "ai_support_escalation",
        "file": "ai_support_escalation.json",
        "title": "AI Support & Escalation",
        "short": "Интеллектуальная техподдержка с передачей оператору",
        "ru": "Принимает сообщения в Telegram, LLM-классификатором определяет тип обращения. "
              "Типовые вопросы закрывает AI-агент с сохранением контекста диалога; сложные "
              "тикеты (оплаты, жалобы) маршрутизирует на живого оператора с полной историей.",
        "tech": "n8n · Telegram API · LLM classification · dialog memory · human handoff",
        "video": None,
        "images": ["n8n_debug.png"],
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


def render_mermaid(code: str, height: int = 560):
    components.html(
        f"""
        <div class="mermaid">{html.escape(code)}</div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{ startOnLoad: true, theme: "base",
            themeVariables: {{ fontSize: "13px" }} }});</script>
        """,
        height=height,
        scrolling=True,
    )


def load_flow(fname: str):
    path = os.path.join(ASSETS, fname)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


tabs = st.tabs([f["title"] for f in FLOWS])

for tab, meta in zip(tabs, FLOWS):
    with tab:
        wf = load_flow(meta["file"])
        st.subheader(meta["short"])
        st.write(meta["ru"])
        st.caption(f"**Технологии:** {meta['tech']}")

        if not wf:
            st.warning(f"Файл не найден: assets/n8n/{meta['file']}")
            continue

        n_nodes = len(wf.get("nodes", []))
        n_conns = sum(
            len([t for b in outs.get("main", []) or [] for t in (b or [])])
            for outs in (wf.get("connections", {}) or {}).values()
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Nodes", n_nodes)
        c2.metric("Connections", n_conns)
        c3.metric("Workflow", wf.get("name", "—"))

        if meta.get("video"):
            vpath = os.path.join(ASSETS, meta["video"])
            if os.path.exists(vpath):
                st.markdown("**Демо-запись**")
                st.video(vpath)

        with st.expander("Диаграмма воркфлоу", expanded=not meta.get("video")):
            render_mermaid(to_mermaid(wf), height=560)

        for img in meta.get("images", []):
            ipath = os.path.join(ASSETS, img)
            if os.path.exists(ipath):
                st.image(ipath, caption=img)

        with st.expander("Показать / скачать JSON"):
            st.download_button(
                "⬇️ Download workflow JSON",
                data=json.dumps(wf, ensure_ascii=False, indent=2),
                file_name=meta["file"],
                mime="application/json",
                key=f"dl_{meta['key']}",
            )
            st.json({k: wf.get(k) for k in ("name", "active", "settings")}, expanded=False)

st.divider()
st.caption("Диаграммы генерируются из экспортированных JSON во время запуска. "
           "Живой n8n-редактор и креды наружу не публикуются.")
