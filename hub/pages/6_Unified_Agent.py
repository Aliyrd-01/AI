"""Unified Agent — one agent that routes between RAG and the CRM database (MCP)."""

import html
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "rag")))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "agents")))

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Unified Agent", page_icon="🧭", layout="wide")


def render_mermaid(code: str, height: int = 360):
    components.html(
        f"""
        <div class="mermaid">{html.escape(code)}</div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{ startOnLoad: true, theme: "base" }});</script>
        """,
        height=height,
        scrolling=True,
    )


st.title("🧭 Unified Agent")
st.caption("Один агент с инструментами: сам решает — искать в базе знаний (RAG) "
           "или запросить CRM (PostgreSQL через MCP).")

with st.expander("Как это работает", expanded=True):
    render_mermaid(
        "flowchart TD\n"
        '  U["Question"] --> A["Unified Agent (Qubax, tool-calling)"]\n'
        '  A -->|tool| R["search_knowledge_base · Qdrant hybrid"]\n'
        '  A -->|tool| D["query_database · MCP → PostgreSQL"]\n'
        '  R --> A\n'
        '  D --> A\n'
        '  A --> Ans["Answer with [KB] / [DB]"]'
    )
    st.caption("Агент вызывает нужные инструменты (может несколько), затем отвечает "
               "с пометками [KB] (база знаний) и [DB] (CRM).")

EXAMPLES = [
    "What color is amber urine?",
    "How many leads are in the CRM and what's the hottest one?",
    "Summarize what the knowledge base says about dark amber urine, then show me the latest leads.",
]

st.markdown("**Try:**  " + " · ".join(f"`{e}`" for e in EXAMPLES[:2]))
question = st.text_input("Question", key="ua_q", placeholder="Ask anything (KB or CRM)")

if st.button("Run agent", type="primary", disabled=not question.strip()):
    q = question.strip()
    with st.spinner("Agent is choosing tools..."):
        try:
            import unified_agent as ua
            t0 = time.time()
            res = ua.run(q)
            dt = time.time() - t0
            err = None
        except Exception as e:  # noqa: BLE001
            res, dt, err = None, 0, f"{type(e).__name__}: {e}"

    if err:
        st.error(f"Agent failed: {err}")
    else:
        st.markdown("### Answer")
        st.markdown(res["answer"] or "_(empty)_")
        st.caption(f"model `{res['model']}` · {dt:.1f}s · tools called: {len(res['steps'])}")

        if res["steps"]:
            st.markdown("**Tool trace:**")
            for i, s in enumerate(res["steps"], 1):
                args = json.dumps(s["args"], ensure_ascii=False)
                with st.expander(f"🔧 {i}. {s['tool']}  ·  {args[:90]}"):
                    st.code(s["result"], language=None)
        else:
            st.info("No tools were needed — the model answered directly.")

st.divider()
st.caption("Инструмент CRM ходит в PostgreSQL MCP-сервер (`POST /mcp`); если он не запущен, "
           "агент честно сообщит и ответит по базе знаний. RAG-инструмент работает всегда (Qdrant Cloud).")