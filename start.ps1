# start.ps1 — 一键启停全部 Shiki 服务
# Usage:
#   .\start.ps1       启动全部服务
#   .\start.ps1 -Stop  停止全部服务（等价于 shutdown_all.py）
#
# 启动顺序:
#   1. llama-server (从 config.yaml 读取路径, ngl=41 batch=1024/512)
#   2. Live2D Bridge (localhost:19200)
#   3. OpenClaw Gateway
#   4. 启用 llama-watchdog 计划任务（崩溃自动重启守护）
#
# Stop 模式:
#   1. 禁用 llama-watchdog（防止自动重启）
#   2. 调用 shutdown_all.py 停止所有进程

param([switch]$Stop)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8

$scriptRoot = $PSScriptRoot

# ========== Watchdog 计划任务管理 ==========
$watchdogTaskName = "AI_Girlfriend_llama_watchdog"

function Enable-Watchdog {
    try {
        $task = schtasks /query /tn $watchdogTaskName 2>$null
        if ($LASTEXITCODE -eq 0) {
            $state = schtasks /query /tn $watchdogTaskName /fo CSV | Select-Object -Skip 1 | ConvertFrom-Csv
            if ($state.Status -eq "Ready") {
                Write-Host "  llama-watchdog task already enabled" -ForegroundColor Green
                return
            }
            schtasks /change /tn $watchdogTaskName /enable | Out-Null
            Write-Host "  llama-watchdog task re-enabled" -ForegroundColor Green
        } else {
            Write-Host "  WARNING: llama-watchdog task not found ($watchdogTaskName)" -ForegroundColor Yellow
            Write-Host "  Create it with: schtasks /create /tn $watchdogTaskName /tr ... /sc minute /mo 10" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  WARNING: Could not manage watchdog task: $_" -ForegroundColor Yellow
    }
}

function Disable-Watchdog {
    try {
        $task = schtasks /query /tn $watchdogTaskName 2>$null
        if ($LASTEXITCODE -eq 0) {
            schtasks /change /tn $watchdogTaskName /disable | Out-Null
            Write-Host "  llama-watchdog task disabled (won't auto-restart)" -ForegroundColor Cyan
        }
    } catch {
        # silently ignore — task might not exist
    }
}

# ========== Stop mode ==========
if ($Stop) {
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  四季夏目 — Shutdown" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "[1/2] Disabling llama-watchdog..." -ForegroundColor Yellow
    Disable-Watchdog
    
    Write-Host "[2/2] Stopping all processes..." -ForegroundColor Yellow
    $shutdownScript = Join-Path $scriptRoot "shutdown_all.py"
    if (-not (Test-Path $shutdownScript)) {
        Write-Host "ERROR: shutdown_all.py not found at $shutdownScript" -ForegroundColor Red
        exit 1
    }
    # Resolve python exe (avoid file-association popup if 'python' missing from PATH)
    $pyExe = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $pyExe) { $pyExe = (Get-Command py -ErrorAction SilentlyContinue).Source }
    if (-not $pyExe) {
        Write-Host "ERROR: python not found in PATH" -ForegroundColor Red
        exit 1
    }
    & $pyExe $shutdownScript
    exit $LASTEXITCODE
}

# ========== 读取 config.yaml ==========
$configPath = Join-Path $scriptRoot "config.yaml"
if (-not (Test-Path $configPath)) {
    Write-Host "ERROR: config.yaml not found at $configPath" -ForegroundColor Red
    Write-Host "Run quick_setup.ps1 first, or copy config.example.yaml → config.yaml" -ForegroundColor Yellow
    exit 1
}
$configRaw = Get-Content $configPath -Raw -Encoding UTF8

