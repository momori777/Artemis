# start-ccr.ps1 - Start CCR (Claude Code Router)
# =================================================
# Reads ports from project-root config.yaml (no hardcoding).
# ccr start reuses any running service (writes service.json), so it is safe to run repeatedly.
#
# Usage:
#   .\skills\ccr\start-ccr.ps1
#   .\skills\ccr\start-ccr.ps1 -NoGateway   # management UI only, do not start the model gateway

param(
    [switch]$NoGateway = $false
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8

# Locate project root + read config.yaml
$scriptRoot = $PSScriptRoot
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptRoot)
$configPath = Join-Path $projectRoot "config.yaml"

function Get-YamlValue([string]$raw, [string]$key) {
    $pattern = '(?m)^\s*' + [regex]::Escape($key) + '\s*:\s*"?([^"\r\n]*)"?'
    $m = [regex]::Match($raw, $pattern)
    if ($m.Success) { return $m.Groups[1].Value.Trim('"').Trim() }
    return $null
}

if (-not (Test-Path $configPath)) {
    Write-Host "[ERROR] config.yaml not found: $configPath" -ForegroundColor Red
    exit 1
}
$cfgRaw = Get-Content $configPath -Raw -Encoding UTF8

# Ports from config.yaml, falling back to CCR defaults
$WebPort = Get-YamlValue $cfgRaw 'ccr_web_port';       if (-not $WebPort) { $WebPort = 3458 }
$GwPort  = Get-YamlValue $cfgRaw 'ccr_port';           if (-not $GwPort)  { $GwPort  = 3456 }
$UpPort  = Get-YamlValue $cfgRaw 'ccr_upstream_port';  if (-not $UpPort)  { $UpPort  = 8080 }

# Check ccr command
$ccrCmd = Get-Command ccr -ErrorAction SilentlyContinue
if (-not $ccrCmd) {
    Write-Host "[ERROR] ccr command not found." -ForegroundColor Red
    Write-Host "  Install: npm install -g @musistudio/claude-code-router" -ForegroundColor Yellow
    exit 1
}

Write-Host "=== CCR start ===" -ForegroundColor Cyan
Write-Host "  project root: $projectRoot" -ForegroundColor Gray
Write-Host "  gateway port: $GwPort (upstream llama: $UpPort)" -ForegroundColor Gray
Write-Host "  web port:     $WebPort" -ForegroundColor Gray
Write-Host ""

# Start (ccr start reuses existing service)
$args = @("start", "--host", "127.0.0.1", "--port", "$WebPort", "--no-open")
if ($NoGateway) { $args += "--no-gateway" }

& $ccrCmd.Source @args

Write-Host ""
Write-Host "CCR started." -ForegroundColor Green
Write-Host "  management UI: http://127.0.0.1:$WebPort" -ForegroundColor Cyan
Write-Host "  model gateway: http://127.0.0.1:$GwPort  (upstream http://127.0.0.1:$UpPort/v1)" -ForegroundColor Cyan
