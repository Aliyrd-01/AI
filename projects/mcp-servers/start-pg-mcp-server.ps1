Write-Host "Stopping old PG MCP server..."
$conn = Get-NetTCPConnection -LocalPort 9002 -ErrorAction SilentlyContinue
if ($conn) { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1

$env:PG_HOST = if ($env:PG_HOST) { $env:PG_HOST } else { "localhost" }
$env:PG_PORT = if ($env:PG_PORT) { $env:PG_PORT } else { "5432" }
# Роль только для чтения: без SUPERUSER, чтобы нельзя было прочитать pg_shadow
# и файлы хоста БД. Создаётся скриптом pg-mcp-server\db\roles\01_create_mcp_ro.sql.
$env:PG_USER = if ($env:PG_USER) { $env:PG_USER } else { "mcp_ro" }
$env:PG_DATABASE = if ($env:PG_DATABASE) { $env:PG_DATABASE } else { "testPost2" }

# local-only secret: пароль роли mcp_ro в файле вне репозитория
$dbEnvFile = Join-Path $env:USERPROFILE "mcp_db.env"
if (-not $env:PG_PASSWORD -and (Test-Path $dbEnvFile)) {
    foreach ($line in Get-Content $dbEnvFile) {
        if ($line -match '^\s*PG_PASSWORD=(.+)$') { $env:PG_PASSWORD = $Matches[1].Trim() }
    }
}

if (-not $env:PG_PASSWORD) {
    Write-Warning "PG_PASSWORD is not set (and not found in $dbEnvFile). Задайте пароль роли mcp_ro перед запуском."
}

# Read-only не мешает чтению: под суперпользователем остаются доступны
# pg_shadow и pg_read_file. Если PG_USER пришёл из окружения как postgres —
# это почти наверняка забытая переменная из старого окна.
if ($env:PG_USER -eq "postgres" -and $env:READ_ONLY -ne "0") {
    Write-Warning "PG_USER=postgres (SUPERUSER) в read-only режиме: pg_shadow и pg_read_file останутся доступны."
    Write-Warning "Уберите переменную из окна (Remove-Item Env:\PG_USER), чтобы скрипт взял mcp_ro."
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

