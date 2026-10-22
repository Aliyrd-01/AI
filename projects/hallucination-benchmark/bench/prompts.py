"""Prompt templates per dataset."""

ANSWER_SUFFIX = "\n\nAnswer with ONLY the letter." if False else ""  # keep it short below


def _mc_prompt(item):
    letters = "ABCDEF"[: len(item["choices"])]
    lines = [f"{letters[i]}) {c}" for i, c in enumerate(item["choices"])]
    return f"{item['question']}\n\n" + "\n".join(lines) + "\n\nReply with ONLY the letter."


def build_prompt(dataset, item):
    if dataset in ("truthfulqa", "mmlu", "bbh"):
        return _mc_prompt(item)
    if dataset == "gsm8k":
        return f"{item['question']}\n\nSolve the problem. End your reply with the final numeric answer after ### (like: ### 42)."
    if dataset == "humaneval":
        return (
            "Complete the following Python function. Reply with the FULL function implementation only "
            "(no imports, no tests, no explanations).\n\n"
            + item["prompt"]
        )
    raise ValueError(dataset)
