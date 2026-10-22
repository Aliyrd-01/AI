"""CLI: python -m bench.run_all --dataset mmlu --models big-pickle --limit 5"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bench.config import available_models
from bench.runner import run_dataset


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", required=True, choices=["truthfulqa", "gsm8k", "bbh", "mmlu", "humaneval"])
    p.add_argument("--models", default=",".join(available_models()))
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()

    for model in (m.strip() for m in args.models.split(",")):
        print(f"=== {args.dataset} × {model} ===")
        s = run_dataset(args.dataset, model, args.limit)
        print(f"acc={s['acc']:.3f} ({s['correct']}/{s['answered']})  err={s['errors']}  avg_lat={s['avg_latency_s']}s  run={s['run_seconds']}s")


if __name__ == "__main__":
    main()
