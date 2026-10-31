"""Pure graders (no network) + HumanEval executor (subprocess sandbox)."""

import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
import os

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


# --- multiple choice -------------------------------------------------------
def mchoice_answer(text):
    """Return letter index 0..5 parsed from model text, else -1.

    Priority: 'Answer: X' marker > last (X) > last 'X)' > first bare letter.
    """
    if not text or not text.strip():
        return -1
    t = text.strip()
    m = re.search(r"[Aa]nswer\s*[:\-]?\s*\(?([A-Z])\)?", t)
    if m:
        return LETTERS.index(m.group(1))
    m = None
    for pat in (r"\(([A-Z])\)", r"\b([A-Z])\)"):
        found = re.findall(pat, t)
        if found:
            return LETTERS.index(found[-1])
    found = re.findall(r"\b([A-Z])\b", t)
    if found:
        return LETTERS.index(found[0])
    return -1


def mchoice_score(text, gold):
    """Accept gold as int index (0..25) or letter string ('A', '(D)')."""
    if isinstance(gold, str):
        g = gold.strip()
        if g.startswith("(") and g.endswith(")"):
            g = g[1:-1].strip()
        try:
            gold = LETTERS.index(g)
        except ValueError:
            return 0
    elif isinstance(gold, str):  # unreachable; kept for clarity
        pass
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


DANGEROUS_MODULES = {
    "os", "sys", "subprocess", "shutil", "socket", "http", "urllib", "requests",
    "ctypes", "posix", "nt", "pty", "fcntl", "signal", "winreg", "webbrowser",
    "multiprocessing", "threading", "asyncio", "importlib", "inspect", "builtins",
    "tempfile", "pickle", "shelve", "marshal", "tarfile", "zipfile", "pathlib", "gc",
}

DANGEROUS_CALLS = {
    "eval", "exec", "compile", "__import__", "open", "breakpoint", "globals", "locals", "vars", "dir"
}

DANGEROUS_ATTRS = {
    "__subclasses__", "__globals__", "__code__", "__bases__", "__mro__",
    "__builtins__", "__class__", "func_globals", "gi_frame"
}


def is_safe_humaneval_code(code_str: str) -> tuple[bool, str]:
    """AST-based static security verification to prevent RCE, network, file or privilege escalation."""
    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                if root_pkg in DANGEROUS_MODULES:
                    return False, f"Dangerous import rejected: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split(".")[0]
                if root_pkg in DANGEROUS_MODULES:
                    return False, f"Dangerous from-import rejected: {node.module}"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_CALLS:
                return False, f"Dangerous built-in call rejected: {node.func.id}"
        elif isinstance(node, ast.Attribute):
            if node.attr in DANGEROUS_ATTRS:
                return False, f"Introspection attribute rejected: {node.attr}"

    return True, "OK"


def humaneval_run(code, harness, entry_point, timeout=10):
    """Run code+tests in a sandboxed execution environment. Returns 1/0/-1 (error)."""
    # 1. AST static analysis to stop RCE attacks before execution
    safe, _ = is_safe_humaneval_code(code)
    if not safe:
        return 0

    # 2. Check if Docker container sandbox is enabled
    use_docker = os.environ.get("DOCKER_SANDBOX", "0").lower() in ("1", "true", "yes")

    sandbox_dir = tempfile.mkdtemp(prefix="he_sandbox_")
    script_path = os.path.join(sandbox_dir, "solution.py")

    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code + "\n\n" + harness + "\n")
            if "def check(" not in harness:
                f.write("\ndef check(candidate):\n    pass\n")
            f.write(f"\ncheck({entry_point})\n")

        if use_docker:
            cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                "-m", "128m",
                "-v", f"{sandbox_dir}:/sandbox:ro",
                "python:3.11-slim",
                "python", "/sandbox/solution.py"
            ]
            p = subprocess.run(cmd, capture_output=True, timeout=timeout)
            return 1 if p.returncode == 0 else 0
        else:
            # Isolated subprocess: no secrets in env, isolated working dir, -I flag
            clean_env = {
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
                "PYTHONIOENCODING": "utf-8",
                "PYTHONPATH": "",
                "PYTHONHASHSEED": "0",
                "TEMP": sandbox_dir,
                "TMP": sandbox_dir,
            }
            p = subprocess.run(
                [sys.executable, "-I", script_path],
                cwd=sandbox_dir,
                env=clean_env,
                capture_output=True,
                timeout=timeout,
            )
            return 1 if p.returncode == 0 else 0
    except (subprocess.TimeoutExpired, Exception):
        return 0
    finally:
        try:
            shutil.rmtree(sandbox_dir, ignore_errors=True)
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
