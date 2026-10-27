"""Build the hub-facing benchmark summary from results/bench_results.json."""

import json
import os
import sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(BASE, "results", "bench_results.json")
OUT_LOCAL = os.path.join(BASE, "results", "bench_summary.json")
OUT_HUB = os.path.abspath(os.path.join(BASE, "..", "..", "hub", "eval", "bench_free_results.json"))

DATASETS = ["mmlu", "truthfulqa", "gsm8k", "bbh", "humaneval"]
TARGET = {"mmlu": 100, "truthfulqa": 60, "gsm8k": 50, "bbh": 25, "humaneval": 30}
LABELS = {
    "deepseek": "DeepSeek V4.1 Flash",
    "gemini": "Gemini 3.8 Flash",
    "glm": "GLM 5.3 Flash",
    "qwen": "Qwen3.8 Flash",
    "kimi": "Kimi K3",
    "minimax": "MiniMax M2.5",
    "mistral": "Mistral Large 4.0",
    "grok": "Grok 4.7",
}

runs = json.load(open(RESULTS, encoding="utf-8"))["runs"]
models = [m for m in LABELS if any(r["model"] == m for r in runs)]

results = {}
for m in models:
    results[m] = {"label": LABELS[m]}
for r in runs:
    m, ds = r["model"], r["dataset"]
    if m not in results or ds not in DATASETS:
        continue
    n = r.get("n") or 0
    answered = r.get("answered") or 0
    if not n or answered / TARGET[ds] < 0.9:
        continue
    results[m][ds] = {
        "acc": round(r["acc"], 4),
        "answered": answered,
        "n": n,
        "err": r.get("errors", 0),
        "latency_s": round(r.get("avg_latency_s") or 0, 2),
    }

rows = []
for m, cell in results.items():
    accs = [cell[ds]["acc"] for ds in DATASETS if ds in cell]
    cell["avg"] = round(sum(accs) / len(accs), 4) if accs else None
    cell["datasets_done"] = len(accs)
    rows.append((m, cell["avg"] or 0, cell))

rows.sort(key=lambda x: x[1], reverse=True)
order = [m for m, _, _ in rows]

payload = {
    "meta": {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n": TARGET,
        "datasets": DATASETS,
        "models": order,
    },
    "results": results,
    "tqa": {m: {"acc": results[m]["truthfulqa"]["acc"]} for m in order if "truthfulqa" in results[m]},
    "gsm_bbh": {
        m: {
            "gsm8k": results[m]["gsm8k"]["acc"] * 100 if "gsm8k" in results[m] else None,
            "bbh": results[m]["bbh"]["acc"] * 100 if "bbh" in results[m] else None,
            "total": results[m]["avg"] * 100 if results[m]["avg"] is not None else None,
        }
        for m in order
    },
}

for path in (OUT_LOCAL, OUT_HUB):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("written", path)

print("models:", len(order), "| full grids:", sum(1 for m in order if results[m]["datasets_done"] == 5))
