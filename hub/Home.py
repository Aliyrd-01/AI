"""AI Portfolio hub - entrypoint with grouped sidebar navigation."""

import streamlit as st

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
