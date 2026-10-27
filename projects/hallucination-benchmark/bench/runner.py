"""Runner: run dataset Г— model, write raw JSONL + aggregated bench_results.json."""

import json
import os
import time
from datetime import datetime, timezone

from . import graders
from .config import ask

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(os.path.dirname(HERE), "results")
RAW = os.path.join(RESULTS, "raw")
SUMMARY = os.path.join(RESULTS, "bench_results.json")

SCORE_FNS = {
    "truthfulqa": graders.truthfulqa_score,
    "gsm8k": lambda text, item: graders.gsm8k_score(text, item["gold"]),
    "bbh": graders.bbh_score,
    "mmlu": graders.mmlu_score,
    "humaneval": graders.humaneval_score,
}


def run_one(dataset, item, model_key):
    from .prompts import build_prompt
    prompt = build_prompt(dataset, item)
    r = ask(model_key, prompt, max_tokens=512)
    correct = 0
    if not r["error"] and r["text"]:
        correct = int(SCORE_FNS[dataset](r["text"], item))
    return {
        "item": dataset,
        "model": model_key,
        "correct": bool(correct),
        "score": correct,
        "latency_s": r["latency_s"],
        "prompt_tokens": r["prompt_tokens"],
        "completion_tokens": r["completion_tokens"],
        "error": r["error"] or None,
    }


def run_dataset(dataset, model_key, limit, seed=42):
    from .config import resolve_model
    model_key = resolve_model(model_key)
    from .datasets import load
    items = load(dataset, limit=limit)
    out_path = os.path.join(RAW, f"{dataset}_{model_key}.jsonl")
    os.makedirs(RAW, exist_ok=True)
    rows = []
    t0 = time.time()
    for i, item in enumerate(items, 1):
        row = run_one(dataset, item, model_key)
        row["i"] = i
        rows.append(row)
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), **row}) + "\n")
        mark = "OK " if row["correct"] else ("ERR" if row["error"] else "no ")
        print(f"[{i}/{len(items)}] {mark} lat={row['latency_s']}s", flush=True)
    done = [r for r in rows if not r["error"]]
    summary = _aggregate(dataset, model_key, len(items), done, items)
    summary["run_seconds"] = round(time.time() - t0, 1)
    _merge_summary(summary)
    return summary


def _aggregate(dataset, model_key, total, done, items):
    correct = sum(r["score"] for r in done if r["score"] in (0, 1) and (dataset not in ("humaneval",)))
    if dataset == "humaneval":
        correct = sum(r["score"] for r in done)
    n = len(done)
    return {
        "model": model_key,
        "dataset": dataset,
        "n": total,
        "answered": n,
        "errors": total - n,
        "correct": correct,
        "acc": round(correct / max(1, n), 3) if n else 0.0,
        "avg_latency_s": round(sum(r["latency_s"] for r in done) / max(1, n), 2),
        "tokens_total": sum(r["prompt_tokens"] + r["completion_tokens"] for r in done),
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def _merge_summary(summary):
    data = {"runs": []}
    if os.path.exists(SUMMARY):
        try:
            with open(SUMMARY, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
    data.setdefault("runs", []).append(summary)
    with open(SUMMARY, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

