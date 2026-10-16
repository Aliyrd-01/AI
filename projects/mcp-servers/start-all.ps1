Write-Host "=============================="
Write-Host "Starting MySQL MCP Server..."
Write-Host "=============================="

$env:MYSQL_PORT = "3306"
$env:IS_REMOTE_MCP = "true"
$env:PORT = "9001"

Start-Process -FilePath "npx.cmd" -ArgumentList "-y","@benborla29/mcp-server-mysql" -WindowStyle Hidden

Start-Sleep -Seconds 2
Write-Host "MySQL MCP on http://localhost:9001/mcp"

Write-Host ""
Write-Host "=============================="
Write-Host "Starting PostgreSQL MCP Server (9002)..."
Write-Host "=============================="

$env:PG_HOST="localhost"
$env:PG_PORT="5432"
$env:PG_USER="postgres"
$env:PG_DATABASE="testPost2"
$env:PORT="9002"

Start-Process -FilePath "node" -ArgumentList "$PSScriptRoot\pg-mcp-server\server.js" -WindowStyle Hidden

Start-Sleep -Seconds 2
Write-Host "PG MCP on http://localhost:9002/mcp"

Write-Host ""
Write-Host "=============================="
Write-Host "Starting n8n..."
Write-Host "=============================="

& npx.cmd -y n8n start
