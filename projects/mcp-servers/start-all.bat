@echo off
echo ==============================
echo Starting MySQL MCP Server...
echo ==============================
start /B "" npx.cmd -y "@benborla29/mcp-server-mysql"
timeout /t 3 /nobreak >nul
echo MCP Server on http://localhost:9001/mcp
echo.
echo ==============================
echo Starting n8n...
echo ==============================
call npx.cmd -y n8n start
