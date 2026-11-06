"""AI Portfolio hub - entrypoint with grouped sidebar navigation."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from errors import friendly_error, scrub_paths


def _safe_excepthook(exc_type, exc_value, exc_tb):
    """Last line of defense: uncaught errors never reach the UI as tracebacks
    (they would expose local paths and internals)."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    try:
        st.error(f"⚠️ {friendly_error(exc_value, 'ru')}\n\n{friendly_error(exc_value, 'en')}")
    except Exception:
        pass
    sys.stderr.write(scrub_paths("".join(
        __import__("traceback").format_exception(exc_type, exc_value, exc_tb))) + "\n")


sys.excepthook = _safe_excepthook

# Cloud deploy: Streamlit Cloud / HF Spaces keep secrets in st.secrets, while the
# app reads os.getenv everywhere. Copy string secrets into the environment once,
# before any view imports a module that reads env at import time.
try:
    for _key, _val in st.secrets.items():
        if isinstance(_val, str):
            os.environ.setdefault(_key, _val)
except Exception:
    pass

st.set_page_config(page_title="AI Portfolio - RAG + n8n", page_icon="\U0001F4CA", layout="wide")

NAV = {
    "Products": [
        st.Page("views/0_Home.py", title="Home", icon="\U0001F3E0", default=True),
        st.Page("views/1_RAG.py", title="RAG"),
        st.Page("views/2_N8N.py", title="N8N"),
        st.Page("views/3_Agents.py", title="Agents"),
        st.Page("views/4_MCP.py", title="MCP"),
        st.Page("views/6_Benchmarks.py", title="Benchmarks"),
        st.Page("views/7_Unified_Agent.py", title="Unified Agent"),
        st.Page("views/8_Projects.py", title="Projects"),
    ],
    "Info": [
        st.Page("views/90_Integrations.py", title="Integrations"),
        st.Page("views/91_Security.py", title="Security"),
        st.Page("views/92_Testing.py", title="Testing"),
        st.Page("views/93_Contacts.py", title="Contacts"),
    ],
}

st.navigation(NAV, position="sidebar").run()
