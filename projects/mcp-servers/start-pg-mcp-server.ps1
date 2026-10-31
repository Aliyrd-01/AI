Write-Host "Stopping old PG MCP server..."
$conn = Get-NetTCPConnection -LocalPort 9002 -ErrorAction SilentlyContinue
if ($conn) { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1

$env:PG_HOST = if ($env:PG_HOST) { $env:PG_HOST } else { "localhost" }
$env:PG_PORT = if ($env:PG_PORT) { $env:PG_PORT } else { "5432" }
$env:PG_USER = if ($env:PG_USER) { $env:PG_USER } else { "postgres" }
$env:PG_DATABASE = if ($env:PG_DATABASE) { $env:PG_DATABASE } else { "testPost2" }

if (-not $env:PG_PASSWORD) {
    Write-Warning "PG_PASSWORD is not set. Please set PG_PASSWORD before running in production."
}

# local-only secret: MCP_TOKEN in a user-home env file (never committed)
$tokenFile = Join-Path $env:USERPROFILE "mcp_token.env"
if (-not $env:REMOTE_SECRET_KEY -and (Test-Path $tokenFile)) {
    foreach ($line in Get-Content $tokenFile) {
        if ($line -match '^\s*MCP_TOKEN=(.+)$') { $env:REMOTE_SECRET_KEY = $Matches[1].Trim() }
    }
}
if (-not $env:REMOTE_SECRET_KEY) {
    Write-Warning "REMOTE_SECRET_KEY is not set. MCP requests without token will be rejected (fail-closed)."
}
$env:PORT = if ($env:PORT) { $env:PORT } else { "9002" }

Write-Host "=============================="
Write-Host "PostgreSQL MCP Server"
Write-Host "URL: http://localhost:9002/mcp"
Write-Host "Auth: Bearer (configured via REMOTE_SECRET_KEY)"
Write-Host "=============================="
Write-Host ""

node "$PSScriptRoot\pg-mcp-server\server.js"

