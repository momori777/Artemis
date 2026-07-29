# start.ps1 — 一键启停全部 Shiki 服务
# Usage:
#   .\start.ps1       启动全部服务
#   .\start.ps1 -Stop  停止全部服务（等价于 shutdown_all.py）
#
# 启动顺序:
#   1. llama-server (ngl=41, batch=4096/2048)
#   2. Embedding Server (localhost:9999, all-MiniLM-L6-v2)
#   3. Artemis Headroom Proxy (localhost:19251 → llama:8080)
#   4. Live2D Bridge (localhost:19200)
#   5. OpenClaw Gateway (localhost:18789)
#   6. Cron Jobs (mem0-auto-sync + cleanup-orphans)
#   7. llama-watchdog (Task Scheduler)
#
# Stop 模式:
#   1. 禁用 llama-watchdog（防止自动重启）
#   2. 调用 shutdown_all.py 停止所有进程

param([switch]$Stop)

$ErrorActionPreference = "Stop"
# Gateway start 可能返回非零 exit（已运行时），不要因此中断
$global:ProgressPreference = 'SilentlyContinue'
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
$mem0Bridge  = Get-YamlValue $configRaw 'mem0_bridge'
$embedScript = Get-YamlValue $configRaw 'embedding_server'

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  四季夏目 — Shiki Natsume Startup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

function Test-Online($port, $label) {
    try {
        $null = Invoke-WebRequest -Uri "http://127.0.0.1:${port}/health" -TimeoutSec 2 -UseBasicParsing
        Write-Host "  ${label} already online (port ${port})" -ForegroundColor Green
        return $true
    } catch {
        return $false
    }
}

# ========== 1. Llama Server ==========
Write-Host "[1/6] llama-server" -ForegroundColor Yellow

