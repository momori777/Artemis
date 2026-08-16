# stop-claude-code-ccr.ps1 - Stop Claude Code session services (task board + CCR)
# ==================================================================================
# Stops the visual task board (started by claude-code-ccr.ps1) and, optionally, CCR.
# Reads ports from config.yaml (no hardcoding).
#
# Note: the Claude Code process itself is foreground/interactive; close it with Ctrl+C
#       or its own /exit command. This script only manages the sidecar services.
#
# Usage:
#   .\stop-claude-code-ccr.ps1          # stop task board only
#   .\stop-claude-code-ccr.ps1 -All     # also stop CCR gateway

param(
    [switch]$All = $false
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8

$projectRoot = $PSScriptRoot
$configPath = Join-Path $projectRoot "config.yaml"

function Get-YamlValue([string]$raw, [string]$key) {
    $pattern = '(?m)^\s*' + [regex]::Escape($key) + '\s*:\s*"?([^"\r\n]*)"?'
    $m = [regex]::Match($raw, $pattern)
    if ($m.Success) { return $m.Groups[1].Value.Trim('"').Trim() }
    return $null
}

$BoardPort = 19280
if (Test-Path $configPath) {
    $cfgRaw = Get-Content $configPath -Raw -Encoding UTF8
    $b = Get-YamlValue $cfgRaw 'task_board_port'; if ($b) { $BoardPort = $b }
}

Write-Host "=== Stop Claude Code sidecar services ===" -ForegroundColor Cyan

# Stop task board (match by command line to avoid killing unrelated python)
$board = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'task_board_api\.py' }
if ($board) {
    foreach ($p in $board) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "  stopped task board (PID $($p.ProcessId))" -ForegroundColor Yellow
    }
} else {
    Write-Host "  task board not running" -ForegroundColor Gray
}

# Optionally stop CCR
if ($All) {
    $ccrStop = Join-Path $projectRoot "skills\ccr\stop-ccr.ps1"
    if (Test-Path $ccrStop) {
        Write-Host ""
        & $ccrStop
    } else {
        Write-Host "  [WARN] stop-ccr.ps1 not found: $ccrStop" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Done. Claude Code itself: use /exit or Ctrl+C in its terminal." -ForegroundColor Green
