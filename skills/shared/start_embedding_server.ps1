powershell -ExecutionPolicy Bypass -Command "
# Start OpenClaw Embedding Server (all-MiniLM-L6-v2, port 9999)
# Runs in background, does NOT kill llama-server
$pythonExe = (Get-Command python -ErrorAction Stop).Source
$scriptPath = Join-Path $env:USERPROFILE '.openclaw\workspace\skills\shared\embedding_server.py'

try {
    $response = Invoke-WebRequest -Uri 'http://127.0.0.1:9999/health' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    Write-Host '[embed] Server already running'
} catch {
    Write-Host '[embed] Starting embedding server on port 9999...'
    Start-Process -FilePath $pythonExe -ArgumentList $scriptPath -WindowStyle Hidden
    Start-Sleep -Seconds 3
    Write-Host '[embed] Server started'
}
"
