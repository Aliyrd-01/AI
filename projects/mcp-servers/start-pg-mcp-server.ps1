Write-Host "Stopping old PG MCP server..."
$conn = Get-NetTCPConnection -LocalPort 9002 -ErrorAction SilentlyContinue
if ($conn) { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1

$env:PG_HOST="localhost"
$env:PG_PORT="5432"
$env:PG_USER="postgres"
$env:PG_PASSWORD="REDACTED"
$env:PG_DATABASE="testPost2"

# local-only secret: MCP_TOKEN in a user-home env file (never committed)
$tokenFile = Join-Path $env:USERPROFILE "mcp_token.env"
$secret = "REDACTED_KEY"
if (Test-Path $tokenFile) { foreach ($line in Get-Content $tokenFile) { if ($line -match '^\s*MCP_TOKEN=(.+)$') { $secret = $Matches[1].Trim() } } }
$env:REMOTE_SECRET_KEY = $secret
$env:PORT="9002"

Write-Host "=============================="
Write-Host "PostgreSQL MCP Server"
Write-Host "URL: http://localhost:9002/mcp"
Write-Host "Auth: Bearer REDACTED_KEY"
Write-Host "=============================="
Write-Host ""

node "$PSScriptRoot\pg-mcp-server\server.js"

