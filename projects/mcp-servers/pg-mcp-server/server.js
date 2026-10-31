import express from "express";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListResourceTemplatesRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs";
import path from "path";
import pkg from "pg";
const { Pool } = pkg;

const pool = new Pool({
  host: process.env.PG_HOST || "localhost",
  port: parseInt(process.env.PG_PORT || "5432"),
  user: process.env.PG_USER || "postgres",
  password: process.env.PG_PASSWORD,
  database: process.env.PG_DATABASE || "testPost2",
});

const APP_PORT = parseInt(process.env.PORT || "9002");
const SECRET_KEY = process.env.REMOTE_SECRET_KEY || "";
const READ_ONLY = (process.env.READ_ONLY || "1").toLowerCase() !== "0";
const ROW_LIMIT = parseInt(process.env.ROW_LIMIT || "100");
const AUDIT_FILE = process.env.AUDIT_FILE || "";

async function runSql(sql, params = []) {
  const r = await pool.query(sql, params);
  return r.rows;
}

async function runSqlRaw(sql) {
  const r = await pool.query(sql);
  return r.rows;
}

function mcpText(data) {
  const text = data === undefined ? "[]" : JSON.stringify(data, null, 2);
  return { content: [{ type: "text", text }] };
}

function mcpError(msg) {
  return { content: [{ type: "text", text: "ERROR: " + msg }], isError: true };
}

function audit(entry) {
  if (!AUDIT_FILE) return;
  try {
    if (!fs.existsSync(path.dirname(AUDIT_FILE))) fs.mkdirSync(path.dirname(AUDIT_FILE), { recursive: true });
    fs.appendFileSync(AUDIT_FILE, JSON.stringify({ ts: new Date().toISOString(), ...entry }) + "\n");
  } catch { }
}

function safeIdent(name, what = "identifier") {
  if (typeof name !== "string" || !/^[A-Za-z_][A-Za-z0-9_]{0,62}$/.test(name)) {
    throw new Error(`Invalid ${what}: ${String(name).slice(0, 40)}`);
  }
  return name;
}

function limitSelect(sql) {
  if (/\blimit\s+\d+/i.test(sql)) return sql;
  return sql.trim().replace(/\s*;?\s*$/, "") + ` LIMIT ${ROW_LIMIT}`;
}

function assertWritable(name) {
  if (READ_ONLY) throw new Error(`Server is in READ_ONLY mode: "${name}" is not available`);
}

function validateSafeClause(clause, name = "clause") {
  if (typeof clause !== "string" || !clause.trim()) throw new Error(`Missing ${name}`);
  if (/;|\/\*|\*\/|--/.test(clause)) {
    throw new Error(`Forbidden SQL characters in ${name}: semicolons and comment tokens are rejected`);
  }
  return clause.trim();
}

