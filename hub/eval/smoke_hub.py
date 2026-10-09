"""Smoke test for the portfolio hub: every page must render without exception.

    python hub/eval/smoke_hub.py
"""

import os
import sys

from streamlit.testing.v1 import AppTest

HUB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = [
    "Home.py",
    "pages/1_RAG.py",
    "pages/2_n8n.py",
    "pages/3_Projects.py",
    "pages/4_Agents.py",
    "pages/5_Benchmarks.py",
    "pages/6_Unified_Agent.py",
]

fails = []
for p in PAGES:
    path = os.path.join(HUB, p)
    at = AppTest.from_file(path, default_timeout=300)
    at.run()
    if at.exception:
        msg = str(at.exception[0].message)
        fails.append((p, msg))
        print(f"FAIL  {p}  -- {msg}")
    else:
        print(f"PASS  {p}")

print("\n" + ("ALL PAGES OK" if not fails else f"FAILED: {[p for p, _ in fails]}"))
sys.exit(1 if fails else 0)
