Write-Host "=============================="
Write-Host "Starting MySQL MCP Server..."
Write-Host "=============================="

$env:MYSQL_HOST = "auth-db936.hstgr.io"
$env:MYSQL_PORT = "3306"
$env:MYSQL_USER = "u543957720_crypto"
$env:MYSQL_PASS = "REDACTED"
$env:MYSQL_DB = "u543957720_cryptoprice"
$env:IS_REMOTE_MCP = "true"
$env:REMOTE_SECRET_KEY = "REDACTED_KEY"
$env:PORT = "9001"

Start-Process -FilePath "C:\Program Files\nodejs\node.exe" -ArgumentList "C:\Users\valen\AppData\Roaming\npm\node_modules\@benborla29\mcp-server-mysql\dist\index.js" -WindowStyle Hidden

Start-Sleep -Seconds 2
Write-Host "MySQL MCP on http://localhost:9001/mcp"

Write-Host ""
Write-Host "=============================="
Write-Host "Starting PostgreSQL MCP Server (9002)..."
Write-Host "=============================="

$env:PG_HOST="localhost"
$env:PG_PORT="5432"
$env:PG_USER="postgres"
$env:PG_PASSWORD="REDACTED"
$env:PG_DATABASE="testPost2"
$env:PORT="9002"

Start-Process -FilePath "C:\Program Files\nodejs\node.exe" -ArgumentList "D:\n8n\MCP\pg-mcp-server\server.js" -WindowStyle Hidden

Start-Sleep -Seconds 2
Write-Host "PG MCP on http://localhost:9002/mcp"

Write-Host ""
Write-Host "=============================="
Write-Host "Starting n8n..."
Write-Host "=============================="

& "C:\Users\valen\AppData\Roaming\npm\n8n.cmd" start
