# MCP Servers вЂ” Р·Р°РїСѓСЃРє Рё С‚РµСЃС‚ (runbook)

РљРѕРјРїРѕРЅРµРЅС‚С‹:
- `pg-mcp-server/` вЂ” РЅР°С€ Node.js СЃРµСЂРІРµСЂ Рє PostgreSQL (РїРѕСЂС‚ 9002)
- `start-mysql-mcp-server.ps1` вЂ” РєРѕСЂРѕР±РѕС‡РЅС‹Р№ npm-РїР°РєРµС‚ Рє MySQL (РїРѕСЂС‚ 9001)

---

## РЁРђР“ 1. Р—Р°РїСѓСЃС‚РёС‚СЊ СЃРµСЂРІРµСЂ + РёРЅСЃРїРµРєС‚РѕСЂ РѕРґРЅРѕР№ РєРѕРјР°РЅРґРѕР№ (СЂРµРєРѕРјРµРЅРґСѓРµС‚СЃСЏ)

РћС‚РєСЂРѕР№ PowerShell Рё РІС‹РїРѕР»РЅРё РґРІРµ СЃС‚СЂРѕРєРё:

```powershell
cd <repo>\projects\mcp-servers
.\start-inspector.ps1
```

РћР±СЏР·Р°С‚РµР»СЊРЅРѕ РґРѕР¶РґРёСЃСЊ СЃС‚СЂРѕРє:

```
pg-mcp-server started, PID ...
Server is up: http://localhost:9002/mcp
Opening MCP Inspector ...
```

Р­С‚Рѕ РѕРєРЅРѕ РќР• Р·Р°РєСЂС‹РІР°Р№ (РІ РЅС‘Рј РєСЂСѓС‚РёС‚СЃСЏ СЃРµСЂРІРµСЂ; СЃРІРµСЂРЅСѓР» вЂ” РЅРµ СЃС‚СЂР°С€РЅРѕ).

Р‘СЂР°СѓР·РµСЂ РѕС‚РєСЂРѕРµС‚СЃСЏ СЃР°Рј СЃ MCP Inspector, РЅР°С€ СЃРµСЂРІРµСЂ СѓР¶Рµ РІС‹Р±СЂР°РЅ.

Р’ Р±СЂР°СѓР·РµСЂРµ:
1. **Connect**
2. РІРєР»Р°РґРєР° **Tools** в†’ **List Tools** вЂ” СѓРІРёРґРёС€СЊ 10 РёРЅСЃС‚СЂСѓРјРµРЅС‚РѕРІ
3. `list_tables` в†’ **Run** в†’ СЃРїРёСЃРѕРє С‚Р°Р±Р»РёС†
4. `select` в†’ SQL `SELECT COUNT(*) FROM leads_leads` в†’ **Run** в†’ С‡РёСЃР»Рѕ

Р—Р°РІРµСЂС€РµРЅРёРµ: РІРµСЂРЅРёСЃСЊ РІ РѕРєРЅРѕ PowerShell, РЅР°Р¶РјРё `Ctrl+C` вЂ” СЃРєСЂРёРїС‚ РѕСЃС‚Р°РЅРѕРІРёС‚ СЃРµСЂРІРµСЂ.

Р•СЃР»Рё Р±СЂР°СѓР·РµСЂ РЅРµ РѕС‚РєСЂС‹Р»СЃСЏ СЃР°Рј: РѕС‚РєСЂРѕР№ РІСЂСѓС‡РЅСѓСЋ `http://localhost:6274`
(Рё РІ UI: Transport = Streamable HTTP, URL = http://localhost:9002/mcp,
Header: `Authorization` = `Bearer <С‚РѕРєРµРЅ РёР· start-pg-mcp-server.ps1>`, РґР°Р»РµРµ Connect).

---

## РЁРђР“ 2. Р’Р°СЂРёР°РЅС‚ СЂСѓРєР°РјРё: СЃРµСЂРІРµСЂ РѕС‚РґРµР»СЊРЅРѕ, РёРЅСЃРїРµРєС‚РѕСЂ РѕС‚РґРµР»СЊРЅРѕ

РўРµСЂРјРёРЅР°Р» СЃРµСЂРІРµСЂР° (РќР• Р·Р°РєСЂС‹РІР°С‚СЊ):
```powershell
cd <repo>\projects\mcp-servers
.\start-pg-mcp-server.ps1
```
РЈСЃРїРµС… = Р±Р°РЅРЅРµСЂ В«PostgreSQL MCP Server / URL: http://localhost:9002/mcpВ».

