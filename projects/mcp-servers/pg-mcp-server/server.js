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
import pkg from "pg";
const { Pool } = pkg;

const pool = new Pool({
  host: process.env.PG_HOST || "localhost",
  port: parseInt(process.env.PG_PORT || "5432"),
  user: process.env.PG_USER || "postgres",
  password: process.env.PG_PASSWORD || "12qwerty12",
  database: process.env.PG_DATABASE || "testPost2",
});

async function runSql(sql, params = []) {
  const r = await pool.query(sql, params);
  return r.rows ?? [];
}

async function runSqlRaw(sql) {
  const r = await pool.query(sql);
  return { rows: r.rows ?? [], rowCount: r.rowCount ?? 0 };
}

function mcpText(data) {
  return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
}

function mcpError(msg) {
  return { content: [{ type: "text", text: `Error: ${msg}` }], isError: true };
}

const APP_PORT = parseInt(process.env.PORT || "9002");
const SECRET_KEY = process.env.REMOTE_SECRET_KEY || "my-secret-key-123";

async function handleToolCall(name, args) {
  switch (name) {
    case "list_tables": {
      const rows = await runSql(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
      );
      return mcpText(rows.map((r) => r.table_name));
    }
    case "describe_table": {
      const rows = await runSql(
        `SELECT column_name, data_type, is_nullable, column_default
         FROM information_schema.columns
         WHERE table_schema='public' AND table_name=$1
         ORDER BY ordinal_position`,
        [args.table]
      );
      return mcpText(rows);
    }
    case "select": {
      const rows = await runSql(args.sql);
      return mcpText(rows);
    }
    case "insert": {
      const cols = Object.keys(args.data);
      const vals = Object.values(args.data);
      const ph = vals.map((_, i) => `$${i + 1}`).join(",");
      const sql = `INSERT INTO ${args.table} (${cols.join(",")}) VALUES (${ph}) RETURNING *`;
      const rows = await runSql(sql, vals);
      return mcpText(rows);
    }
    case "update": {
      const entries = Object.entries(args.set);
      const setClause = entries.map(([k, _], i) => `${k}=$${i + 1}`).join(",");
      const vals = entries.map(([_, v]) => v);
      const sql = `UPDATE ${args.table} SET ${setClause} WHERE ${args.where} RETURNING *`;
      const rows = await runSql(sql, vals);
      return mcpText(rows);
    }
    case "delete_rows": {
      const sql = `DELETE FROM ${args.table} WHERE ${args.where} RETURNING *`;
      const rows = await runSql(sql);
      return mcpText(rows);
    }
    case "create_table": {
      await runSql(args.sql);
      return mcpText("Table created");
    }
    case "add_column": {
      const sql = `ALTER TABLE ${args.table} ADD COLUMN ${args.column_def}`;
      await runSql(sql);
      return mcpText("Column added");
    }
    case "create_index": {
      const sql = `CREATE INDEX ON ${args.table} (${args.columns})`;
      await runSql(sql);
      return mcpText("Index created");
    }
    case "run_sql": {
      const r = await runSqlRaw(args.sql);
      return mcpText(r.rowCount > 0 ? { affected_rows: r.rowCount, rows: r.rows } : r.rows);
    }
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

async function getTableNames() {
  return await runSql(
    "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
  );
}

async function getTableColumns(table) {
  return await runSql(
    `SELECT column_name, data_type, is_nullable, column_default
     FROM information_schema.columns
     WHERE table_schema='public' AND table_name=$1
     ORDER BY ordinal_position`,
    [table]
  );
}

async function getTableSampleRows(table, limit = 5) {
  return await runSql(`SELECT * FROM ${table} LIMIT ${limit}`);
}

async function getTableCount(table) {
  const r = await runSql(`SELECT COUNT(*) AS cnt FROM ${table}`);
  return r[0]?.cnt ?? 0;
}

const mcpServer = new Server(
  { name: "PostgreSQL MCP Server", version: "1.0.0" },
  { capabilities: { tools: {}, resources: {}, prompts: {} } }
);

mcpServer.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    { name: "list_tables", description: "List all tables", inputSchema: { type: "object", properties: {}, required: [] } },
    { name: "describe_table", description: "Show columns of a table", inputSchema: { type: "object", properties: { table: { type: "string" } }, required: ["table"] } },
    { name: "select", description: "Run a SELECT query", inputSchema: { type: "object", properties: { sql: { type: "string" } }, required: ["sql"] } },
    { name: "insert", description: "Insert data into a table", inputSchema: { type: "object", properties: { table: { type: "string" }, data: { type: "object", additionalProperties: true } }, required: ["table", "data"] } },
    { name: "update", description: "Update rows", inputSchema: { type: "object", properties: { table: { type: "string" }, set: { type: "object", additionalProperties: true }, where: { type: "string" } }, required: ["table", "set", "where"] } },
    { name: "delete_rows", description: "Delete rows from a table", inputSchema: { type: "object", properties: { table: { type: "string" }, where: { type: "string" } }, required: ["table", "where"] } },
    { name: "create_table", description: "Create a new table", inputSchema: { type: "object", properties: { sql: { type: "string" } }, required: ["sql"] } },
    { name: "add_column", description: "Add a column to a table", inputSchema: { type: "object", properties: { table: { type: "string" }, column_def: { type: "string" } }, required: ["table", "column_def"] } },
    { name: "create_index", description: "Create an index on a table", inputSchema: { type: "object", properties: { table: { type: "string" }, columns: { type: "string" } }, required: ["table", "columns"] } },
    { name: "run_sql", description: "Run any SQL statement", inputSchema: { type: "object", properties: { sql: { type: "string" } }, required: ["sql"] } },
  ],
}));

mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    return await handleToolCall(request.params.name, request.params.arguments);
  } catch (err) {
    return mcpError(err.message);
  }
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

const app = express();
app.use(express.json());

app.post("/mcp", async (req, res) => {
  const auth = req.headers["authorization"];
  if (SECRET_KEY && (!auth || auth !== `Bearer ${SECRET_KEY}`)) {
    return res.status(401).json({ error: "Unauthorized" });
  }
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
  });
  res.on("close", () => {
    transport.close();
  });
  try {
    await mcpServer.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: "2.0",
        error: { code: -32603, message: error.message },
        id: null,
      });
    }
  }
});

app.listen(APP_PORT, () => {
  console.log(`PostgreSQL MCP Server on port ${APP_PORT}`);
  console.log(`http://localhost:${APP_PORT}/mcp`);
});