async function handleToolCall(name, args) {
  const t0 = Date.now();
  try {
    if (!args || typeof args !== "object") throw new Error("Missing arguments");
    let rows;
    switch (name) {
      case "list_tables": {
        rows = await runSql(
          "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name"
        );
        break;
      }
      case "describe_table": {
        const table = safeIdent(args.table, "table name");
        rows = await runSql(
          "SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_schema='public' AND table_name=$1 ORDER BY ordinal_position",
          [table]
        );
        break;
      }
      case "select": {
        if (typeof args.sql !== "string") throw new Error("Missing argument: sql");
        if (!/^\s*select\b|^\s*with\b/i.test(args.sql)) throw new Error("select tool accepts SELECT or WITH queries only");
        if (/;/.test(args.sql.trim().replace(/\s*;?\s*$/, ""))) throw new Error("Multiple SQL statements separated by ';' are forbidden");
        rows = await runSql(limitSelect(args.sql));
        break;
      }
      case "insert": {
        assertWritable(name);
        const table = safeIdent(args.table, "table name");
        const cols = Object.keys(args.data).map((c) => safeIdent(c, "column"));
        const vals = Object.values(args.data);
        const ph = vals.map((_, i) => `$${i + 1}`).join(",");
        const sql = `INSERT INTO ${table} (${cols.join(",")}) VALUES (${ph}) RETURNING *`;
        rows = await runSql(sql, vals);
        break;
      }
      case "update": {
        assertWritable(name);
        const table = safeIdent(args.table, "table name");
        const setCols = Object.keys(args.set).map((c) => safeIdent(c, "column"));
        const vals = Object.values(args.set);
        const setClause = setCols.map((c, i) => `${c} = $${i + 1}`).join(", ");
        const whereClause = validateSafeClause(args.where, "WHERE condition");
        rows = await runSql(`UPDATE ${table} SET ${setClause} WHERE ${whereClause} RETURNING *`, vals);
        break;
      }
      case "delete_rows": {
        assertWritable(name);
        const table = safeIdent(args.table, "table name");
        const whereClause = validateSafeClause(args.where, "WHERE condition");
        rows = await runSql(`DELETE FROM ${table} WHERE ${whereClause} RETURNING *`);
        break;
      }
      case "create_table": {
        assertWritable(name);
        await runSqlRaw(args.sql);
        rows = [];
        break;
      }
      case "add_column": {
        assertWritable(name);
        const table = safeIdent(args.table, "table name");
        if (typeof args.column_def !== "string" || !args.column_def.trim() || /;/.test(args.column_def)) {
          throw new Error("add_column requires a column def like \"name TYPE [constraint]\" and must not contain ';' ");
        }
        await runSqlRaw(`ALTER TABLE ${table} ADD COLUMN ${args.column_def}`);
        rows = [];
        break;
      }
      case "create_index": {
        assertWritable(name);
        const table = safeIdent(args.table, "table name");
        const columns = String(args.columns)
          .split(",")
          .map((c) => safeIdent(c.trim(), "column"))
          .join(",");
        await runSqlRaw(`CREATE INDEX ON ${table} (${columns})`);
        rows = [];
        break;
      }
      case "run_sql": {
        assertWritable(name);
        if (typeof args.sql !== "string") throw new Error("Missing argument: sql");
        rows = await runSqlRaw(args.sql);
        break;
      }
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
    audit({ kind: "tool", tool: name, ok: true, ms: Date.now() - t0, args_size: JSON.stringify(args || {}).length });
    return mcpText(rows);
  } catch (err) {
    audit({ kind: "tool", tool: name, ok: false, ms: Date.now() - t0, error: String(err.message).slice(0, 300) });
    return mcpError(err.message);
  }
}

async function getTableNames() {
  return await runSql(
    "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name"
  );
}

async function getTableColumns(table) {
  return await runSql(
    "SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_schema='public' AND table_name=$1 ORDER BY ordinal_position",
    [table]
  );
}

async function getTableSampleRows(table, limit = 5) {
  const t = safeIdent(table, "table name");
  return await runSql(`SELECT * FROM ${t} LIMIT ${limit}`);
}

async function getTableCount(table) {
  const t = safeIdent(table, "table name");
  const r = await runSql(`SELECT COUNT(*)::int AS cnt FROM ${t}`);
  return r[0]?.cnt ?? 0;
}

function createMcpServer() {
  const mcpServer = new Server(
    { name: "PostgreSQL MCP Server", version: "2.0.0" },
    { capabilities: { tools: {}, resources: {}, prompts: {} } }
  );

  mcpServer.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [
      { name: "list_tables", description: "List all tables", inputSchema: { type: "object", properties: {}, required: [] } },
      { name: "describe_table", description: "Show columns of a table", inputSchema: { type: "object", properties: { table: { type: "string" } }, required: ["table"] } },
      { name: "select", description: "Run a SELECT query", inputSchema: { type: "object", properties: { sql: { type: "string" } }, required: ["sql"] } },
      { name: "insert", description: "Insert data into a table", inputSchema: { type: "object", properties: { table: { type: "string" }, data: { type: "object" } }, required: ["table", "data"] } },
      { name: "update", description: "Update rows", inputSchema: { type: "object", properties: { table: { type: "string" }, set: { type: "object" }, where: { type: "string" } }, required: ["table", "set", "where"] } },
      { name: "delete_rows", description: "Delete rows by condition", inputSchema: { type: "object", properties: { table: { type: "string" }, where: { type: "string" } }, required: ["table", "where"] } },
      { name: "create_table", description: "Create a new table", inputSchema: { type: "object", properties: { sql: { type: "string" } }, required: ["sql"] } },
      { name: "add_column", description: "Add a column (schema migration)", inputSchema: { type: "object", properties: { table: { type: "string" }, column_def: { type: "string" } }, required: ["table", "column_def"] } },
      { name: "create_index", description: "Create an index", inputSchema: { type: "object", properties: { table: { type: "string" }, columns: { type: "string" } }, required: ["table", "columns"] } },
      { name: "run_sql", description: "Run any SQL statement", inputSchema: { type: "object", properties: { sql: { type: "string" } }, required: ["sql"] } },
    ],
  }));

  mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
    return await handleToolCall(request.params.name, request.params.arguments);
  });

  mcpServer.setRequestHandler(ListResourcesRequestSchema, async () => {
    const tables = await getTableNames();
    return {
      resources: [
        {
          uri: "postgres://tables",
          name: "All Tables",
          description: "List of all tables in the public schema",
          mimeType: "application/json",
        },
        ...tables.map((t) => ({
          uri: `postgres://table/${t.table_name}`,
          name: `Table: ${t.table_name}`,
          description: `Columns and sample rows for table ${t.table_name}`,
          mimeType: "application/json",
        })),
      ],
    };
  });

  mcpServer.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const uri = request.params.uri;
    if (uri === "postgres://tables") {
      const tables = await getTableNames();
      return {
        contents: [{ uri, mimeType: "application/json", text: JSON.stringify(tables.map((r) => r.table_name), null, 2) }],
      };
    }
    const tableMatch = uri.match(/^postgres:\/\/table\/(.+)$/);
    if (tableMatch) {
      const table = tableMatch[1];
      const columns = await getTableColumns(table);
      const count = await getTableCount(table);
      const sample = await getTableSampleRows(table);
      return {
        contents: [{
          uri,
          mimeType: "application/json",
          text: JSON.stringify({ table, columns, row_count: count, sample_rows: sample }, null, 2),
        }],
      };
    }
    throw new Error(`Resource not found: ${uri}`);
  });

  mcpServer.setRequestHandler(ListResourceTemplatesRequestSchema, async () => ({
    resourceTemplates: [
      {
        uriTemplate: "postgres://table/{name}",
        name: "Table Details",
        description: "Columns and sample data for a specific table",
        mimeType: "application/json",
      },
      {
        uriTemplate: "postgres://table/{name}/schema",
        name: "Table Schema",
        description: "Column definitions for a specific table",
        mimeType: "application/json",
      },
    ],
  }));

  mcpServer.setRequestHandler(ListPromptsRequestSchema, async () => ({
    prompts: [
      {
        name: "explain_table",
        description: "Explain the structure and content of a table",
        arguments: [
          { name: "table", description: "Table name", required: true },
          { name: "detail", description: "Detail level: basic or full", required: false },
        ],
      },
      {
        name: "query_data",
        description: "Generate an SQL query to answer a question about a table",
        arguments: [
          { name: "table", description: "Table name", required: true },
          { name: "question", description: "What data do you want to find?", required: true },
        ],
      },
    ],
  }));

  mcpServer.setRequestHandler(GetPromptRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    if (name === "explain_table") {
      const table = args?.table;
      if (!table) throw new Error("Missing argument: table");
      const columns = await getTableColumns(table);
      const count = await getTableCount(table);
      const colDesc = columns.map((c) => `- ${c.column_name} (${c.data_type})${c.is_nullable === "NO" ? " NOT NULL" : ""}${c.column_default ? ` DEFAULT ${c.column_default}` : ""}`).join("\n");
      const detail = args?.detail ?? "basic";
      let sample = "";
      if (detail === "full") {
        const rows = await getTableSampleRows(table, 10);
        sample = "\n\nSample rows:\n" + JSON.stringify(rows, null, 2);
      }
      audit({ kind: "prompt", prompt: name, ok: true, table });
      return {
        messages: [
          {
            role: "user",
            content: {
              type: "text",
              text: `Table \`${table}\` has ${count} rows.\n\nColumns:\n${colDesc}${sample}\n\nExplain what this table stores and suggest example queries.`,
            },
          },
        ],
      };
    }
    if (name === "query_data") {
      const table = args?.table;
      const question = args?.question;
      if (!table || !question) throw new Error("Missing required arguments");
      const columns = await getTableColumns(table);
      const colList = columns.map((c) => `${c.column_name} ${c.data_type}`).join(", ");
      audit({ kind: "prompt", prompt: name, ok: true, table });
      return {
        messages: [
          {
            role: "user",
            content: {
              type: "text",
              text: `Table \`${table}\` has columns: ${colList}\n\nQuestion: ${question}\n\nWrite a PostgreSQL query to answer this question.`,
            },
          },
        ],
      };
    }
    throw new Error(`Unknown prompt: ${name}`);
  });

  return mcpServer;
}

