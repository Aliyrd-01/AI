"""
Pure-function unit tests (no network, no models). Safe to run in CI.

    python eval/test_units.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rag"))
sys.path.insert(0, HERE)

from module_5_retrieval import _fix_mojibake, _diversify  # noqa: E402
from eval_retrieval import hit_rate_at_k, mrr_at_k, ndcg_at_k  # noqa: E402

FAILS = []


def check(name, cond):
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        FAILS.append(name)


# --- mojibake repair -------------------------------------------------------
check("mojibake: em-dash repaired", _fix_mojibake("Color\u00e2\u20ac\u201durine") == "Color\u2014urine")
check("mojibake: clean text untouched", _fix_mojibake("plain text") == "plain text")
check("mojibake: empty safe", _fix_mojibake("") == "")

# --- retrieval metrics -----------------------------------------------------
check("hit@k: hit", hit_rate_at_k(["a", "b"], {"b"}, 2) == 1.0)
check("hit@k: miss", hit_rate_at_k(["a"], {"b"}, 1) == 0.0)
check("mrr@k: rank 2", mrr_at_k(["a", "b"], {"b"}, 10) == 0.5)
check("ndcg@k: perfect", ndcg_at_k(["a"], {"a"}, 10) == 1.0)

# --- diversity -------------------------------------------------------------
docs = [("1", "alpha beta gamma", 1.0, {}),
        ("2", "alpha beta gamma", 0.9, {}),
        ("3", "delta epsilon zeta", 0.8, {})]
out = _diversify(docs, 2)
check("diversify drops near-duplicate", len(out) == 2 and {d[0] for d in out} == {"1", "3"})

# --- strict grounding gate (auto-refuse) -----------------------------------
from module_7_generation import apply_strict_grounding, extract_citations, normalize_citations  # noqa: E402

ids = ["a1", "b2"]
g = apply_strict_grounding("Plain answer with no citations.", ids, refusal="REFUSED")
check("strict: uncited -> refused", g["refused"] and g["answer"] == "REFUSED"
      and g["draft"] == "Plain answer with no citations.")
g = apply_strict_grounding("Fact [1](msmarco#a1).", ids)
check("strict: cited -> kept", (not g["refused"]) and g["answer"] == "Fact [1](msmarco#a1)."
      and g["cited"] == {"a1"} and g["draft"] == "")
g = apply_strict_grounding("Fact [1](msmarco#nope).", ids, refusal="REFUSED")
check("strict: unknown doc -> refused", g["refused"] and g["answer"] == "REFUSED")
g = apply_strict_grounding("", ids, refusal="REFUSED")
check("strict: empty answer -> refused", g["refused"] and g["answer"] == "REFUSED")

# --- bare-number citation repair -------------------------------------------
fixed = normalize_citations("Dark yellow urine is concentrated 1, and beets can tint it 2.", ids)
check("cite repair: bare numbers -> links",
      extract_citations(fixed) == [("1", "a1"), ("2", "b2")])
check("cite repair: proper links untouched",
      normalize_citations("Fact [2](msmarco#b2).", ids) == "Fact [2](msmarco#b2).")
check("cite repair: out of range untouched",
      normalize_citations("It costs 0 and 7 000 dollars.", ids) == "It costs 0 and 7 000 dollars.")
check("cite repair: decimal/date untouched",
      normalize_citations("Take 2.5 mg in 2007 at 3 pm.", ids) == "Take 2.5 mg in 2007 at 3 pm.")
check("cite repair: grounds the answer",
      not apply_strict_grounding(normalize_citations("Dark urine is concentrated 1.", ids), ids)["refused"])

# --- judge score parser ------------------------------------------------------
from module_7_generation import parse_score  # noqa: E402

check("score: plain", parse_score("0.95") == 0.95)
check("score: comma decimal", parse_score("0,95") == 0.95)
check("score: percent", parse_score("95%") == 0.95)
check("score: sentence", parse_score("The score is 0.8 out of 1.") == 0.8)
check("score: clamped", parse_score("1.4") == 1.0)
check("score: garbage -> None (not a silent 0)", parse_score("yes") is None)
check("score: empty -> None", parse_score("") is None)
check("score: huge -> None", parse_score("1000000") is None)

print("\n" + ("ALL UNIT TESTS PASSED" if not FAILS else f"FAILED: {FAILS}"))
sys.exit(1 if FAILS else 0)
