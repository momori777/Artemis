# Keeps shiki_daemon.py (ports 19260 chat API / 19270 WebChat) alive.
# Started by scheduled task "ShikiDaemonWatchdog" every 5 minutes.
# NOTE: llama.cpp lives on 9931; 8080 belongs to the Strata engine.
# This script never touches 8080 and never launches llama.cpp (--no-llama),
# so it cannot evict/over-commit the Strata stack.
$ErrorActionPreference = "Continue"
$log = "E:\AI_Girlfriend\daemon_watchdog.log"
function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Out-File -FilePath $log -Append -Encoding utf8 }

if (Get-NetTCPConnection -State Listen -LocalPort 19260 -ErrorAction SilentlyContinue) {
    exit 0
}

Log "19260 not listening; launching daemon"
Start-Process -FilePath "python" `
    -ArgumentList '"E:\AI_Girlfriend\shiki_daemon.py"', '--no-llama' `
    -WorkingDirectory "E:\AI_Girlfriend" -WindowStyle Hidden

for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:19260/api/status" -TimeoutSec 3
        if ($r.StatusCode -eq 200) { Log "daemon up"; exit 0 }
    } catch {}
}
Log "daemon failed to come up"
