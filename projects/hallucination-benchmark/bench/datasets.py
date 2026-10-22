"""Dataset loaders - pure, deterministic, local-first (cached downloads)."""

import csv
import io
import json
import os
import requests
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

DATASETS = ["truthfulqa", "gsm8k", "bbh", "mmlu", "humaneval"]

GSM8K_URL = "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl"
BBH_TASKS = ["date_understanding", "logical_deduction_five_objects", "sports_understanding", "tracking_shuffled_objects_seven_objects", "boolean_expressions"]
BBH_BASE_URL = "https://raw.githubusercontent.com/suzgunmirac/BIG-Bench-Hard/main/bbh"


def _cache(name):
    return os.path.join(ROOT, "datasets", name)


def _get_cache(name, url=None, refresh=False):
    path = _cache(name)
    if refresh or not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with requests.get(url, timeout=60) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
    return path


def load_truthfulqa(limit=60, seed=42):
    """Real TruthfulQA csv (817 rows, mc1 format). Deterministic subset by seed."""
    path = os.path.join(ROOT, "TruthfulQA.csv")
    with open(path, encoding="utf-8", errors="replace") as f:
        rows = list(csv.DictReader(f))
    rows = _subset(rows, limit, seed)
    out = []
    for r in rows:
        # mc1: choices are comma-inside strings like "","",""; parse safely
        correct = r.get("Correct Answers", "")
        wrong = r.get("Incorrect Answers", "")
        choices = [x.strip() for x in _csv_split(correct) + _csv_split(wrong)]
        gold_idx = _csv_split(correct).index(next(s for s in _csv_split(correct) if s.strip() in choices))
        out.append({"question": r.get("Question", ""), "choices": choices, "gold": gold_idx, "category": r.get("Category", "")})
    return out


def _csv_split(s):
    return [x for x in (s or "").split(",") if x.strip()]


def _subset(rows, limit, seed):
    import random

    if limit and limit < len(rows):
        rnd = random.Random(seed)
        rows = rnd.sample(rows, limit)
    else:
        limit = len(rows)
    return rows


def load_gsm8k(limit=50, seed=42):
    path = _get_cache("gsm8k_test.jsonl", GSM8K_URL)
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            gold = d["answer"].split("####")[-1].strip().replace(",", "")
            rows.append({"question": d["question"], "gold": gold})
    return _subset(rows, limit, seed)


def load_bbh(limit_per_task=5, seed=42):
    all_rows = []
    for task in BBH_TASKS:
        fname = f"{urllib.parse.quote(task)}.json"
        url = f"{BBH_BASE_URL}/{fname}"
        path = _get_cache(os.path.join("bbh", f"{task}.json"), url)
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        examples = d.get("examples", [])
        if not examples:
            continue
        # example_target gives gold answer; each example is {input, target}
        rows = [{"question": e["input"], "gold": e["target"], "task": task} for e in examples]
        all_rows.extend(_subset(rows, limit_per_task, seed + hash(task) % 100))
    return all_rows


def load_mmlu(limit=100, seed=42):
    path = os.path.join(ROOT, "mmlu_500.json")
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    out = [{"question": r["question"], "choices": r["choices"], "gold": r["answer"], "subject": r.get("subject", "")} for r in rows]
    return _subset(out, limit, seed)


def load_humaneval(limit=30, seed=42):
    path = os.path.join(ROOT, "humaneval.json")
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    rows = rows if isinstance(rows, list) else list(rows.values())
    out = [{"task_id": r["task_id"], "prompt": r["prompt"], "entry_point": r["entry_point"], "test": r["test"]} for r in rows]
    return _subset(out, limit, seed)


def load(name, limit=None, seed=42):
    if name == "truthfulqa":
        return load_truthfulqa(limit=limit or 60)
    if name == "gsm8k":
        return load_gsm8k(limit=limit or 50)
    if name == "bbh":
        return load_bbh(limit_per_task=limit or 5)
    if name == "mmlu":
        return load_mmlu(limit=limit or 100)
    if name == "humaneval":
        return load_humaneval(limit=limit or 30)
    raise ValueError(f"unknown dataset: {name} (available: {DATASETS})")