РўРµСЂРјРёРЅР°Р» РёРЅСЃРїРµРєС‚РѕСЂР°:
```powershell
npx @modelcontextprotocol/inspector@latest --transport http --server-url http://localhost:9002/mcp --header "Authorization: Bearer <С‚РѕРєРµРЅ РёР· СЃРєСЂРёРїС‚Р° СЃРµСЂРІРµСЂР°>"
```
(С‚РѕРєРµРЅ РІР·СЏС‚СЊ РёР· `start-pg-mcp-server.ps1`, СЃС‚СЂРѕРєР° REMOTE_SECRET_KEY)

РџРѕСЃР»Рµ СѓСЃС‚Р°РЅРѕРІРєРё Р·Р°РІРёСЃРёРјРѕСЃС‚РµР№ СЃРµСЂРІРµСЂР° (РѕРґРёРЅ СЂР°Р·):
```powershell
cd <repo>\projects\mcp-servers\pg-mcp-server
npm install
```

---

## РЁРђР“ 3. РџСЂРѕРІРµСЂРєР° Р¶РёРІРѕСЃС‚Рё Р±РµР· Р±СЂР°СѓР·РµСЂР° (СЃРµСЂРІРµСЂ РёР· РЁРђР“Рђ 2 РµС‰С‘ СЂР°Р±РѕС‚Р°РµС‚)

Р’ Р»СЋР±РѕРј РЅРѕРІРѕРј РѕРєРЅРµ (РїР°РїРєР° РЅРµ РІР°Р¶РЅР°):
```powershell
Invoke-RestMethod -Uri http://localhost:9002/mcp -Method Post `
  -ContentType "application/json" `
  -Headers @{ Accept = "application/json, text/event-stream" } `
  -Body '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}'
```
РћС‚РІРµС‚ JSON вЂ” СЃРµСЂРІРµСЂ Р¶РёРІ.

---

## РЁРђР“ 4. MySQL MCP (РіРѕС‚РѕРІС‹Р№ РїР°РєРµС‚, РїРѕ Р¶РµР»Р°РЅРёСЋ)

```powershell
cd <repo>\projects\mcp-servers
.\start-mysql-mcp-server.ps1
```
Р­РЅРґРїРѕРёРЅС‚: `POST http://localhost:9001/mcp`.
РљРѕРЅРЅРµРєС‚ Рє Р‘Р” вЂ” РїРµСЂРµРјРµРЅРЅС‹Рµ РѕРєСЂСѓР¶РµРЅРёСЏ РІ СЃРєСЂРёРїС‚Рµ (MYSQL_HOST/USER/PASS/DB), Р·Р°РїРѕР»РЅРёС‚СЊ РѕРґРёРЅ СЂР°Р·.
Р’ РёРЅСЃРїРµРєС‚РѕСЂРµ: С‚Рѕ Р¶Рµ СЃР°РјРѕРµ, С‚РѕР»СЊРєРѕ URL `http://localhost:9001/mcp`.

---

## РЁРђР“ 5. РџРѕРґРєР»СЋС‡РёС‚СЊ Рє Р°РіРµРЅС‚Сѓ РІ n8n

Р’ РІРѕСЂРєС„Р»РѕСѓ: **AI Agent** в†’ СЃРЅРёР·Сѓ РїРѕР»Рµ РёРЅСЃС‚СЂСѓРјРµРЅС‚РѕРІ в†’ **MCP Client**:

| РџР°СЂР°РјРµС‚СЂ | Р—РЅР°С‡РµРЅРёРµ |
|----------|----------|
| Server Transport | `Streamable HTTP` |
| Endpoint | `http://localhost:9002/mcp` |
| Additional Headers | `Authorization: Bearer <С‚РѕРєРµРЅ>` |

Р’ С‡Р°С‚ Р°РіРµРЅС‚Сѓ: В«РїРѕРєР°Р¶Рё С‚Р°Р±Р»РёС†С‹В» / В«СЃРєРѕР»СЊРєРѕ Р»РёРґРѕРІВ» вЂ” Р°РіРµРЅС‚ СЃР°Рј РІС‹Р±РµСЂРµС‚ tool.
РџСЂРёРјРµСЂ РІРѕСЂРєС„Р»РѕСѓ: `MySQL-MCP.json` РІ СЌС‚РѕР№ РїР°РїРєРµ (Chat Trigger в†’ AI Agent в†’ MCP Client).
