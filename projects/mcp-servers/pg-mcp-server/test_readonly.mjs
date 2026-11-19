// READ_ONLY mode smoke-test: spawn server with READ_ONLY=1
import { spawn } from "child_process";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = "9993";
process.env.READ_ONLY = "1";
process.env.PORT = PORT;
process.env.REMOTE_SECRET_KEY = process.env.REMOTE_SECRET_KEY || "testtoken123";

const server = spawn(process.execPath, [path.join(__dirname, "server.js")], {
  env: process.env,
  stdio: "ignore",
});

// Ждём реальную готовность: фиксированная пауза давала ECONNREFUSED
// на медленном старте (node + pg pool).
async function waitForHealth(url, timeoutMs = 20000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    try {
      const r = await fetch(url);
      if (r.ok) return true;
    } catch {
      /* сервер ещё не слушает */
    }
    await new Promise((r) => setTimeout(r, 200));
  }
  return false;
}

const ready = await waitForHealth(`http://localhost:${PORT}/health`);
if (!ready) {
  server.kill();
  console.log("FAIL  server did not become ready within 20s");
  process.exit(1);
}

const URL_ = `http://localhost:${PORT}/mcp`;
const c = new Client({ name: "ro", version: "1" });
await c.connect(new StreamableHTTPClientTransport(new URL(URL_), { requestInit: { headers: { Authorization: `Bearer ${process.env.REMOTE_SECRET_KEY}` } } }));

let pass = 0, fail = 0;
const chk = (n, x) => { x ? (pass++, console.log("PASS  " + n)) : (fail++, console.log("FAIL  " + n)); };

const sel = await c.callTool({ name: "select", arguments: { sql: "SELECT 1" } });
// Без живых учётных данных БД SELECT упадёт на подключении — это не нарушение
// политики. Важно, что инструмент не отвергнут самим read-only режимом.
const selText = (sel.content?.[0]?.text || "");
chk(
  "readonly select allowed by policy",
  sel.isError !== true || !selText.includes("READ_ONLY"),
);
if (sel.isError === true) console.log("      note: select reached DB but failed there:", selText.slice(0, 120));
const ins = await c.callTool({ name: "insert", arguments: { table: "city", data: { city: "x" } } });
chk("readonly insert blocked", ins.isError === true && ins.content[0].text.includes("READ_ONLY"));
const upd = await c.callTool({ name: "run_sql", arguments: { sql: "DELETE FROM city" } });
chk("readonly run_sql blocked", upd.isError === true && upd.content[0].text.includes("READ_ONLY"));
// data-modifying CTE через select не должен проходить
const cte = await c.callTool({
  name: "select",
  arguments: { sql: "WITH x AS (DELETE FROM city RETURNING *) SELECT * FROM x" },
});
chk("readonly CTE write blocked", cte.isError === true && cte.content[0].text.includes("READ_ONLY"));
server.kill();
console.log(`\n===== ${pass} passed, ${fail} failed (READ_ONLY) =====`);
process.exit(fail ? 1 : 0);
