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
    "views/0_Home.py",
    "views/1_RAG.py",
    "views/2_N8N.py",
    "views/3_Agents.py",
    "views/4_MCP.py",
    "views/6_Benchmarks.py",
    "views/7_Unified_Agent.py",
    "views/8_Projects.py",
    "views/90_Integrations.py",
    "views/91_Security.py",
    "views/92_Testing.py",
    "views/93_Contacts.py",
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
