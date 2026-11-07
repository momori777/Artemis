# setup-dsh.ps1
# AI Girlfriend — DeepSeek Harness (dsh) 一键部署 (Windows PowerShell)
#
# dsh = DeepSeek 官方开源 agent harness（社区昵称「大肥鱼」），
# 与 OpenClaw / Claude Code 并列为本项目第三个 agent 运行时。
#
# 自动完成:
#   1. 检测 Node.js（dsh 需要 Node 24+）
#   2. npm 全局安装 @deepseek-ai/dsh（含原生依赖 allow-scripts）
#   3. 验证 dsh CLI
#   4. 打印角色演绎插件位置（benchmark_projects/ 下的 dsh-* 仓库）
#
# 用法:
#   powershell -ExecutionPolicy Bypass -File setup-dsh.ps1
#   powershell -ExecutionPolicy Bypass -File setup-dsh.ps1 -SkipInstall
#
# 启动:  dsh web   （或免安装: npx @deepseek-ai/dsh web）

param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  AI Girlfriend · DeepSeek Harness (dsh) 一键部署           ║" -ForegroundColor Cyan
Write-Host "║  第三个 Agent 运行时 · everything-is-a-plugin              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# --- 1. Node.js check (dsh requires Node >= 24) ---
$nodeMajor = 0
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeMajor = [int]((node -v) -replace 'v(\d+).*', '$1')
}
if ($nodeMajor -lt 24) {
    Write-Host "[!] Node.js 24+ required (found: $(if ($nodeMajor) { "v$nodeMajor" } else { 'none' })). Install from https://nodejs.org" -ForegroundColor Yellow
    exit 1
}
Write-Host "[ok] Node.js $(node -v)" -ForegroundColor Green

# --- 2. Global install ---
if (-not $SkipInstall) {
    Write-Host "[..] npm install -g @deepseek-ai/dsh (with allow-scripts for native deps)" -ForegroundColor Cyan
    npm install -g --allow-scripts=@deepseek-ai/dsh-subprocess-local,koffi,node-pty,@google/genai,protobufjs @deepseek-ai/dsh
    if ($LASTEXITCODE -ne 0) { Write-Host "[!] npm install failed" -ForegroundColor Red; exit 1 }
}

# --- 3. Verify ---
$dshCmd = Get-Command dsh -ErrorAction SilentlyContinue
if (-not $dshCmd) { Write-Host "[!] dsh not on PATH after install" -ForegroundColor Red; exit 1 }
Write-Host "[ok] dsh $(dsh --version 2>$null)  ($($dshCmd.Source))" -ForegroundColor Green

# --- 4. Plugin inventory (git-ignored clones) ---
$benchDir = Join-Path $ScriptDir "benchmark_projects"
$plugins = @('deepseek-harness','dsh-liketavern','dsh-nexttavern','dsh-agent-rp','dsh-familiar-memory','ProjectKaren','dafeiyu-character-cards')
Write-Host ""
Write-Host "本地 dsh 仓库 (benchmark_projects/，git-ignored):" -ForegroundColor Cyan
foreach ($p in $plugins) {
    $path = Join-Path $benchDir $p
    if (Test-Path $path) { Write-Host "  [x] $p" -ForegroundColor Green }
    else { Write-Host "  [ ] $p (未克隆: git clone --depth 1 https://github.com/<owner>/$p.git)" -ForegroundColor DarkGray }
}
Write-Host ""
Write-Host "启动 Web UI:  dsh web" -ForegroundColor Cyan
Write-Host "角色扮演插件生态综述: benchmark_projects/2026-11-07-dsh-roleplay-report.md" -ForegroundColor Cyan
Write-Host ""
