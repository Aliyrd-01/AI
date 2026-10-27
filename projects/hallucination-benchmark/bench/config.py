"""Config & shared LLM access for the benchmark suite.

Keys are read ONLY from environment / .env files (no hardcoded secrets).
Providers: opencode-zen, mistral, openrouter, qubax.
"""

import io
import os
import sys
import time
import requests
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

# portfolio/.env (OPENAI_API_KEY = OpenCode Zen, MISTRAL_API_KEY, OPENROUTER_API_KEY)
load_dotenv(os.path.join(os.path.dirname(ROOT), ".env"))
# qubax.env (QUBAX_API_KEY, QUBAX_API_BASE)
load_dotenv(os.path.join("D:", os.sep, "AI", "opencode-work", "secrets", "qubax.env"))

ZEN_KEY = os.getenv("OPENAI_API_KEY", "")
MISTRAL_KEY = os.getenv("MISTRAL_API_KEY", "")
OR_KEY = os.getenv("OPENROUTER_API_KEY", "")
QUBAX_KEY = os.getenv("QUBAX_API_KEY", "")

DELAY = float(os.getenv("BENCH_DELAY", "0.5"))
TIMEOUT = 90

ENDPOINTS = {
    "opencode-zen": "https://opencode.ai/zen/v1/chat/completions",
    "mistral": "https://api.mistral.ai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "qubax": os.getenv("QUBAX_API_BASE", "").rstrip("/") + "/chat/completions",
}

API_KEYS = {
    "opencode-zen": ZEN_KEY,
    "mistral": MISTRAL_KEY,
    "openrouter": OR_KEY,
    "qubax": QUBAX_KEY,
}

# Default eval candidates — "equal weight-class" open/flash-tier lineup (Qubax aggregator).
# Chosen by user 2026-10-23: no OpenAI/Anthropic flagships (token cost), latest versions only.
MODELS = {
    "deepseek": ("qubax", "deepseek-v4.1-flash", "DeepSeek V4.1 Flash"),
    "gemini": ("qubax", "gemini-3.8-flash", "Gemini 3.8 Flash"),
    "glm": ("qubax", "glm-5.3-flash", "GLM 5.3 Flash"),
    "qwen": ("qubax", "qwen3.8-flash", "Qwen3.8 Flash"),
    "kimi": ("qubax", "kimi-k3", "Kimi K3"),
    "minimax": ("qubax", "minimax-m2.5", "MiniMax M2.5"),
    "mistral": ("qubax", "mistral-large-4-0", "Mistral Large 4.0"),
    "grok": ("qubax", "grok-4.7", "Grok 4.7"),
}

ALIASES = {
    "deepseek-v4.1-flash": "deepseek",
    "gemini-3.8-flash": "gemini",
    "glm-5.3-flash": "glm",
    "qwen3.8-flash": "qwen",
    "kimi-k3": "kimi",
    "minimax-m2.5": "minimax",
    "mistral-large-4-0": "mistral",
    "grok-4.7": "grok",
}


def resolve_model(key):
    key = (key or "").strip()
    return ALIASES.get(key, key)


def available_models():
    return [k for k, (prov, _, _) in MODELS.items() if API_KEYS.get(prov)]


class _Trip(Exception):
    pass


def _fail_stop():
    _FAIL["n"] += 1
    if _FAIL["n"] >= 5:
        raise _Trip("5 consecutive failures - stopping run")
    return _FAIL["n"]


_FAIL = {"n": 0}
_SUCCESS_STOP = 0


def ask(model_key, prompt, max_tokens=200, temperature=0.0):
    """Return dict: text, latency_s, prompt_tokens, completion_tokens, error."""
    global _SUCCESS_STOP
    model_key = resolve_model(model_key)
    if model_key not in MODELS:
        return {"text": "", "latency_s": 0.0, "prompt_tokens": 0, "completion_tokens": 0, "error": f"unknown model: {model_key}"}
    provider, model, _label = MODELS[model_key]
    key = API_KEYS.get(provider)
    if not key:
        return {"text": "", "latency_s": 0.0, "prompt_tokens": 0, "completion_tokens": 0, "error": f"no API key for {provider}"}

    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": temperature}
    if temperature == 0:
        payload["top_p"] = 1
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}

    t0 = time.time()
    err = None
    text = ""
    ptoks = ctoks = 0
    for attempt in (0, 1):  # one retry
        try:
            resp = requests.post(ENDPOINTS[provider], json=payload, headers=headers, timeout=TIMEOUT)
            if resp.status_code == 429:
                err = "429 rate limit"
                time.sleep(3.0 * (attempt + 1))
                continue
            resp.raise_for_status()
            data = resp.json()
            if "choices" in data and data["choices"]:
                msg = data["choices"][0].get("message", {}) or {}
                text = msg.get("content", "") or msg.get("reasoning_content", "") or msg.get("reasoning", "") or ""
                u = data.get("usage", {}) or {}
                ptoks = u.get("prompt_tokens", 0) or 0
                ctoks = u.get("completion_tokens", 0) or 0
            else:
                err = "no choices in response"
            err = None
            _FAIL["n"] = 0
            break
        except requests.RequestException as e:
            err = str(e)[:150]
            _fail_stop()
            time.sleep(2.0 * (attempt + 1))
        except Exception as e:  # noqa: BLE001
            err = str(e)[:150]
            _fail_stop()
            break
    if DELAY:
        time.sleep(DELAY)
    return {"text": text, "latency_s": round(time.time() - t0, 2), "prompt_tokens": ptoks, "completion_tokens": ctoks, "error": err}

