"""Smoke test for the portfolio hub: every page must render without exception.

Pages are opened through the Home entrypoint (switch_page), so `st.page_link`
paths resolve exactly as they do in the running app.

    python hub/eval/smoke_hub.py
"""

import os
import sys

from streamlit.testing.v1 import AppTest

HUB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.join(HUB, "Home.py")
PAGES = [
    "pages/1_RAG.py",
    "pages/2_n8n.py",
    "pages/3_Agents.py",
    "pages/4_MCP.py",
    "pages/9_Testing.py",
    "pages/6_Benchmarks.py",
    "pages/7_Unified_Agent.py",
    "pages/8_Projects.py",
    "pages/10_Contacts.py",
]

fails = []
for p in PAGES:
    at = AppTest.from_file(HOME, default_timeout=300)
    at.run()
    if at.exception:
        msg = str(at.exception[0].message)
        fails.append((p, msg))
        print(f"FAIL  Home.py  -- {msg}")
        continue
    at.switch_page(p)
    at.run()
    if at.exception:
        msg = str(at.exception[0].message)
        fails.append((p, msg))
        print(f"FAIL  {p}  -- {msg}")
    else:
        print(f"PASS  {p}")

print("\n" + ("ALL PAGES OK" if not fails else f"FAILED: {[p for p, _ in fails]}"))
sys.exit(1 if fails else 0)