function Get-YamlValue($raw, $key) {
    $pattern = "(?m)^\s*${key}\s*:\s*`"?(.+?)`"?\s*$"
    $m = [regex]::Match($raw, $pattern)
    if ($m.Success) { return $m.Groups[1].Value.Trim('"').Trim() }
    return $null
}

$llamaExe   = Get-YamlValue $configRaw 'llama_exe'
$llamaModel = Get-YamlValue $configRaw 'llama_model'
$llamaPort  = Get-YamlValue $configRaw 'llama_port'
if (-not $llamaPort) { $llamaPort = 8080 }
$llamaLogDir = Get-YamlValue $configRaw 'llama_log_dir'
$workspace  = Get-YamlValue $configRaw 'workspace'

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  四季夏目 — Shiki Natsume Startup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ========== 1. Llama Server ==========
Write-Host "[1/4] llama-server" -ForegroundColor Yellow

function Test-Online($port, $label) {
    try {
        $null = Invoke-WebRequest -Uri "http://127.0.0.1:${port}/health" -TimeoutSec 2 -UseBasicParsing
        Write-Host "  ${label} already online (port ${port})" -ForegroundColor Green
        return $true
    } catch {
        return $false
    }
}

if (Test-Online $llamaPort "llama-server") {
    # already up — skip
} else {
    # Validate paths
    if (-not (Test-Path $llamaExe)) {
        Write-Host "  ERROR: llama-server.exe not found: $llamaExe" -ForegroundColor Red
        Write-Host "  Check config.yaml → llama_exe" -ForegroundColor Yellow
        exit 1
    }
    if (-not (Test-Path $llamaModel)) {
        Write-Host "  ERROR: Model not found: $llamaModel" -ForegroundColor Red
        Write-Host "  Check config.yaml → llama_model" -ForegroundColor Yellow
        exit 1
    }

    Write-Host "  Starting llama-server (ngl=41, batch=1024/512)..."

    # Kill stale processes
    Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1

    $llamaArgs = @(
        '-m', $llamaModel,
        '-c', '120000',
        '--flash-attn', 'on',
        '-ctk', 'q8_0',
        '-ctv', 'q8_0',
        '-ngl', '41',
        '--cpu-moe',
        '--batch-size', '2048',
        '--ubatch-size', '1024',
        '--threads', '24',
        '--api-key', '123456',
        '-rea', 'off',
        '--jinja',
        '--cache-ram', '3000',
        '--parallel', '1',
        '--kv-unified',
        '--no-mmap',
        '--port', $llamaPort,
        '--timeout', '600'
    )

    # Redirect stderr to llama_log_dir for the Get-Content -Tail -Wait command
    $llamaErrLog = Join-Path $llamaLogDir "llama-err.log"
    $null = New-Item -ItemType Directory -Force -Path $llamaLogDir -ErrorAction SilentlyContinue
    $null = Start-Process -FilePath $llamaExe -ArgumentList $llamaArgs -WindowStyle Hidden `
        -RedirectStandardError $llamaErrLog

    # Wait for ready
    Write-Host "  Waiting for llama-server to load model..."
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $maxWait = 300
    $ready = $false
    while ($sw.Elapsed.TotalSeconds -lt $maxWait) {
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:${llamaPort}/health" -TimeoutSec 3 -UseBasicParsing
            if ($r.StatusCode -eq 200) {
                $took = [math]::Round($sw.Elapsed.TotalSeconds, 1)
                Write-Host "  llama-server ready! (${took}s)" -ForegroundColor Green
                $ready = $true
                break
            }
        } catch {}
        Start-Sleep -Seconds 2
    }
    if (-not $ready) {
        Write-Host "  WARNING: llama-server not responding after ${maxWait}s — continuing anyway" -ForegroundColor Yellow
    }
}

# ========== 2. Embedding Server (OpenClaw memory search) ==========
Write-Host "[2/5] Embedding Server" -ForegroundColor Yellow

$embedPort = 9999
$embedScript = Join-Path $scriptRoot "skills\shared\embedding_server.py"

