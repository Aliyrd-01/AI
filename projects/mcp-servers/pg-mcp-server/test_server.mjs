// pg-mcp-server v2 integration tests (self-contained: spawns its own server on TEST_PORT)
// Run: node test_server.mjs   (env: PG_* from caller, REMOTE_SECRET_KEY, TEST_PORT optional)
import { spawn, execSync } from "child_process";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = process.env.TEST_PORT || "9992";
const TOKEN = process.env.REMOTE_SECRET_KEY || "testtoken123";
const URL_ = `http://localhost:${PORT}/mcp`;
const AUDIT = path.join(__dirname, ".test-audit.jsonl");

let pass = 0, fail = 0;
const failures = [];
function ok(name, cond, extra = "") {
  if (cond) { pass++; console.log(`PASS  ${name}`); }
  else { fail++; failures.push(name); console.log(`FAIL  ${name} ${extra ? "(" + extra + ")" : ""}`); }
}
async function raw(url, method, headers, body) {
  const res = await fetch(url, { method, headers, body });
  return { status: res.status, text: await res.text() ? await res.text() : "" };
}

process.env.REMOTE_SECRET_KEY = TOKEN;
process.env.PORT = PORT;
process.env.ROW_LIMIT = "5";
process.env.AUDIT_FILE = AUDIT;
if (fs.existsSync(AUDIT)) fs.unlinkSync(AUDIT);

const server = spawn(process.execPath, [path.join(__dirname, "server.js")], {
  env: process.env,
  stdio: ["ignore", "pipe", "pipe"],
});
// wait for listen
let up = false;
server.stdout.on("data", () => { up = true; });
server.stderr.on("data", (d) => { up = true; });
for (let i = 0; i < 40 && !up; i++) {
  try { const r = await fetch(URL_); if (r.status === 405) { up = true; break; } } catch { }
  await new Promise((r) => setTimeout(r, 250));
}
ok("server listens", up);

// route negatives
const noAuth = await fetch(URL_, { method: "POST", headers: { "content-type": "application/json" }, body: "{}" });
ok("401 without token", noAuth.status === 401);
const get = await fetch(URL_, { method: "GET" });
ok("GET /mcp = 405", get.status === 405);
const def = await fetch(URL_, { method: "DELETE" });
ok("DELETE /mcp = 405", def.status === 405);

// proper client over streamable http
const transport = new StreamableHTTPClientTransport(new URL(URL_), {
  requestInit: { headers: { Authorization: `Bearer ${TOKEN}` } },
});
const client = new Client({ name: "test", version: "1.0.0" });
await client.connect(transport);
ok("client connect", true);

const tools = await client.listTools();
ok("10 tools", tools.tools.length === 10, `got ${tools.tools.length}`);
const names = tools.tools.map((t) => t.name).sort().join(",");
const expected = "add_column,create_index,create_table,delete_rows,describe_table,insert,list_tables,run_sql,select,update";
ok("exact tool set", names === expected, names);

const tables = await client.callTool({ name: "list_tables", arguments: {} });
const tableCount = tables.content?.[0]?.text ? JSON.parse(tables.content[0].text).length : 0;
ok("list_tables returns array", Array.isArray(tables.content) && tableCount >= 0);
const anyTable = tableCount > 0 ? JSON.parse(tables.content[0].text)[0].table_name : null;

if (anyTable) {
  const desc = await client.callTool({ name: "describe_table", arguments: { table: anyTable } });
  ok("describe_table columns", desc.content?.[0]?.text?.includes("column_name"));
}

const one = await client.callTool({ name: "select", arguments: { sql: "SELECT 1::int AS x, 'a'::text AS y" } });
ok("select 1", one.content?.[0]?.text?.includes('"x": 1'));
ok("select not isError", one.isError !== true);

// row limit: no LIMIT in sql -> wrapped with LIMIT 5
if (anyTable) {
  const lim = await client.callTool({ name: "select", arguments: { sql: `SELECT * FROM ${anyTable}` } });
  const parsed = JSON.parse(lim.content[0].text);
  ok("ROW_LIMIT applied", parsed.length <= 5, `got ${parsed.length}`);
}

