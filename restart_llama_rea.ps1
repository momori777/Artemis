# restart_llama_rea.ps1 — Restart llama-server with -rea on/off
# Usage: restart_llama_rea.ps1 <on|off> [llama_exe] [model_path] [log_dir]
param([string]$Mode = "auto",
      [string]$Exe = "",
      [string]$Model = "",
      [string]$LogDir = "")

$port = 8080

Write-Output "Switching llama to -rea $Mode"

# Kill existing
taskkill /f /im llama-server.exe 2>&1 | Out-Null

# Wait for port release
do {
    Start-Sleep -Seconds 1
    try { $null = Invoke-WebRequest -Uri "http://127.0.0.1:$port/health" -TimeoutSec 1 -UseBasicParsing } catch { break }
} while ($true)
Write-Output "Port $port released"

# Start llama
$args = @(
    "-m", $Model,
    "-c", "120000", "--flash-attn", "on",
    "-ctk", "q8_0", "-ctv", "q8_0",
    "--no-mmap", "--cpu-moe",
    "--batch-size", "2048", "--ubatch-size", "1024",
    "--threads", "24",
    "-rea", $Mode, "--reasoning-format", "deepseek", "--jinja",
    "--cache-ram", "3000",
    "--parallel", "1", "--kv-unified", "--no-mmap",
    "--port", "$port", "--timeout", "600"
)
$proc = Start-Process -FilePath $Exe -ArgumentList $args -WindowStyle Hidden -PassThru
Write-Output "Started llama PID=$($proc.Id) with -rea $Mode"

# Wait for ready
$waited = 0
do {
    Start-Sleep -Seconds 2
    $waited += 2
    if ($waited -gt 180) { Write-Output "TIMEOUT"; exit 1 }
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$port/health" -TimeoutSec 3 -UseBasicParsing
        if ($r.StatusCode -eq 200) { break }
    } catch {}
} while ($true)

Write-Output "DONE: -rea $Mode"
