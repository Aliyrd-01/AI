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

const server = spawn(process.execPath, [path.join(__dirname, "server.js")], { env: process.env, stdio: "ignore" });
await new Promise((r) => setTimeout(r, 1500));
const URL_ = `http://localhost:${PORT}/mcp`;
const c = new Client({ name: "ro", version: "1" });
await c.connect(new StreamableHTTPClientTransport(new URL(URL_), { requestInit: { headers: { Authorization: `Bearer ${process.env.REMOTE_SECRET_KEY}` } } }));

let pass = 0, fail = 0;
const chk = (n, x) => { x ? (pass++, console.log("PASS  " + n)) : (fail++, console.log("FAIL  " + n)); };

const sel = await c.callTool({ name: "select", arguments: { sql: "SELECT 1" } });
chk("readonly select allowed", sel.isError !== true);
const ins = await c.callTool({ name: "insert", arguments: { table: "city", data: { city: "x" } } });
chk("readonly insert blocked", ins.isError === true && ins.content[0].text.includes("READ_ONLY"));
const upd = await c.callTool({ name: "run_sql", arguments: { sql: "DELETE FROM city" } });
chk("readonly run_sql blocked", upd.isError === true && upd.content[0].text.includes("READ_ONLY"));
server.kill();
console.log(`\n===== ${pass} passed, ${fail} failed (READ_ONLY) =====`);
process.exit(fail ? 1 : 0);
