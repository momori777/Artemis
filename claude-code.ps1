# Artemis Claude Code Launcher + Task Board
# ============================================
# Launches Claude Code with Artemis AI Girlfriend integration.
# Also starts the Task Board API (port 19280) if not running.
#
# Prerequisites:
#   1. Install Claude Code: npm install -g @anthropic-ai/claude-code
#   2. Start Shiki Daemon first: .\shiki.cmd
#
# Usage:
#   .\claude-code.ps1                    — Launch Claude Code (task loop mode)
#   .\claude-code.ps1 "draw me Natsume"  — Launch with initial prompt
#   .\claude-code.ps1 -BoardOnly         — Start task Board only (no Claude)
#   .\claude-code.ps1 -KillBoard         — Stop task Board API

param(
    [string]$Prompt = "",
    [switch]$BoardOnly = $false,
    [switch]$KillBoard = $false
)

$ErrorActionPreference = "Stop"
$BoardPort = 19280

function Start-TaskBoard {
    $existing = Get-NetTCPConnection -LocalPort $BoardPort -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "  ✅ Task Board already running on :$BoardPort" -ForegroundColor Green
        Write-Host "     Open: http://127.0.0.1:$BoardPort" -ForegroundColor Cyan
        return
    }
    Write-Host "  🚀 Starting Task Board API on :$BoardPort..." -ForegroundColor Magenta
    $apiScript = Join-Path $PSScriptRoot ".claude\task_board_api.py"
    Start-Process python -ArgumentList $apiScript -WindowStyle Hidden
    Start-Sleep -Seconds 1
    Write-Host "  ✅ Task Board: http://127.0.0.1:$BoardPort" -ForegroundColor Green
}

function Stop-TaskBoard {
    $procs = Get-WmiObject Win32_Process -Filter "CommandLine LIKE '%task_board_api.py%'" -ErrorAction SilentlyContinue
    if ($procs) {
        foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
        Write-Host "  🛑 Task Board stopped" -ForegroundColor Yellow
    } else {
        Write-Host "  ⚪ Task Board not running" -ForegroundColor DarkGray
    }
}

Write-Host "🌸 Artemis × Claude Code" -ForegroundColor Magenta
Write-Host "=========================" -ForegroundColor DarkGray
Write-Host ""

if ($KillBoard) {
    Stop-TaskBoard
    exit 0
}

if ($BoardOnly) {
    Start-TaskBoard
    # Open browser
    Start-Process "http://127.0.0.1:$BoardPort"
    exit 0
}

# Verify Claude Code
$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if (-not $claudeCmd) {
    Write-Host "❌ Claude Code not found!" -ForegroundColor Red
    Write-Host "   Install: npm install -g @anthropic-ai/claude-code" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Claude Code found: $($claudeCmd.Source)" -ForegroundColor Green

# Check services
$ports = @{
    "llama" = 8080
    "live2d" = 19200
    "artemis_bridge" = 19250
    "webchat" = 19270
}
Write-Host ""
Write-Host "📡 Service Status:" -ForegroundColor Cyan
foreach ($name in $ports.Keys) {
    $port = $ports[$name]
    try {
        $c = New-Object System.Net.Sockets.TcpClient("127.0.0.1", $port)
        $c.Close()
        Write-Host "  ✅ $name (:$port)" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️ $name (:$port) — OFFLINE" -ForegroundColor Yellow
    }
}

# Start Task Board
Write-Host ""
Start-TaskBoard

Write-Host ""
$PROJECT_DIR = $PSScriptRoot
Write-Host "📂 Project: $PROJECT_DIR" -ForegroundColor Cyan
Write-Host "🧩 MCP tools: 14 total (8 Artemis + 6 Task Queue)" -ForegroundColor DarkGray
Write-Host "🔄 Task loop: getNextTask → ongoing → execute → reply → completed" -ForegroundColor DarkGray
Write-Host ""

# Launch Claude Code
Push-Location $PROJECT_DIR
try {
    if ($Prompt) {
        Write-Host "🚀 Launching Claude Code with prompt..." -ForegroundColor Magenta
        claude --dangerously-load-development-channels server:artemis -p $Prompt
    } else {
        Write-Host "🚀 Launching Claude Code (task loop mode)..." -ForegroundColor Magenta
        claude --dangerously-load-development-channels server:artemis
    }
} finally {
    Pop-Location
}