if (Test-Online $embedPort "Embedding Server") {
    # already up
} else {
    if (-not (Test-Path $embedScript)) {
        Write-Host "  WARNING: embedding_server.py not found at $embedScript" -ForegroundColor Yellow
    } else {
        Write-Host "  Starting embedding server (all-MiniLM-L6-v2 on port ${embedPort})..."
        $pyExe = (Get-Command python -ErrorAction SilentlyContinue).Source
        if (-not $pyExe) { $pyExe = (Get-Command py -ErrorAction SilentlyContinue).Source }
        if (-not $pyExe) {
            Write-Host "  WARNING: python not found — skip embedding server" -ForegroundColor Yellow
        } else {
            $null = Start-Process -FilePath $pyExe -ArgumentList $embedScript -WindowStyle Hidden
            Start-Sleep -Seconds 3

            $swEmb = [Diagnostics.Stopwatch]::StartNew()
            $readyEmb = $false
            while ($swEmb.Elapsed.TotalSeconds -lt 45) {
                try {
                    $null = Invoke-WebRequest -Uri "http://127.0.0.1:${embedPort}/health" -TimeoutSec 3 -UseBasicParsing
                    Write-Host "  Embedding server ready! (port ${embedPort})" -ForegroundColor Green
                    $readyEmb = $true
                    break
                } catch {}
                Start-Sleep -Seconds 2
            }
            if (-not $readyEmb) {
                Write-Host "  WARNING: Embedding server not responding after 45s" -ForegroundColor Yellow
            }
        }
    }
}

# ========== 3. Live2D Bridge ==========
Write-Host "[3/5] Live2D Bridge" -ForegroundColor Yellow

if (Test-Online 19200 "Live2D Bridge") {
    # already up — skip
} else {
    $live2dDir = Join-Path $scriptRoot "live2d"
    if (-not (Test-Path (Join-Path $live2dDir "live2d-bridge.mjs"))) {
        Write-Host "  WARNING: live2d-bridge.mjs not found in $live2dDir" -ForegroundColor Yellow
    } else {
        Write-Host "  Starting Live2D Bridge..."
        $null = Start-Process -FilePath node -ArgumentList "live2d-bridge.mjs" -WorkingDirectory $live2dDir -WindowStyle Hidden
        Start-Sleep -Seconds 2

        $sw2 = [Diagnostics.Stopwatch]::StartNew()
        $ready2 = $false
        while ($sw2.Elapsed.TotalSeconds -lt 10) {
            try {
                $null = Invoke-WebRequest -Uri "http://localhost:19200/api/status" -TimeoutSec 2 -UseBasicParsing
                Write-Host "  Live2D Bridge ready! (port 19200)" -ForegroundColor Green
                $ready2 = $true
                break
            } catch {}
            Start-Sleep -Seconds 1
        }
        if (-not $ready2) {
            Write-Host "  WARNING: Bridge not responding after 10s" -ForegroundColor Yellow
        }
    }
}

# ========== 4. OpenClaw Gateway ==========
Write-Host "[4/5] OpenClaw Gateway" -ForegroundColor Yellow

try {
    $gwStatus = openclaw gateway status 2>&1
    if ($gwStatus -match 'running') {
        Write-Host "  Gateway already running" -ForegroundColor Green
    } else {
        Write-Host "  Starting gateway..."
        openclaw gateway start
        Start-Sleep -Seconds 2
        Write-Host "  Gateway started" -ForegroundColor Green
    }
} catch {
    Write-Host "  WARNING: Could not check/start gateway: $($_.Exception.Message)" -ForegroundColor Yellow
}

# ========== 5. Enable Watchdog ==========
Write-Host "[5/5] llama-watchdog" -ForegroundColor Yellow
Enable-Watchdog

# ========== Done ==========
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  All services ready!" -ForegroundColor Green
Write-Host "  llama-server : http://127.0.0.1:${llamaPort}" -ForegroundColor Green
Write-Host "  Live2D Bridge: http://localhost:19200" -ForegroundColor Green
Write-Host "  Gateway      : http://127.0.0.1:18789" -ForegroundColor Green
Write-Host "  Watchdog     : enabled (auto-restart if crash)" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
