"""Day-2 full run driver: all models x all datasets, sequential, log-friendly.

Usage: python day2_run.py            (uses bench.config MODELS order)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bench.config import MODELS
from bench.runner import run_dataset

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
SUMMARY = os.path.join(RESULTS, "bench_results.json")

DATASETS = ["mmlu", "truthfulqa", "gsm8k", "bbh", "humaneval"]
SIZES = {"mmlu": 100, "truthfulqa": 60, "gsm8k": 50, "bbh": 25, "humaneval": 30}

done = set()
if os.path.exists(SUMMARY):
    try:
        data = json.load(open(SUMMARY, encoding="utf-8"))
        for r in data.get("runs", []):
            if r.get("answered") == SIZES.get(r.get("dataset")) and not r.get("errors"):
                done.add((r["dataset"], r["model"]))
    except Exception:
        pass
print(f"resume: {len(done)} combos already complete", flush=True)

for model in MODELS:
    for ds in DATASETS:
        if (ds, model) in done:
            print(f"=== SKIP {ds} x {model} (done) ===", flush=True)
            continue
        print(f"=== {ds} x {model} ===", flush=True)
        try:
            s = run_dataset(ds, model, None)
            print(
                f"acc={s['acc']:.3f} n={s['answered']} err={s['errors']} "
                f"tok={s['tokens_total']} lat={s['avg_latency_s']}s run={s['run_seconds']}s",
                flush=True,
            )
        except Exception as e:  # noqa: BLE001
            print(f"FAILED {ds} x {model}: {e}", flush=True)
print("DAY2 COMPLETE", flush=True)
