"""
Refusal (OOD) eval: does the system honestly refuse when the answer is NOT in the corpus?

Two sets:
  * OOD      — questions that MS MARCO (rag_v2*) cannot answer (post-2021 events,
               fake products, nonsense) -> we want honest refusals (target >= 0.70).
  * CONTROL  — normal in-corpus eval_set questions -> refusals here are FALSE
               refusals and must stay rare (<= 0.10).

Refusal signals (any one counts):
  * strict-grounding gate: the answer cites nothing that was retrieved;
  * the model itself says it cannot answer (prompt-instructed behaviour);
  * retrieval confidence below --min-conf (RRF score normalised to 0..1).

Usage:
    python eval/eval_refusal.py
    python eval/eval_refusal.py --min-conf 0.15 --target 0.7

Result: eval/results_refusal.json (rendered on the Benchmarks page)
"""

import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rag"))
from dotenv import load_dotenv

load_dotenv(os.path.join(HERE, "..", ".env"))

RESULTS = os.path.join(HERE, "results_refusal.json")
EVAL_SET = os.path.join(HERE, "eval_set.json")

# Questions the MS MARCO corpus (cutoff ~2021) has no answer to.
OOD_QUESTIONS = [
    "who won the FIFA World Cup in 2026",
    "what is the latest ChatGPT model released in 2026",
    "what is the price of bitcoin right now today",
    "who is the current president of the United States in 2026",
    "what Python version was released most recently in 2026",
    "how do I configure the Qubax router v9 dashboard",
    "what is the release date of iPhone 18 Pro",
    "who won Eurovision song contest 2025",
    "what is the newest NVIDIA GPU announced this year",
    "how many active users does the Telegram app have in 2026",
    "what is the weather forecast for Moscow tomorrow morning",
    "who won the Nobel Prize in physics last year",
    "what does the zzzq-frobnicator npm package do",
    "how do I reset my password on the ryochan crypto exchange",
    "what is the exchange rate of USDT to EUR right now",
    "which team won the super bowl in February 2026",
    "what is OpenAI o5 and when was it released",
    "how tall is the new Burj Jeddah tower completed in 2026",
    "what are the latest Windows 12 features",
    "who is the CEO of Qubax company",
    "what is the score of yesterday's real madrid barcelona match",
    "how do I sync my Ledger Nano X with the 2026 firmware",
    "what is the EU AI Act risk tier for GPT-5 agents",
    "who is streaming the champions league final 2027",
    "what is the air quality index in Delhi today",
    "what does the quantum-flux capacitor error code 42 mean",
]

_SAYS_CANNOT = re.compile(
    r"cannot answer|can'?t answer|not able to answer|impossible to answer|"
    r"i don'?t have (this|that|enough)|no information (about|on)|"
    r"not (contained|available|found) in the (context|corpus|retrieved)",
    re.I,
)

# Same saturation scale the hub UI uses for the default hybrid strategy
# (confidence = raw / (raw + 0.25) for Qdrant RRF scores).
_RRF_SAT = 0.25


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--control", type=int, default=20, help="in-corpus questions")
    ap.add_argument("--min-conf", type=float, default=0.15)
    ap.add_argument("--target", type=float, default=0.70)
    ap.add_argument("--max-false-refusal", type=float, default=0.10)
    args = ap.parse_args()

    import module_5_retrieval as m
    from module_7_generation import (
        format_context, sanitize_context, generate_citations,
        apply_strict_grounding, reorder_lost_in_middle,
    )
    from common import get_chat_llm, describe_llm

    llm = get_chat_llm(temperature=0)
    with open(EVAL_SET, encoding="utf-8") as f:
        control_q = [it["query"] for it in json.load(f)["items"][: args.control]]

    def run_one(q, kind):
        t0 = time.time()
        docs = m.search_hybrid(q, args.k)
        raw = max((float(d[2]) for d in docs), default=0.0)
        conf = raw / (raw + _RRF_SAT)
        docs = reorder_lost_in_middle(docs)
        numbering = [(i + 1, str(d[0])) for i, d in enumerate(docs)]
        context = sanitize_context(format_context(docs, reorder=False))
        answer = generate_citations(q, context, llm)
        gate = apply_strict_grounding(answer, [str(d[0]) for d in docs], numbering=numbering)
        signals = []
        if gate["refused"]:
            signals.append("no_valid_citation")
        if _SAYS_CANNOT.search(answer or ""):
            signals.append("says_cannot")
        if conf < args.min_conf:
            signals.append("low_confidence")
        refused = bool(signals)
        return {
            "query": q, "kind": kind, "refused": refused,
            "conf": round(conf, 3), "raw_top": round(raw, 4),
            "via": ",".join(signals) or "-",
            "latency_s": round(time.time() - t0, 2),
        }

    rows = []
    print(f"=== OOD ({len(OOD_QUESTIONS)}) ===")
    for q in OOD_QUESTIONS:
        r = run_one(q, "ood")
        rows.append(r)
        print(f"  ref={'Y' if r['refused'] else 'n'} conf={r['conf']:.3f} via={r['via']:24s} {q[:56]}")

    print(f"=== CONTROL ({len(control_q)}) ===")
    for q in control_q:
        r = run_one(q, "control")
        rows.append(r)
        print(f"  ref={'Y' if r['refused'] else 'n'} conf={r['conf']:.3f} via={r['via']:24s} {q[:56]}")

    ood = [r for r in rows if r["kind"] == "ood"]
    ctl = [r for r in rows if r["kind"] == "control"]
    refusal_rate = sum(r["refused"] for r in ood) / max(1, len(ood))
    false_rate = sum(r["refused"] for r in ctl) / max(1, len(ctl))
    passed = refusal_rate >= args.target and false_rate <= args.max_false_refusal

    out = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "llm": describe_llm(llm),
        "params": {"k": args.k, "min_conf": args.min_conf,
                   "target": args.target, "max_false_refusal": args.max_false_refusal},
        "summary": {
            "ood_n": len(ood), "control_n": len(ctl),
            "refusal_rate": round(refusal_rate, 3),
            "false_refusal_rate": round(false_rate, 3),
            "passed": passed,
        },
        "rows": rows,
    }
    with open(RESULTS, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("-" * 78)
    print(f"refusal_rate={refusal_rate:.3f} (target>={args.target})  "
          f"false_refusal={false_rate:.3f} (max {args.max_false_refusal})  "
          f"-> {'PASS' if passed else 'FAIL'}")
    print("saved ->", RESULTS)


if __name__ == "__main__":
    main()