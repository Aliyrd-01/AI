@echo off
echo ==============================
echo Starting PostgreSQL MCP Server (9002)...
echo ==============================
set PG_HOST=localhost
set PG_PORT=5432
set PG_USER=postgres
set PG_PASSWORD=YOUR_PG_PASSWORD
set PG_DATABASE=testPost2
set REMOTE_SECRET_KEY=YOUR_MCP_TOKEN
set PORT=9002
start /B "" "C:\Program Files\nodejs\node.exe" "D:\n8n-local\MCP\pg-mcp-server\server.js"
timeout /t 3 /nobreak >nul
echo.
echo PG MCP on http://localhost:9002/mcp
echo Auth: Bearer REDACTED_KEY
echo Close this window to stop the server.
echo.
pause
