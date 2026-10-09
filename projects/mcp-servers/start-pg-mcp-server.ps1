Write-Host "Stopping old PG MCP server..."
Get-Process -Id (Get-NetTCPConnection -LocalPort 9002 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

$env:PG_HOST="localhost"
$env:PG_PORT="5432"
$env:PG_USER="postgres"
$env:PG_PASSWORD="REDACTED"
$env:PG_DATABASE="testPost2"
$env:REMOTE_SECRET_KEY="REDACTED_KEY"
$env:PORT="9002"

Write-Host "=============================="
Write-Host "PostgreSQL MCP Server"
Write-Host "URL: http://localhost:9002/mcp"
Write-Host "Auth: Bearer REDACTED_KEY"
Write-Host "=============================="
Write-Host ""

node "D:\n8n\MCP\pg-mcp-server\server.js"
