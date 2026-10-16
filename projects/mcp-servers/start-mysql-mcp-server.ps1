$env:MYSQL_PORT = "3306"
$env:IS_REMOTE_MCP = "true"
$env:PORT = "9001"

Write-Host "======================================"
Write-Host "MySQL MCP Server (HTTP mode)"
Write-Host "URL: http://localhost:9001/mcp"
Write-Host "Auth: set REMOTE_SECRET_KEY (empty = auth disabled)"
Write-Host "======================================"
Write-Host ""

& npx.cmd -y "@benborla29/mcp-server-mysql"
