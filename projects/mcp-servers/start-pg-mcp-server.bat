@echo off
echo ==============================
echo Starting PostgreSQL MCP Server (9002)...
echo ==============================
set PG_HOST=localhost
set PG_PORT=5432
set PG_USER=postgres
set PG_PASSWORD=
set PG_DATABASE=testPost2
set REMOTE_SECRET_KEY=
set PORT=9002
start /B "" node "%~dp0pg-mcp-server\server.js"
timeout /t 3 /nobreak >nul
echo.
echo PG MCP on http://localhost:9002/mcp
echo Auth: set REMOTE_SECRET_KEY (empty = auth disabled)
echo Close this window to stop the server.
echo.
pause
