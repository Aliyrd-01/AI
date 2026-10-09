@echo off
echo ==============================
echo Starting MySQL MCP Server...
echo ==============================
start /B "" "C:\Program Files\nodejs\node.exe" "C:\Users\valen\AppData\Roaming\npm\node_modules\@benborla29\mcp-server-mysql\dist\index.js"
timeout /t 3 /nobreak >nul
echo MCP Server on http://localhost:9001/mcp
echo.
echo ==============================
echo Starting n8n...
echo ==============================
call "C:\Users\valen\AppData\Roaming\npm\n8n.cmd" start