const app = express();
app.use(express.json());

app.post("/mcp", async (req, res) => {
  const auth = req.headers["authorization"];
  const t0 = Date.now();
  if (!SECRET_KEY || !auth || auth !== `Bearer ${SECRET_KEY}`) {
    audit({ kind: "http", event: "unauthorized", ok: false, ms: Date.now() - t0 });
    return res.status(401).json({ error: "Unauthorized: Missing or invalid token" });
  }
  try {
    const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
    const server = createMcpServer();
    res.on("close", () => {
      transport.close();
      server.close();
      audit({ kind: "http", event: "request_done", ok: true, ms: Date.now() - t0 });
    });
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    if (!res.headersSent) {
      res.status(500).json({ jsonrpc: "2.0", error: { code: -32603, message: error.message }, id: null });
    }
  }
});

app.get("/mcp", (_req, res) => {
  res.status(405).json({ jsonrpc: "2.0", error: { code: -32000, message: "Server does not stream by GET in stateless mode" }, id: null });
});

app.delete("/mcp", (_req, res) => {
  res.status(405).json({ jsonrpc: "2.0", error: { code: -32000, message: "No sessions persisted" }, id: null });
});

app.listen(APP_PORT, () => {
  console.log(`PostgreSQL MCP Server v2 on port ${APP_PORT}`);
  console.log(`http://localhost:${APP_PORT}/mcp`);
  if (READ_ONLY) console.log("READ_ONLY mode is ON");
  if (!SECRET_KEY) console.log("WARNING: REMOTE_SECRET_KEY is empty - auth is disabled");
  else console.log("Auth: Bearer token required");
});
