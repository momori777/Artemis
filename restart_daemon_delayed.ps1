param([int]$DelaySeconds = 5)
$ErrorActionPreference = "Continue"
$root = $PSScriptRoot
$log = Join-Path $root "restart_daemon_delayed.log"
function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Out-File -FilePath $log -Append -Encoding utf8 }
Log "restart task started (delay=$DelaySeconds)"
Start-Sleep -Seconds $DelaySeconds

# kill any leftover daemon instance
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'shiki_daemon\.py' } |
  ForEach-Object { Log "killing leftover daemon pid $($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

# wait for port 19260 to free
for ($i = 0; $i -lt 20; $i++) {
  if (-not (Get-NetTCPConnection -State Listen -LocalPort 19260 -ErrorAction SilentlyContinue)) { break }
  Start-Sleep -Seconds 1
}

# relaunch daemon; --no-llama: flash-next GGUF moved to Strata engine (8080),
# llama.cpp model path in config.yaml no longer exists, and loading both stacks
# at once would over-commit RAM.
$daemon = Join-Path $root "shiki_daemon.py"
Start-Process -FilePath "python" -ArgumentList "`"$daemon`"", '--no-llama' -WorkingDirectory $root -WindowStyle Hidden
Log "daemon launched, waiting for 19260..."

$ok = $false
for ($i = 0; $i -lt 60; $i++) {
  Start-Sleep -Seconds 2
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:19260/api/status" -TimeoutSec 3
    if ($r.StatusCode -eq 200) { $ok = $true; break }
  } catch {}
}
Log "daemon up: $ok"
schtasks /delete /tn ShikiDaemonRestart /f 2>&1 | Out-Null
Log "task self-deleted"
