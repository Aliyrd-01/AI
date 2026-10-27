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

st.set_page_config(page_title="N8N Automations", page_icon="🔗", layout="wide")

lang = lang_switcher()

T = {
    "ru": {
        "caption": "Три production-пайплайна: контент, продажи, поддержка. "
                   "Редактор наружу не публикуется — диаграмма воркфлоу + JSON + демо-запись.",
        "nodes": "Узлов",
        "conns": "Связей",
        "workflow": "Воркфлоу",
        "feeds": "Источники (RSS)",
        "diagram": "Диаграмма воркфлоу",
        "json": "Показать / скачать JSON",
        "download": "⬇️ Download workflow JSON",
        "demo": "Демо-запись",
        "foot": "Диаграмма строится из реального графа воркфлоу (JSON, экспортированный из n8n): "
                "узлы и связи — как в редакторе.  n8n-редактор и креды наружу не публикуются, "
                "секреты в JSON заменены плейсхолдерами.",
        "notfound": "Файл не найден: assets/n8n/{f}",
        "tech": "Технологии",
        "llm": "LLM",
    },
    "en": {
        "caption": "Three production pipelines: content, sales, support. "
                   "No n8n editor exposed — workflow diagram + JSON + demo recording.",
        "nodes": "Nodes",
        "conns": "Connections",
        "workflow": "Workflow",
        "feeds": "Feeds (RSS)",
        "diagram": "Workflow diagram",
        "json": "Show / download JSON",
        "download": "⬇️ Download workflow JSON",
        "demo": "Demo recording",
        "foot": "The diagram is generated from the real workflow graph (JSON exported from n8n): "
                "nodes and edges as in the editor. The n8n editor and credentials are never "
                "exposed; secrets in the JSON are replaced with placeholders.",
        "notfound": "File not found: assets/n8n/{f}",
        "tech": "Tech",
        "llm": "LLM",
    },
}[lang]

