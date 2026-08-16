# claude-code-ccr.ps1 - Launch Claude Code through CCR (connect to local llama)
# ==============================================================================
# Ports are read from project-root config.yaml (no hardcoding).
# Depends on CCR gateway + Claude Code + Artemis MCP task board; does NOT start OpenClaw ports.
#
# MCP: Claude Code auto-loads the project `.mcp.json` (artemis stdio server) when
#      launched from the project root. The artemis server exposes the task queue
#      tools (getWorkspace/getNextTask/createTask/updateTaskStatus/reply/getTaskMessages)
#      plus Artemis capabilities (tts/comfyui/live2d/memory/asr/switch_character).
#      A visual task board (HTTP) is optionally started as well.
#
# Prereqs:
#   1. llama-server running (config.yaml llama_port / ccr_upstream_port)
#   2. CCR running (.\skills\ccr\start-ccr.ps1)
#   3. Claude Code installed; first launch approves the artemis MCP server once.
#
# Usage:
#   .\claude-code-ccr.ps1                          # interactive + start task board
#   .\claude-code-ccr.ps1 "draw me Natsume"        # with initial prompt
#   .\claude-code-ccr.ps1 -NoTaskBoard             # do NOT start the visual task board
#   .\claude-code-ccr.ps1 -NoCcrCheck              # skip CCR online check

param(
    [string]$Prompt = "",
    [switch]$NoTaskBoard = $false,
    [switch]$NoCcrCheck = $false
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8

# Project root + read ports from config.yaml
$projectRoot = $PSScriptRoot
$configPath = Join-Path $projectRoot "config.yaml"

function Get-YamlValue([string]$raw, [string]$key) {
    $pattern = '(?m)^\s*' + [regex]::Escape($key) + '\s*:\s*"?([^"\r\n]*)"?'
    $m = [regex]::Match($raw, $pattern)
    if ($m.Success) { return $m.Groups[1].Value.Trim('"').Trim() }
    return $null
}

$GwPort = 3456; $UpPort = 8080; $BoardPort = 19280
if (Test-Path $configPath) {
    $cfgRaw = Get-Content $configPath -Raw -Encoding UTF8
    $g = Get-YamlValue $cfgRaw 'ccr_port';           if ($g) { $GwPort    = $g }
    $u = Get-YamlValue $cfgRaw 'ccr_upstream_port';  if ($u) { $UpPort    = $u }
    $b = Get-YamlValue $cfgRaw 'task_board_port';    if ($b) { $BoardPort = $b }
}

# Check Claude Code
$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if (-not $claudeCmd) {
    Write-Host "[ERROR] claude command not found." -ForegroundColor Red
    Write-Host "  Install: npm install -g @anthropic-ai/claude-code" -ForegroundColor Yellow
    exit 1
}

Write-Host "=== Claude Code (via CCR) ===" -ForegroundColor Magenta
Write-Host "  project root: $projectRoot" -ForegroundColor Gray
Write-Host "  CCR gateway:  http://127.0.0.1:$GwPort  (upstream llama http://127.0.0.1:$UpPort/v1)" -ForegroundColor Gray
Write-Host "  MCP server:   artemis (.mcp.json, auto-loaded)" -ForegroundColor Gray
Write-Host ""

# Start visual task board (optional)
if (-not $NoTaskBoard) {
    $boardScript = Join-Path $projectRoot ".claude\task_board_api.py"
    $boardOnline = $false
    try {
        $c = New-Object System.Net.Sockets.TcpClient("127.0.0.1", $BoardPort)
        $c.Close(); $boardOnline = $true
    } catch {}

    if ($boardOnline) {
        Write-Host "  [OK] Task board already online (:${BoardPort})" -ForegroundColor Green
    } elseif (Test-Path $boardScript) {
        $env:ARTEMIS_TASK_PORT = "$BoardPort"
        Start-Process python -ArgumentList $boardScript -WindowStyle Hidden
        Write-Host "  [OK] Task board started: http://127.0.0.1:$BoardPort" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Task board script not found: $boardScript" -ForegroundColor Yellow
    }
}

# Check CCR gateway online (skippable)
if (-not $NoCcrCheck) {
    $online = $false
    try {
        $c = New-Object System.Net.Sockets.TcpClient("127.0.0.1", $GwPort)
        $c.Close(); $online = $true
    } catch {}

    if ($online) {
        Write-Host "  [OK] CCR gateway online (:${GwPort})" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] CCR gateway not responding (:${GwPort})" -ForegroundColor Yellow
        Write-Host "         run .\skills\ccr\start-ccr.ps1 first" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Launch Claude Code (via CCR; Artemis MCP auto-loads from .mcp.json)
Push-Location $projectRoot
try {
    if ($Prompt) {
        claude -p $Prompt
    } else {
        claude
    }
} finally {
    Pop-Location
}
