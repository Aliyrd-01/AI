"""Unified Agent — routes a question between the RAG knowledge base and the CRM
database (PostgreSQL via MCP), using Qubax function-calling.

Tools:
  - search_knowledge_base(query) : hybrid retrieval over Qdrant (MS MARCO)
  - query_database(sql)          : read-only SQL via the PostgreSQL MCP server
"""

import json
import os

import httpx
from dotenv import load_dotenv

_HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_HERE, "..", "..", ".env"), override=True)

_BASE = (os.getenv("QUBAX_API_BASE") or os.getenv("OPENAI_API_BASE") or "https://api.qubax.ai/v1").rstrip("/")
_KEY = os.getenv("QUBAX_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
MODEL = os.getenv("AGENT_MODEL") or (os.getenv("QUBAX_MODELS", "").split(",")[0].strip() or "qwen3-235b-a22b-2507")
MCP_URL = os.getenv("MCP_URL", "http://localhost:9002/mcp")
MCP_TOKEN = os.getenv("MCP_TOKEN", "my-secret-key-123")

SYSTEM = (
    "You are a unified assistant with two tools: "
    "`search_knowledge_base` (MS MARCO passages) and `query_database` "
    "(PostgreSQL CRM, read-only). Choose the right tool(s) for the question. "
    "Use search_knowledge_base for general/encyclopedic knowledge and "
    "query_database for anything about leads, contacts, or CRM tables. You may "
    "call several tools. Then answer concisely, tagging facts with [KB] "
    "(knowledge base) or [DB] (database). If a tool fails, say so briefly and "
    "answer with what you have."
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
    if txt.lstrip().startswith("data:"):
        for line in txt.splitlines():
            if line.startswith("data:"):
                txt = line[5:].strip()
                break
    try:
        data = json.loads(txt)
    except Exception:  # noqa: BLE001
        return f"[DB raw] {txt[:300]}"
    result = data.get("result") or {}
    content = result.get("content") or []
    text = content[0].get("text") if content else json.dumps(result)
    return str(text)[:2000]


def _execute(name: str, args: dict) -> str:
    if name == "search_knowledge_base":
        return _search_kb(args.get("query", ""), int(args.get("k", 5) or 5))
    if name == "query_database":
        return _query_db(args.get("sql", ""))
    return f"Unknown tool: {name}"


def _chat(messages, tools):
    r = httpx.post(_BASE + "/chat/completions", timeout=180, headers={
        "Authorization": f"Bearer {_KEY}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": messages, "tools": tools,
              "tool_choice": "auto", "temperature": 0})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]


def run(question: str, max_steps: int = 4, on_step=None) -> dict:
    """Run the agent loop. Returns {answer, steps, model}. `on_step` is an optional
    callback(steps_list) for live UIs."""
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": question}]
    steps = []
    for _ in range(max_steps):
        msg = _chat(messages, TOOLS)
        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            return {"answer": msg.get("content") or "", "steps": steps, "model": MODEL}
        messages.append({"role": "assistant", "content": msg.get("content") or "",
                         "tool_calls": tool_calls})
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except Exception:  # noqa: BLE001
                args = {}
            result = _execute(name, args)
            steps.append({"tool": name, "args": args, "result": result[:800]})
            if on_step:
                on_step(steps)
            messages.append({"role": "tool",
                             "tool_call_id": tc.get("id", ""),
                             "content": result[:4000]})
    final = _chat(messages, TOOLS)
    return {"answer": final.get("content") or "(max steps reached)",
            "steps": steps, "model": MODEL}