// select rejects non-SELECT
const nonSel = await client.callTool({ name: "select", arguments: { sql: "DELETE FROM pg_tables" } });
ok("select rejects DELETE", nonSel.isError === true && nonSel.content[0].text.includes("SELECT or WITH"));

// injection: invalid table identifier
const injTable = await client.callTool({ name: "insert", arguments: { table: 'x"; DROP TABLE t; --', data: { a: 1 } } });
ok("injection table rejected", injTable.isError === true && injTable.content[0].text.includes("Invalid table name"));

// resources (before DDL tests so list_tables snapshot of stable schema)
const resources = await client.listResources();
ok("resources include postgres://tables", resources.resources.some((r) => r.uri === "postgres://tables"));
const resAll = await client.readResource({ uri: "postgres://tables" });
ok("readResource tables", resAll.contents[0].text.includes("["));
if (anyTable) {
  const resOne = await client.readResource({ uri: `postgres://table/${anyTable}` });
  ok("readResource table", resOne.contents[0].text.includes("row_count") && resOne.contents[0].text.includes("sample_rows"));
}
const templates = await client.listResourceTemplates();
ok("2 templates", templates.resourceTemplates.length === 2);

// prompts
const prompts = await client.listPrompts();
ok("2 prompts", prompts.prompts.length === 2);
if (anyTable) {
  const p = await client.getPrompt({ name: "explain_table", arguments: { table: anyTable, detail: "full" } });
  ok("prompt explain_table", p.messages[0].content.text.includes("Sample rows"));
}

// read-only ops blocked only when READ_ONLY=1 (not set here -> writable allowed try on temp table)
const created = await client.callTool({ name: "create_table", arguments: { sql: "CREATE TABLE IF NOT EXISTS _mcp_test_t (id serial PRIMARY KEY, v text)" } });
ok("create_table allowed in rw", created.isError !== true, JSON.stringify(created).slice(0, 150));
const ins = await client.callTool({ name: "insert", arguments: { table: "_mcp_test_t", data: { v: "hello" } } });
ok("insert works", ins.isError !== true && JSON.stringify(ins).includes("hello"));
const upd = await client.callTool({ name: "update", arguments: { table: "_mcp_test_t", set: { v: "bye" }, where: "v = 'hello'" } });
ok("update works", upd.isError !== true);
const del = await client.callTool({ name: "delete_rows", arguments: { table: "_mcp_test_t", where: "v = 'bye'" } });
ok("delete works", del.isError !== true);
const col = await client.callTool({ name: "add_column", arguments: { table: "_mcp_test_t", column_def: "note text" } });
ok("add_column works", col.isError !== true);
const idx = await client.callTool({ name: "create_index", arguments: { table: "_mcp_test_t", columns: "v" } });
ok("create_index works", idx.isError !== true);
const drop = await client.callTool({ name: "run_sql", arguments: { sql: "DROP TABLE _mcp_test_t" } });
ok("run_sql works", drop.isError !== true);

// second full session on SAME client transport already exercised; now a NEW fresh client to mimic inspector re-connect
await client.close();
const client2 = new Client({ name: "test2", version: "1.0.0" });
await client2.connect(new StreamableHTTPClientTransport(new URL(URL_), { requestInit: { headers: { Authorization: `Bearer ${TOKEN}` } } }));
const tools2 = await client2.listTools();
ok("second session tools", tools2.tools.length === 10);
await client2.close();

// audit log written with entries
await new Promise((r) => setTimeout(r, 300));
ok("audit file exists", fs.existsSync(AUDIT));
if (fs.existsSync(AUDIT)) {
  const lines = fs.readFileSync(AUDIT, "utf8").trim().split("\n").filter(Boolean);
  ok("audit has tool entries", lines.some((l) => l.includes('"kind":"tool"')));
  ok("audit has 401 entry", lines.some((l) => l.includes("unauthorized")));
  ok("no password in audit", !lines.some((l) => /password/i.test(l.replace(/"error":"[^"]*"/g, ""))));
}

server.kill();
// summary
console.log(`\n===== ${pass} passed, ${fail} failed =====`);
if (failures.length) { console.log("FAILED: " + failures.join(" | ")); process.exit(1); }
process.exit(0);