FLOWS = [
    {
        "key": "news_content_publisher",
        "file": "news_content_publisher.json",
        "title": "Automated AI Content Publisher",
        "short": {"ru": "Автономная новостная редакция", "en": "Autonomous news desk"},
        "desc": {
            "ru": "7 RSS-лент (Forklog, Habr, Habr AI, TechCrunch AI, MIT Tech Review, "
                  "Decoder, DailyAI)\n\n"
                  "→ единый дедуп: ссылки в пачке + история публикаций "
                  "(similarity по заголовкам, реестр в staticData)\n\n"
                  "→ очистка текста и извлечение "
                  "обложки (enclosure / media:content / og:image, при промахе — SERP fallback)\n\n"
                  "→ детектор темы (crypto / AI) и предфильтр по интересам\n\n"
                  "→ LLM переводит и сжимает "
                  "материал в строгий JSON (важность, релевантность, заголовок, 3–4 предложения, "
                  "вывод, теги; temperature 0.2 для стабильного JSON)\n\n"
                  "→ форматирование поста (HTML)\n\n"
                  "→ порог релевантности (relevance_score от LLM)\n\n"
                  "→ публикация в Telegram "
                  "(фото или текст); стоимость LLM-шага (usage → $) пишется в llm_usage. "
                  "Человека в цикле нет.",
            "en": "7 RSS feeds (Forklog, Habr, Habr AI, TechCrunch AI, MIT Tech Review, "
                  "Decoder, DailyAI)\n\n"
                  "→ unified dedup: in-batch links + publication history "
                  "(title similarity, registry in staticData)\n\n"
                  "→ text cleaning and cover extraction "
                  "(enclosure / media:content / og:image, SERP fallback on miss)\n\n"
                  "→ topic detector "
                  "(crypto / AI) and interest pre-filter\n\n"
                  "→ an LLM translates and condenses the piece "
                  "into strict JSON (importance, relevance, title, 3–4 sentences, takeaway, tags; "
                  "temperature 0.2 for stable JSON)\n\n"
                  "→ post formatting (HTML)\n\n"
                  "→ relevance gate "
                  "(relevance_score from the LLM)\n\n"
                  "→ publish to Telegram (photo or text post); the "
                  "LLM step's cost (usage → $) is logged to llm_usage. No human in the loop.",
        },
        "tech_base": "n8n · 7 × RSS · Code (JS) · Qubax · og:image + SerpAPI fallback · cost tracking · Telegram",
        "video": {"ru": "news_demo.mp4", "en": "news_demo_en.mp4"},
        "images": [],
        "diagram_h": 170,
    },
    {
        "key": "lead_qualification",
        "file": "lead_qualification.json",
        "title": "Lead Qualification & Scoring",
        "short": {"ru": "B2B-квалификация лидов с A/B-тестом промптов",
                  "en": "B2B lead qualification with A/B prompt testing"},
        "desc": {
            "ru": "Лид приходит с веб-формы (webhook, Basic Auth)\n\n"
                  "→ валидация email/телефона\n\n"
                  "→ обогащение "
                  "из Postgres-CRM нативной нодой (контакт/компания, параметризованный SQL $1..$9)\n\n"
                  "→ A/B два промпта скорринга "
                  "(conservative vs aggressive)\n\n"
                  "→ JSON-score (0–100, tier, next action)\n\n"
                  "→ ветка «hot > 70»\n\n"
                  "→ Telegram-алерт + upsert лида в CRM (нативная Postgres-нода, "
                  "INSERT … ON CONFLICT, параметры $1..$16)\n\n"
                  "→ стоимость скоринга (usage → $ через "
                  "прайс-таблицу) в llm_usage\n\n"
                   "→ в ответ вебхука идёт "
                   "сводка A/B (n и средний скор каждой руки, текущий победитель) и cost_usd.",
            "en": "A lead arrives from a web form (webhook, Basic Auth)\n\n"
                  "→ email/phone validation\n\n"
                  "→ enrichment "
                  "via native Postgres nodes against the CRM (contact/company, parameterized $1..$9 SQL)\n\n"
                  "→ A/B testing of two scoring "
                  "prompts (conservative vs aggressive)\n\n"
                  "→ JSON score (0–100, tier, next action)\n\n"
                  "→ hot > 70 branch\n\n"
                  "→ Telegram alert + lead upsert into the CRM (native Postgres node, "
                  "INSERT … ON CONFLICT, $1..$16 params)\n\n"
                  "→ scoring cost (usage → $ via a pricing "
                  "table) logged to llm_usage\n\n"
                  "→ the webhook response "
                   "returns the A/B summary (n and avg score per arm, current winner) plus cost_usd.",
        },
        "tech_base": "n8n · Webhook (Basic Auth) · Postgres CRM (native nodes, params) · A/B prompt testing · cost tracking · Telegram",
        "video": {"ru": "leadqual_demo.mp4", "en": "leadqual_demo_en.mp4"},
        "images": [],
        "diagram_h": 210,
    },
    {
        "key": "ai_support_escalation",
        "file": "ai_support_escalation.json",
        "title": "AI Support & Escalation",
        "short": {"ru": "Интеллектуальная техподдержка с передачей оператору",
                  "en": "Smart support desk with human handoff"},
        "desc": {
            "ru": "Telegram-триггер\n\n"
                  "→ сообщение и состояние пользователя пишутся в Postgres "
                  "(user_states)\n\n"
                  "→ в режиме оператора диалог сразу пересылается оператору\n\n"
                  "→ нативный Text Classifier (AI-нода n8n + Qubax Chat Model) решает simple / operator, "
                  "с fallback «other»\n\n"
                  "→ простые вопросы закрывает "
                  "локальный RAG-сервис (FastAPI + Qdrant), сложные (оплаты, жалобы, недовольный "
                  "клиент) переводят пользователя в режим оператора; оператору уходит алерт "
                  "с ID пользователя и текстом вопроса, а ответ доставляется обычным Reply "
                  "на алерт; есть закрытие диалога и сброс в режим бота.",
            "en": "Telegram trigger\n\n"
                  "→ the message and the user state are written to Postgres "
                  "(user_states)\n\n"
                  "→ in operator mode the dialog is forwarded straight to the human\n\n"
                  "→ a native Text Classifier node (n8n AI node + Qubax Chat Model) decides simple / "
                  "operator with an 'other' fallback\n\n"
                  "→ simple questions are answered by a "
                  "local RAG service (FastAPI + Qdrant), complex ones (payments, complaints, angry "
                  "customer) switch the user to operator mode; the operator gets an alert with "
                  "the user ID and the question text, and a plain Reply to the alert "
                  "delivers the answer; dialog close and reset-to-bot are supported.",
        },
        "tech_base": "n8n · Telegram API · Postgres (user_states) · AI nodes (Text Classifier) · RAG (FastAPI + Qdrant) · human handoff",
        "video": {"ru": "support_demo.mp4", "en": "support_demo_en.mp4"},
        "images": [],
        "diagram_h": 310,
    },
]

# Провайдеры, которые ищем в JSON воркфлоу: (подстрока в ноде, человекочитаемая метка)
PROVIDERS = [
    ("api.qubax.ai", "Qubax"),
    ("openrouter.ai", "OpenRouter"),
    ("opencode.ai", "OpenCode Zen"),
    ("generativelanguage.googleapis.com", "Google Gemini"),
    ("127.0.0.1:8000", "local RAG (FastAPI)"),
    ("127.0.0.1:9001", "MCP MySQL"),
    ("127.0.0.1:9002", "MCP Postgres"),
]


def detect_llm_stack(wf: dict):
    """Какие провайдеры реально используются — по содержимому нод (а не по хардкоду на странице)."""
    found = []
    for n in wf.get("nodes", []):
        blob = json.dumps(n, ensure_ascii=False)
        for needle, label in PROVIDERS:
            if needle in blob and label not in found:
                found.append(label)
    return found