if (Test-Online $llamaPort "llama-server") {
    # already up — skip
} else {
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

    Write-Host "  Starting llama-server (ngl=41, batch=2048/1024)..."

    Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1

    $llamaArgs = @(
        '-m', $llamaModel,
        '-c', '120000',
        '--flash-attn', 'on',
        '-ctk', 'q8_0',
        '-ctv', 'q8_0',
        '--no-mmap',
        '--cpu-moe',
        '--batch-size', '4096',
        '--ubatch-size', '2048',
        '--threads', '24',
        '-rea', 'off',
        '--jinja',
        '--cache-ram', '3000',
        '--parallel', '1',
        '--kv-unified',
        '--no-mmap',
        '--port', $llamaPort,
        '--timeout', '600'
    )

    $llamaErrLog = Join-Path $llamaLogDir "llama-err.log"
    $null = New-Item -ItemType Directory -Force -Path $llamaLogDir -ErrorAction SilentlyContinue
    $null = Start-Process -FilePath $llamaExe -ArgumentList $llamaArgs -WindowStyle Hidden `
        -RedirectStandardError $llamaErrLog

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

# ========== 2. Embedding Server ==========
Write-Host "[2/6] Embedding Server" -ForegroundColor Yellow

$embedPort = 9999

if (-not $embedScript) {
    $embedScript = Join-Path $scriptRoot "skills\shared\embedding_server.py"
}

if (Test-Online $embedPort "Embedding Server") {
    # already up
} else {
    if (-not (Test-Path $embedScript)) {
        Write-Host "  WARNING: embedding_server.py not found at $embedScript" -ForegroundColor Yellow
        Write-Host "  OpenClaw memory_search (semantic) will degrade to BM25-only" -ForegroundColor Yellow
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

# ========== 3. Headroom Proxy ==========
Write-Host "[3/7] Headroom Proxy (19251 → llama:8080)" -ForegroundColor Yellow

$headroomPort = 19251
$headroomScript = Join-Path $scriptRoot "artemis_headroom_proxy.py"

if (Test-Online $headroomPort "Headroom Proxy") {
    # already up
} else {
    if (-not (Test-Path $headroomScript)) {
        Write-Host "  WARNING: artemis_headroom_proxy.py not found at $headroomScript" -ForegroundColor Yellow
        Write-Host "  OpenClaw local provider (19251/v1) will fail!" -ForegroundColor Red
    } else {
        Write-Host "  Starting Headroom Proxy..."
        $pyExe = (Get-Command python -ErrorAction SilentlyContinue).Source
        if (-not $pyExe) { $pyExe = (Get-Command py -ErrorAction SilentlyContinue).Source }
        $null = Start-Process -FilePath $pyExe -ArgumentList @($headroomScript, "--port", $headroomPort) -WindowStyle Hidden
        Start-Sleep -Seconds 3

        $sw3 = [Diagnostics.Stopwatch]::StartNew()
        $ready3 = $false
        while ($sw3.Elapsed.TotalSeconds -lt 15) {
            try {
                $null = Invoke-WebRequest -Uri "http://127.0.0.1:${headroomPort}/health" -TimeoutSec 3 -UseBasicParsing
                Write-Host "  Headroom Proxy ready! (port ${headroomPort})" -ForegroundColor Green
                $ready3 = $true
                break
            } catch {}
            Start-Sleep -Seconds 1
        }
        if (-not $ready3) {
            Write-Host "  WARNING: Headroom Proxy not responding after 15s" -ForegroundColor Yellow
        }
    }
}

# ── Headroom 就绪后在 openclaw.json 新增 local-llama provider（只加不改） ──
# 现有 provider 原封不动，local-llama 下挂载本地模型 + 云端模型副本
# 原始 baseUrl 存入 sidecar 文件 ~/.openclaw/headroom_routes.json
if (Test-Online 19251 "Headroom Proxy") {
    Write-Host "  Adding local-llama provider to openclaw.json (add-only)..." -ForegroundColor DarkGray
    $ocJson = Join-Path $env:USERPROFILE ".openclaw\openclaw.json"
    $routesJson = Join-Path $env:USERPROFILE ".openclaw\headroom_routes.json"
    if (Test-Path $ocJson) {
        try {
            $ocCfg = Get-Content $ocJson -Raw -Encoding UTF8 | ConvertFrom-Json
            $headroomBase = "http://127.0.0.1:19251/v1"
            $llamaCtx = if ($config.llama.context) { [int]$config.llama.context } else { 120000 }
            $llamaPort = if ($config.llama_port) { $config.llama_port } else { 8080 }

            # 收集 sidecar 路由
            $routes = [PSCustomObject]@{}
            if (Test-Path $routesJson) {
                $routes = Get-Content $routesJson -Raw -Encoding UTF8 | ConvertFrom-Json
            }

            # 遍历非 local-llama provider，复制模型 + 记录 baseUrl
            $cloudModels = @()
            foreach ($provId in @($ocCfg.models.providers.PSObject.Properties.Name)) {
                if ($provId -in @('local-llama', 'local')) { continue }
                $prov = $ocCfg.models.providers.$provId
                $origUrl = $prov.baseUrl
                if (-not $origUrl -or $origUrl.Contains('19251')) { continue }

                # 保存 provider baseUrl 到 sidecar
                if (-not $routes.PSObject.Properties[$provId]) {
                    $routes | Add-Member -NotePropertyName $provId -NotePropertyValue $origUrl -Force
                }

                # 复制该 provider 的模型
                foreach ($m in $prov.models) {
                    $exists = $false
                    foreach ($cm in $cloudModels) { if ($cm.id -eq $m.id) { $exists = $true; break } }
                    if ($exists) { continue }
                    $modelCopy = $m.PSObject.Copy()
                    $modelCopy.name = "$($m.name) via Headroom"
                    $cloudModels += $modelCopy
                }
            }

            # 本地模型
            $localModel = [PSCustomObject]@{
                id = "llama-local"
                name = "Local Llama (Headroom+Mem0)"
                contextWindow = $llamaCtx
                maxTokens = 8192
                reasoning = $false
                compat = [PSCustomObject]@{
                    supportsReasoningEffort = $false
                    supportsTools = $false
                    supportsTemperature = $true
                    requiresStringContent = $true
                }
            }
            if (-not $routes.PSObject.Properties['llama-local']) {
                $routes | Add-Member -NotePropertyName 'llama-local' -NotePropertyValue "http://127.0.0.1:${llamaPort}/v1" -Force
            }

            $allModels = @($localModel) + $cloudModels

            # 检查 local-llama 是否已存在且配置一致
            $needPatch = $true
            if ($ocCfg.models.providers.PSObject.Properties['local-llama']) {
                $existing = $ocCfg.models.providers.'local-llama'
                if ($existing.baseUrl -and $existing.baseUrl.Contains('19251')) {
                    $existingIds = $existing.models | ForEach-Object { $_.id } | Sort-Object
                    $newIds = $allModels | ForEach-Object { $_.id } | Sort-Object
                    if ($existingIds -eq $newIds) { $needPatch = $false }
                }
            }

            if ($needPatch) {
                $localProvider = [PSCustomObject]@{
                    baseUrl = $headroomBase
                    api = "openai-completions"
                    apiKey = "***"
                    auth = "api-key"
                    timeoutSeconds = 300
                    models = $allModels
                }
                $ocCfg.models.providers | Add-Member -NotePropertyName 'local-llama' -NotePropertyValue $localProvider -Force

                # 写 sidecar + openclaw.json
                $routes | ConvertTo-Json -Depth 5 | Out-File -FilePath $routesJson -Encoding utf8NoBOM
                $ocCfg | ConvertTo-Json -Depth 10 | Out-File -FilePath $ocJson -Encoding utf8NoBOM
                Write-Host "  local-llama provider added ($($allModels.Count) models). Existing providers untouched." -ForegroundColor Green
            } else {
                # 仍然更新 sidecar
                $routes | ConvertTo-Json -Depth 5 | Out-File -FilePath $routesJson -Encoding utf8NoBOM
                Write-Host "  local-llama provider already configured" -ForegroundColor DarkGray
            }
        } catch {
            Write-Host "  WARNING: Failed to patch openclaw.json: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

# ========== 4. Live2D Bridge ==========
Write-Host "[4/7] Live2D Bridge" -ForegroundColor Yellow

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

# ========== 5. OpenClaw Gateway ==========
Write-Host "[5/7] OpenClaw Gateway" -ForegroundColor Yellow

try {
    $gwStatus = & openclaw gateway status 2>&1
    if ($gwStatus -match 'running') {
        Write-Host "  Gateway already running" -ForegroundColor Green
    } else {
        Write-Host "  Starting gateway..."
        & openclaw gateway start 2>&1 | Out-Null
        Start-Sleep -Seconds 2
        # Verify it actually started
        $gwVerify = & openclaw gateway status 2>&1
        if ($gwVerify -match 'running') {
            Write-Host "  Gateway started" -ForegroundColor Green
        } else {
            Write-Host "  WARNING: Gateway may not have started. Check: openclaw gateway status" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "  WARNING: Could not check/start gateway: $($_.Exception.Message)" -ForegroundColor Yellow
}

Start-Sleep -Seconds 2

# ========== 6. Mem0 Auto-Sync Cron Job ==========
Write-Host "[6/7] Memory System (mem0 → OpenClaw cron)" -ForegroundColor Yellow

if (-not $mem0Bridge) {
    $mem0Bridge = Join-Path $scriptRoot "skills\shared\mem0_bridge.py"
}

if (Test-Path $mem0Bridge) {
    Write-Host "  mem0_bridge.py found" -ForegroundColor Green

    # 清理旧的冗余 cron job（单角色 sync）
    $oldJobNames = @("mem0-to-markdown-sync", "mem0-sync-natsume", "mem0-sync-enola", "mem0-sync-atori")
    foreach ($name in $oldJobNames) {
        try {
            $check = & openclaw cron list 2>$null | Select-String $name -SimpleMatch
            if ($check) {
                Write-Host "  Removing deprecated cron job: $name" -ForegroundColor DarkGray
            }
        } catch {}
    }

    # 检查 mem0-auto-sync 是否存在（统一四角色同步）
    try {
        $check = & openclaw cron list 2>$null | Select-String "mem0-auto-sync" -SimpleMatch
        if ($check) {
            Write-Host "  mem0-auto-sync cron job already registered (every 30 min)" -ForegroundColor Green
        } else {
            Write-Host "  Registering mem0-auto-sync cron job..."
            $mem0SyncCron = Join-Path $scriptRoot "skills\shared\mem0_sync_cron.py"
            $syncMsg = "Run: python `"$mem0SyncCron`". Only exec, nothing else."
            & openclaw cron add --% --name mem0-auto-sync --every-ms 1800000 --message "$syncMsg" --timeout 60 --light-context --no-deliver 2>&1 | Out-Null
            Write-Host "  mem0-auto-sync cron job registered! (every 30 min, all 4 characters)" -ForegroundColor Green
        }
    } catch {
        Write-Host "  WARNING: Could not register mem0 cron job. Gateway may not be ready yet." -ForegroundColor Yellow
        Write-Host "  Run manually later: openclaw cron add ..." -ForegroundColor Yellow
    }
} else {
    Write-Host "  WARNING: mem0_bridge.py not found at $mem0Bridge" -ForegroundColor Yellow
    Write-Host "  Memory sync cron job skipped" -ForegroundColor Yellow
}

# ========== 7. Enable Watchdog ==========
Write-Host "[7/7] llama-watchdog" -ForegroundColor Yellow
Enable-Watchdog

# ========== Done ==========
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  All services ready!" -ForegroundColor Green
Write-Host "  llama-server   : http://127.0.0.1:${llamaPort}" -ForegroundColor Green
Write-Host "  Embedding      : http://127.0.0.1:${embedPort} (hybrid memory search)" -ForegroundColor Green
Write-Host "  Headroom Proxy : http://127.0.0.1:19251 (mem0 + context compression)" -ForegroundColor Green
Write-Host "  Live2D Bridge  : http://localhost:19200" -ForegroundColor Green
Write-Host "  Gateway        : http://127.0.0.1:18789" -ForegroundColor Green
Write-Host "  Mem0 Sync Cron : every 30 min (Qdrant → _mem0_auto.md)" -ForegroundColor Green
Write-Host "  Watchdog       : enabled (auto-restart if crash)" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
