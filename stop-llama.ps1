# ============================================================
# stop-llama.ps1 — 停止 llama-server
# 用法: .\stop-llama.ps1
# ============================================================

$port = 8080

Write-Host "Stopping llama-server (port $port)..." -ForegroundColor Yellow

# Graceful shutdown
curl.exe -s -X POST "http://127.0.0.1:${port}/shutdown" --connect-timeout 3 2>$null | Out-Null
Start-Sleep -Seconds 2

# Force kill
taskkill /f /im llama-server.exe 2>$null | Out-Null

Write-Host "Done." -ForegroundColor Green