def _short(name: str, limit: int = 20) -> str:
    """Компактная подпись ноды: убираем служебные хвосты и обрезаем."""
    s = str(name).strip()
    if " (Postgres)" in s:
        s = s.replace(" (Postgres)", " (PG)")
    for junk in (" (prep)", " (CRM)", " account", " Trigger"):
        s = s.replace(junk, "")
    s = s.replace(" (Text fallback)", " (Text FB)")
    s = s.replace("/", "/ ").strip()
    return s if len(s) <= limit else s[: limit - 1].rstrip(" -→") + "…"


def to_mermaid(wf: dict) -> str:
    """Реальный граф воркфлоу: ветки сохраняются, линейные цепочки схлопываются в один узел
    (label — «шаг → шаг → шаг»), RSS-триггеры — один узел. LR + короткие подписи, чтобы влезало целиком."""
    from collections import Counter, defaultdict

    nodes = wf.get("nodes", [])
    conns = wf.get("connections", {}) or {}
    types = {n.get("name"): n.get("type", "") for n in nodes}
    alias, name_of = {}, {}
    rss = [n for n in nodes if "rssFeedReadTrigger" in n.get("type", "")]
    for i, n in enumerate(nodes):
        name = n.get("name", f"node{i}")
        if rss and "rssFeedReadTrigger" in n.get("type", ""):
            alias[name] = "rss"
            name_of["rss"] = f"RSS × {len(rss)}"
            continue
        nid = f"n{i}"
        alias[name] = nid
        name_of[nid] = _short(name)

    edges, seen = [], set()
    for src, outs in conns.items():
        if src not in alias:
            continue
        for bi, branch in enumerate(outs.get("main", []) or []):
            for tgt in (branch or []):
                t = tgt.get("node") if isinstance(tgt, dict) else None
                if t not in alias:
                    continue
                lbl = "true" if ("n8n-nodes-base.if" in types.get(src, "") and bi == 0) else (
                    "false" if "n8n-nodes-base.if" in types.get(src, "") else "")
                key = (alias[src], alias[t], lbl)
                if key not in seen:
                    seen.add(key)
                    edges.append(key)
    if not edges:
        return "flowchart LR\n  empty[\"no connections\"]"

    succ = defaultdict(list)
    pred = Counter()
    for a, b, l in edges:
        succ[a].append((b, l))
        pred[b] += 1
    branch_ids = {alias[n.get("name")] for n in nodes if "n8n-nodes-base.if" in n.get("type", "")}

    ids = list(name_of)
    ids.sort(key=lambda i: (pred[i] != 0, int(i[1:]) if i[1:].isdigit() else -1))  # источники раньше
    seg_of, segments, used = {}, [], set()
    for start in ids:
        if start in used:
            continue
        chain, cur = [start], start
        used.add(start)
        while True:
            outs = succ[cur]
            if len(outs) != 1:
                break
            nxt, lbl = outs[0]
            if lbl or pred[nxt] != 1 or nxt in branch_ids or nxt in used:
                break
            chain.append(nxt)
            used.add(nxt)
            cur = nxt
        for i in chain:
            seg_of[i] = start
        segments.append(chain)

    lines = ["flowchart LR"]
    for seg in segments:
        names = [name_of[i] for i in seg]
        chunks = [" → ".join(names[k:k + 3]) for k in range(0, len(names), 3)]
        label = "<br/>".join(chunks).replace(chr(34), chr(39))
        lines.append(f'  {seg[0]}["{label}"]')
    for a, b, l in edges:
        if seg_of[a] == seg_of[b]:
            continue
        arrow = f"-->|{l}|" if l else "-->"
        lines.append(f"  {seg_of[a]} {arrow} {seg_of[b]}")
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

if not wf:
    st.warning(T["notfound"].format(f=meta["file"]))
else:
    llm_stack = detect_llm_stack(wf)
    tech = meta["tech_base"] + (f" · {T['llm']}: " + ", ".join(llm_stack) if llm_stack else "")
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    st.caption(f"**{T['tech']}:** {tech}")

    n_nodes = len(wf.get("nodes", []))
    n_conns = sum(
        len([t for b in outs.get("main", []) or [] for t in (b or [])])
        for outs in (wf.get("connections", {}) or {}).values()
    )
    c1, c2 = st.columns(2)
    c1.metric(T["nodes"], n_nodes)
    c2.metric(T["conns"], n_conns)
    st.caption(f"{T['workflow']}: **{wf.get('name', '—')}**")

    feeds = [n.get("name") for n in wf.get("nodes", []) if "rssFeedReadTrigger" in n.get("type", "")]
    if feeds:
        st.caption(f"{T['feeds']}: " + ", ".join(str(x) for x in feeds))

    vfiles = meta.get("video") or {}
    for cand in (vfiles.get(lang), vfiles.get("ru")):
        vpath = os.path.join(ASSETS, cand) if cand else None
        if vpath and os.path.exists(vpath):
            st.markdown(f"**{T['demo']}**")
            st.video(vpath)
            break

    st.markdown(f"**{T['diagram']}**")
    render_mermaid(to_mermaid(wf), height=meta.get("diagram_h", 420), font_size=16)

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
