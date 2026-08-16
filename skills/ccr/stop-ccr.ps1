# stop-ccr.ps1 - Stop CCR (Claude Code Router)
# ==============================================
# Reads ports from project-root config.yaml (consistent with start-ccr.ps1).
# Prefers `ccr stop` for a clean shutdown; falls back to cleaning up stray serve/start processes.

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8

$scriptRoot = $PSScriptRoot
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptRoot)
$configPath = Join-Path $projectRoot "config.yaml"

function Get-YamlValue([string]$raw, [string]$key) {
    $pattern = '(?m)^\s*' + [regex]::Escape($key) + '\s*:\s*"?([^"\r\n]*)"?'
    $m = [regex]::Match($raw, $pattern)
    if ($m.Success) { return $m.Groups[1].Value.Trim('"').Trim() }
    return $null
}

$WebPort = 3458; $GwPort = 3456
if (Test-Path $configPath) {
    $cfgRaw = Get-Content $configPath -Raw -Encoding UTF8
    $w = Get-YamlValue $cfgRaw 'ccr_web_port'; if ($w) { $WebPort = $w }
    $g = Get-YamlValue $cfgRaw 'ccr_port';     if ($g) { $GwPort  = $g }
}

Write-Host "=== CCR stop ===" -ForegroundColor Cyan

# Preferred: official stop
$ccrCmd = Get-Command ccr -ErrorAction SilentlyContinue
if ($ccrCmd) {
    & $ccrCmd.Source stop 2>$null
    Start-Sleep -Seconds 2
}

# Fallback: clean up stray ccr serve/start processes (match command line precisely)
$lingering = Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'claude-code-router.*(serve|start)' }
if ($lingering) {
    foreach ($p in $lingering) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "  stopped stray CCR process (PID $($p.ProcessId))" -ForegroundColor Yellow
    }
} else {
    Write-Host "  no stray CCR process" -ForegroundColor Gray
}

# Confirm ports are released
Start-Sleep -Seconds 1
$left = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -in @($GwPort, $WebPort) }
if ($left) {
    Write-Host "[WARN] ports still in use: $($left.LocalPort -join ', ')" -ForegroundColor Yellow
} else {
    Write-Host "CCR stopped (ports $GwPort / $WebPort released)" -ForegroundColor Green
}
