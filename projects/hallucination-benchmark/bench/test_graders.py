"""Pure unit tests for graders (no network, no models). Safe in CI.

    python bench/test_graders.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from bench.graders import (  # noqa: E402
    bbh_score,
    gsm8k_score,
    humaneval_score,
    mchoice_answer,
    mchoice_score,
    mmlu_score,
    truthfulqa_score,
)
from bench.datasets import load, load_gsm8k, load_mmlu, load_humaneval, load_truthfulqa, load_bbh, DATASETS  # noqa: E402

FAILS = []


def check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    if not cond:
        FAILS.append(name)


# --- multiple choice parsing ------------------------------------------------
check("MC: (B) selected", mchoice_answer("(B) paris") == 1)
check("MC: letter style 'C)' selected", mchoice_answer("C) 42") == 2)
check("MC: 'Answer: D' selected", mchoice_answer("The answer is D") == 3)
check("MC: bold (**A**) selected", mchoice_answer("**A**") == 0)
check("MC: none found", mchoice_answer("idk") == -1)
check("MC: empty", mchoice_answer("") == -1)
check("MC: two letters - first wins", mchoice_answer("A then B") == 0)
check("MC: score right/wrong", mchoice_score("(C)", 2) == 1 and mchoice_score("(B)", 2) == 0)

# --- dataset-based scores ----------------------------------------------------
check("MC: bold (**A**) selected", mchoice_answer("**A**") == 0)
check("MC: none found", mchoice_answer("idk") == -1)
check("MC: empty", mchoice_answer("") == -1)
check("MC: bare first letter wins without markers", mchoice_answer("A then B") == 0)
check("MC: Answer marker beats (B)", mchoice_answer("(B)... Answer: C") == 2)
check("MC: last paren beats early", mchoice_answer("(A) or (C)") == 2)
check("MC: score right/wrong", mchoice_score("(C)", 2) == 1 and mchoice_score("(B)", 2) == 0)

# --- dataset-based scores ----------------------------------------------------
item_mmlu = {"gold": 2}
check("mmlu score (Answer: C)", mmlu_score("Let me think it through.\nAnswer: C", item_mmlu) == 1)
check("mmlu score (last paren wins)", mmlu_score("(A) ... but (C) is correct", item_mmlu) == 1)
item_tqa = {"gold": 0}
check("truthfulqa score", truthfulqa_score("No, A) it isn't", item_tqa) == 1)
item_bbh = {"gold": 3}
check("bbh score (D)", bbh_score("(D)", item_bbh) == 1)

# --- numeric ------------------------------------------------------------------
check("gsm: ### 42", gsm8k_score("### 42", "42") == 1)
check("gsm: trailing number", gsm8k_score("Total is 1,234.", "1234") == 1)
check("gsm: wrong", gsm8k_score("### 40", "42") == 0)
check("gsm: none", gsm8k_score("no numbers here", "42") == 0)
check("gsm: float gold", gsm8k_score("### 3.5", "3.5") == 1)

# --- humaneval ---------------------------------------------------------------
CODE_OK = "def add(a, b):\n    return a + b"
TEST_ADD = dict(entry_point="add",
  specific_test="def check(candidate): assert candidate == None",
  test='def check(candidate):\n    assert candidate(1, 2) == 3\n    assert candidate(-1, 1) == 0')
ITEM_HE = {"task_id": "H/1", "prompt": "def add(a, b):\n\"\"\"add two\"\"\"\n", "entry_point": "add", "test": "def check(candidate):\n    assert candidate(1, 2) == 3\n    assert candidate(-1, 1) == 0"}
check("humaneval: valid code passes", humaneval_score(CODE_OK, ITEM_HE) == 1)
check("humaneval: broken code fails", humaneval_score("def add(a, b):\n    return a - b", ITEM_HE) == 0)
check("humaneval: fence extraction", humaneval_score("```python\ndef add(a, b):\n    return a + b\n```", ITEM_HE) == 1)

# --- datasets loaders ------------------------------------------------------
check("DATASETS list stable", DATASETS == ["truthfulqa", "gsm8k", "bbh", "mmlu", "humaneval"])
g = load_gsm8k(limit=5, seed=1)
check("gsm8k subset n=5", len(g) == 5 and "question" in g[0] and "gold" in g[0])
m = load_mmlu(limit=10, seed=1)
check("mmlu subset n=10", len(m) == 10 and 0 <= m[0]["gold"] <= 3 and isinstance(m[0]["choices"], list) == True)
he = load_humaneval(limit=5, seed=1)
check("humaneval subset keys", all("entry_point" in r and "test" in r for r in he))
t = load_truthfulqa(limit=4, seed=1)
check("truthfulqa has choices+gold", all(len(r["choices"]) >= 2 and r["gold"] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[: len(r["choices"])] for r in t))
b = load_bbh(limit_per_task=2, seed=1)
check("bbh rows>0 and gold present", len(b) >= 2 and all("gold" in r for r in b))
two = load_gsm8k(limit=3, seed=1); three = load_gsm8k(limit=3, seed=1)
check("deterministic subset (seed stable)", two == three)
PASS_ALL = [
    "clean text: MC none stays none",  # extra assertions summary
]


# summary count fix: display real totals at end instead of placeholder.

print("\n===== ALL OK =====" if not FAILS else "", flush=True)
if FAILS:
    print("FAILED: " + " | ".join(FAILS))
    sys.exit(1)
print("ALL OK")
