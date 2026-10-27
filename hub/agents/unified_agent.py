"""Unified Agent — routes a question between the RAG knowledge base and the CRM
database (PostgreSQL via MCP), using Qubax function-calling.

Tools:
  - search_knowledge_base(query) : hybrid retrieval over Qdrant (MS MARCO)
  - query_database(sql)          : read-only SQL via the PostgreSQL MCP server
"""

import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

_HERE = os.path.dirname(os.path.abspath(__file__))
_RAG = os.path.abspath(os.path.join(_HERE, "..", "rag"))
if _RAG not in sys.path:
    sys.path.insert(0, _RAG)
load_dotenv(os.path.join(_HERE, "..", "..", ".env"), override=True)

_BASE = (os.getenv("QUBAX_API_BASE") or os.getenv("OPENAI_API_BASE") or "https://api.qubax.ai/v1").rstrip("/")
_KEY = os.getenv("QUBAX_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
MODEL = os.getenv("AGENT_MODEL") or (os.getenv("QUBAX_MODELS", "").split(",")[0].strip() or "qwen3-235b-a22b-2507")
MCP_URL = os.getenv("MCP_URL", "http://localhost:9002/mcp")

_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_MCP_START_SCRIPT = os.path.join(_ROOT, "projects", "mcp-servers", "start-pg-mcp-server.ps1")
_mcp_bootstrapped = False


def _port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.4):
            return True
    except OSError:
        return False


def ensure_crm_server() -> bool:
    """Make sure the local CRM MCP server is reachable.

    If the port is closed and MCP_URL points to localhost, launch the project's
    start-pg-mcp-server.ps1 once (detached, no window) and wait for readiness.
    Returns True when the port is open; never raises.
    """
    global _mcp_bootstrapped
    u = urlparse(MCP_URL)
    port = u.port or 9002
    if _port_open(port):
        return True
    if _mcp_bootstrapped or (u.hostname or "localhost") not in ("localhost", "127.0.0.1"):
        return False
    _mcp_bootstrapped = True
    if os.name != "nt" or not os.path.exists(_MCP_START_SCRIPT):
        return False
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", _MCP_START_SCRIPT],
            creationflags=flags,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except OSError:
        return False
    deadline = time.time() + 20
    while time.time() < deadline:
        if _port_open(port):
            return True
        time.sleep(0.3)
    return _port_open(port)


def _load_mcp_token() -> str:
    tok = os.getenv("MCP_TOKEN", "")
    if tok:
        return tok
    try:
        p = Path(os.path.expanduser("~")) / "mcp_token.env"
        if p.exists():
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                m = re.match(r"\s*MCP_TOKEN\s*=\s*(.+?)\s*$", line)
                if m:
                    return m.group(1).strip().strip('"').strip("'")
    except Exception:  # noqa: BLE001
        pass
    return ""


MCP_TOKEN = _load_mcp_token()

_ALLOWED_TABLES = {"leads_leads", "leads_contacts", "leads_companies", "llm_pricing", "llm_usage"}
_FORBIDDEN = ("insert", "update", "delete", "drop", "alter", "create", "truncate",
              "grant", "revoke", "copy", "vacuum", "call", "do")

_EMAIL_RX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RX = re.compile(r"\+\d[\d\s().-]{7,}\d")


def mask_pii(text: str) -> str:
    """Redact e-mail addresses and international phone numbers."""
    text = _EMAIL_RX.sub("[email]", text)
    return _PHONE_RX.sub("[phone]", text)


def validate_sql(sql: str) -> tuple[bool, str]:
    """Client-side read-only guard: SELECT/WITH only, single statement, CRM tables."""
    s = (sql or "").strip()
    if not s:
        return False, "empty statement"
    if not re.match(r"^(select|with)\b", s, re.I):
        return False, "only SELECT / WITH statements are allowed"
    body = s.rstrip().rstrip(";")
    if ";" in body:
        return False, "multiple statements are not allowed"
    low = body.lower()
    for word in _FORBIDDEN:
        if re.search(rf"\b{word}\b", low):
            return False, f"{word.upper()} is not allowed"
    ctes = set(re.findall(r"(?:with|,)\s*([a-z_][a-z0-9_]*)\s+as\s*\(", low))
    tables = set(re.findall(r"\b(?:from|join)\s+([a-z_][a-z0-9_]*)", low)) - ctes
    unknown = tables - _ALLOWED_TABLES
    if unknown:
        return False, "table not in allowlist: " + ", ".join(sorted(unknown))
    return True, ""


SYSTEM = (
    "You are a unified assistant with two tools: "
    "`search_knowledge_base` (MS MARCO passages) and `query_database` "
    "(PostgreSQL CRM, read-only). Choose the right tool(s) for the question. "
    "Use search_knowledge_base for general/encyclopedic knowledge and "
    "query_database for anything about leads, contacts, or CRM tables. You may "
    "call several tools. Then answer concisely, tagging facts with [KB] "
    "(knowledge base) or [DB] (database). If a tool fails, say so briefly and "
    "answer with what you have. Never reuse [DB] facts from earlier turns of "
    "the conversation: every lead/CRM number, name or record must come from a "
    "fresh query_database call made in this turn, even if the same figure was "
    "already stated in the dialog.\n\n"
    "CRM schema (use these exact table names, never invent others):\n"
    "- leads_leads(lead_id, name, email, phone, company, company_industry, "
    "company_size, role, source, message, lead_score, lead_tier, priority, "
    "prompt_version, status, next_action)\n"
    "- leads_contacts(name, email, phone, role, company_id)\n"
    "- leads_companies(id, name, industry, size, domain)\n"
    "- llm_usage, llm_pricing\n"
    "For counts and hottest leads use leads_leads; add ORDER BY lead_score DESC "
    "LIMIT 5 unless the user asked for all rows. Keep SQL simple and valid: use "
    "COUNT(*) alone for a count, do not mix aggregates with plain columns in one "
    "SELECT, send one statement per call without a trailing semicolon. If "
    "query_database returns [DB blocked], correct the table/column names and "
    "retry at most once, then explain the limitation briefly instead of guessing "
    "numbers."
)

