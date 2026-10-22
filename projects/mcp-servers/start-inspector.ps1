# One-command launcher: clean stale instances, start pg-mcp-server,
# open MCP Inspector preconfigured to our server. All messages in ASCII
# (PowerShell 5.1 + UTF-8 issues). Runbook: see mcp_tutorial.md section 2.

$scriptDir = $PSScriptRoot
$serverScript = Join-Path $scriptDir 'start-pg-mcp-server.ps1'

# 1) stop stale instances ONLY (inspector + our server), never all node
$stale = Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
    Where-Object { $_.CommandLine -match '@modelcontextprotocol[/\\]inspector|mcp-inspector|pg-mcp-server\\server\.js' }
foreach ($pr in $stale) {
    Write-Host ("Closing stale instance PID " + $pr.ProcessId)
    Stop-Process -Id $pr.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 1

# 2) take Bearer token: prefer local secret file D:\AI\opencode-work\secrets\mcp.env (never committed); fallback: server script value
$tokenFile = Join-Path $env:USERPROFILE "mcp_token.env"
$token = ""
if (Test-Path $tokenFile) { foreach ($line in Get-Content $tokenFile) { if ($line -match '^\s*MCP_TOKEN=(.+)$') { $token = $Matches[1].Trim() } } }
if (-not $token) {
    $match = Select-String -Path $serverScript -Pattern 'REMOTE_SECRET_KEY="([^"]*)"'
    if ($match) { $token = $match.Matches[0].Groups[1].Value }
}

# 3) server env vars from same script, then start hidden
foreach ($kv in (Select-String -Path $serverScript -Pattern '\$env:([A-Z_]+)="([^"]*)"')) {
    Set-Item -Path ("env:" + $kv.Matches[0].Groups[1].Value) -Value $kv.Matches[0].Groups[2].Value
}
if ($token) { $env:REMOTE_SECRET_KEY = $token }
$server = Start-Process node -ArgumentList (Join-Path $scriptDir 'pg-mcp-server\server.js') -WindowStyle Hidden -PassThru
Write-Host ("pg-mcp-server started, PID " + $server.Id)

# 4) wait for port 9002
$ok = $false
for ($i = 0; $i -lt 20; $i++) {
    if (Get-NetTCPConnection -LocalPort 9002 -State Listen -ErrorAction SilentlyContinue) { $ok = $true; break }
    Start-Sleep -Milliseconds 500
}
if ($ok) {
    Write-Host "Server is up: http://localhost:9002/mcp"
} else {
    Write-Host "WARNING: port 9002 did not open - check node errors"
    Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# 5) run inspector, browser opens itself; on exit stop the server
try {
    Write-Host "Opening MCP Inspector (browser gets preconfigured server). Fallback URL: http://localhost:6274"
    $headerArg = '"Authorization: Bearer ' + $token + '"'
    npx.cmd -y "@modelcontextprotocol/inspector@latest" --transport http --server-url "http://localhost:9002/mcp" --header $headerArg
}
finally {
    Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Server stopped."
}

