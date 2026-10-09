@echo off
echo ==============================
echo Starting PostgreSQL MCP Server (9002)...
echo ==============================
set PG_HOST=localhost
set PG_PORT=5432
set PG_USER=postgres
set PG_PASSWORD=12qwerty12
set PG_DATABASE=testPost2
set REMOTE_SECRET_KEY=my-secret-key-123
set PORT=9002
start /B "" "C:\Program Files\nodejs\node.exe" "D:\n8n\MCP\pg-mcp-server\server.js"
timeout /t 3 /nobreak >nul
echo.
echo PG MCP on http://localhost:9002/mcp
echo Auth: Bearer REDACTED_KEY
echo Close this window to stop the server.
echo.
pause