TOOLS = [
    {"type": "function", "function": {
        "name": "search_knowledge_base",
        "description": "Search the MS MARCO knowledge base for passages relevant to a query.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}, "k": {"type": "integer", "default": 5}},
            "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "query_database",
        "description": "Run a read-only SQL SELECT against the CRM PostgreSQL database.",
        "parameters": {"type": "object", "properties": {
            "sql": {"type": "string"}}, "required": ["sql"]}}},
]


def _search_kb(query: str, k: int = 5) -> str:
    try:
        import module_5_retrieval as m
        docs = m.search_hybrid(query, k)
    except Exception as e:  # noqa: BLE001
        return f"[KB error] {type(e).__name__}: {e}"
    if not docs:
        return "(no knowledge-base results)"
    return "\n\n".join(f"[{i}] {d[1][:600]}" for i, d in enumerate(docs, 1))


def _query_db(sql: str) -> str:
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "select", "arguments": {"sql": sql}}}
    try:
        r = httpx.post(MCP_URL, json=body, timeout=30, headers={
            "Authorization": f"Bearer {MCP_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"})
    except Exception as e:  # noqa: BLE001
        return f"[DB unavailable] {type(e).__name__}: {e} (MCP server not running?)"
    if r.status_code != 200:
        return f"[DB error] MCP HTTP {r.status_code}: {r.text[:200]}"
    txt = r.text
    if "data:" in txt:
        data_lines = [ln[5:].strip() for ln in txt.splitlines() if ln.startswith("data:")]
        if data_lines:
            txt = data_lines[-1]
    try:
        data = json.loads(txt)
    except Exception:  # noqa: BLE001
        return f"[DB raw] {txt[:300]}"
    result = data.get("result") or {}
    content = result.get("content") or []
    text = content[0].get("text") if content else json.dumps(result)
    return str(text)[:2000]


def _execute(name: str, args: dict, redact_pii: bool = False) -> str:
    if name == "search_knowledge_base":
        out = _search_kb(args.get("query", ""), int(args.get("k", 5) or 5))
    elif name == "query_database":
        sql = str(args.get("sql", ""))
        ok, why = validate_sql(sql)
        out = _query_db(sql) if ok else f"[DB blocked] {why}. Use a single read-only SELECT on CRM tables."
    else:
        out = f"Unknown tool: {name}"
    return mask_pii(out) if redact_pii else out


def _chat(messages, tools):
    r = httpx.post(_BASE + "/chat/completions", timeout=180, headers={
        "Authorization": f"Bearer {_KEY}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": messages, "tools": tools,
              "tool_choice": "auto", "temperature": 0})
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"], data.get("usage") or {}


def run(question: str, max_steps: int = 4, on_step=None,
        history: list | None = None, redact_pii: bool = False) -> dict:
    """Run the agent loop. Returns {answer, steps, model, usage}.

    `history` is an optional list of prior {role, content} turns (no tool messages).
    `on_step` is an optional callback(steps_list) for live UIs.
    """
    ensure_crm_server()
    messages = [{"role": "system", "content": SYSTEM}]
    for turn in (history or []):
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": str(turn["content"])[:4000]})
    messages.append({"role": "user", "content": question})
    steps = []
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def _loop(msgs: list, st: list) -> dict:
        for _ in range(max_steps):
            t0 = time.time()
            msg, u = _chat(msgs, TOOLS)
            for k in usage:
                usage[k] += int((u or {}).get(k) or 0)
            if not msg.get("tool_calls"):
                return {"answer": msg.get("content") or "", "steps": st,
                        "model": MODEL, "usage": usage,
                        "elapsed": round(time.time() - t0, 2)}
            msgs.append({"role": "assistant", "content": msg.get("content") or "",
                         "tool_calls": msg["tool_calls"]})
            for tc in msg["tool_calls"]:
                fn = tc.get("function", {})
                name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except Exception:  # noqa: BLE001
                    args = {}
                ts = time.time()
                result = _execute(name, args, redact_pii)
                step = {"tool": name, "args": args, "result": result[:1500],
                        "elapsed": round(time.time() - ts, 2)}
                st.append(step)
                if on_step:
                    on_step(st)
                msgs.append({"role": "tool",
                             "tool_call_id": tc.get("id", ""),
                             "content": result[:4000]})
        t0 = time.time()
        final, u = _chat(msgs, TOOLS)
        for k in usage:
            usage[k] += int((u or {}).get(k) or 0)
        return {"answer": final.get("content") or "(max steps reached)", "steps": st,
                "model": MODEL, "usage": usage, "elapsed": round(time.time() - t0, 2)}

    res = _loop(messages, steps)
    hist_db = any("[DB]" in str(t.get("content") or "")
                  for t in (history or []) if t.get("role") == "assistant")
    if hist_db and not res["steps"] and "[DB]" in (res.get("answer") or ""):
        messages.append({"role": "assistant", "content": res["answer"]})
        messages.append({"role": "user", "content":
            "You reused [DB] facts from earlier turns instead of verifying them. "
            "Call query_database now and re-answer from the fresh result only."})
        res2 = _loop(messages, [])
        if res2["steps"]:
            return res2
    return res
