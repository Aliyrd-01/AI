"""Pure graders (no network) + HumanEval executor (subprocess sandbox)."""

import json
import re
import subprocess
import sys
import tempfile
import os

LETTERS = "ABCDEF"


# --- multiple choice -------------------------------------------------------
def mchoice_answer(text):
    """Return letter index 0..5 parsed from model text, else -1.

    Priority: 'Answer: X' marker > last (X) > last 'X)' > first bare letter.
    """
    if not text or not text.strip():
        return -1
    t = text.strip()
    m = re.search(r"[Aa]nswer\s*[:\-]?\s*\(?([A-F])\)?", t)
    if m:
        return LETTERS.index(m.group(1))
    m = None
    for pat in (r"\(([A-F])\)", r"\b([A-F])\)"):
        found = re.findall(pat, t)
        if found:
            return LETTERS.index(found[-1])
    found = re.findall(r"\b([A-F])\b", t)
    if found:
        return LETTERS.index(found[0])
    return -1


def mchoice_score(text, gold):
    return int(mchoice_answer(text) == gold)


def mmlu_score(text, item):
    return mchoice_score(text, item["gold"])


def truthfulqa_score(text, item):
    return mchoice_score(text, item["gold"])


def bbh_score(text, item):
    return mchoice_score(text, item["gold"])


# --- numeric ---------------------------------------------------------------
def last_number(text):
    nums = re.findall(r"-?\d+[\d,]*(?:\.\d+)?", text or "")
    if not nums:
        return None
    return float(nums[-1].replace(",", "").rstrip(".")) if "." in nums[-1] else int(nums[-1].replace(",", ""))


def gsm8k_score(text, gold):
    got = last_number(text)
    try:
        want = float(gold) if "." in gold else int(gold)
    except ValueError:
        return 0
    return int(got == want)


# --- humaneval -------------------------------------------------------------
def extract_code(text, entry_point):
    """Pull python code out of a fenced markdown block, or the raw text."""
    t = (text or "").strip()
    if "```python" in t:
        t = t.split("```python")[1].split("```")[0]
    elif "```" in t:
        t = t.split("```")[1].split("```")[0]
    return t.strip()


def humaneval_run(code, harness, entry_point, timeout=15):
    """Run code+tests in an isolated python subprocess. Returns 1/0/-1 (error)."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code + "\n\n" + harness + "\n")
        f.write(f"\ncheck({entry_point})\n")
        path = f.name
    if "def check(" not in harness:
        # humaneval test blocks call check(candidate) as wrapper
        f2 = open(path, "a", encoding="utf-8")
        f2.write("def check(candidate):\n    pass\n")
        f2.close()
    try:
        p = subprocess.run([sys.executable, path], capture_output=True, timeout=timeout)
        return 1 if p.returncode == 0 else 0
    except subprocess.TimeoutExpired:
        return 0
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def humaneval_score(text, item):
    code = extract_code(text, item["entry_point"])
    if not code or not code.startswith(("#", "import", "from", "def", "class", "\n")):
        # allow code starting with comment OR after leading junk, find def
        m = re.search(r"def\s+" + re.escape(item["entry_point"]), code)
        if not m:
            return 0
        code = code[m.start():]
    harness = "def check(candidate):\n" + "\n".join(("    " + line) for line in item["test"].strip().splitlines() if not line.strip().startswith("def check"))
    r = humaneval_run(code, harness, item["entry_point"])
    return max(0, r) if r in (0, 1) else 0
