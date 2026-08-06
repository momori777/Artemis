<#
.SYNOPSIS
  降级重启 llama-server — ngl 固定 41，逐级降低 batch_size/ubatch_size
  用于 VRAM 不足时手动恢复

.EXAMPLE
  .\restart_llama_degraded.ps1
  .\restart_llama_degraded.ps1 -ForceBatch 1024
#>
param(
  [int]$ForceBatch = -1
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8

# ========== 路径 — 从 config.yaml 读取 ==========
$scriptRoot = $PSScriptRoot
$workspaceRoot = Split-Path -Parent (Split-Path -Parent $scriptRoot)
if ($workspaceRoot -match 'skills$') { $workspaceRoot = Split-Path -Parent $workspaceRoot }

$configPath = Join-Path $workspaceRoot 'config.yaml'
if (-not (Test-Path $configPath)) {
  Write-Host "config.yaml not found at $configPath" -ForegroundColor Red
  exit 1
}
$configRaw = Get-Content $configPath -Raw -Encoding UTF8

function Get-YamlValue($raw, $key) {
  $pattern = "(?m)^\s*${key}\s*:\s*`"?(.+?)`"?\s*$"
  $m = [regex]::Match($raw, $pattern)
  if ($m.Success) { return $m.Groups[1].Value.Trim('"').Trim() }
  return $null
}

$exe    = Get-YamlValue $configRaw 'llama_exe'
$model  = Get-YamlValue $configRaw 'llama_model'
$logDir = Get-YamlValue $configRaw 'llama_log_dir'
$port   = Get-YamlValue $configRaw 'llama_port'
if (-not $port) { $port = 8080 }

if (-not (Test-Path $exe)) {
  Write-Host "llama-server.exe not found: $exe" -ForegroundColor Red
  exit 1
}
if (-not (Test-Path $model)) {
  Write-Host "Model not found: $model" -ForegroundColor Red
  exit 1
}

# ========== 辅助函数 ==========
function Kill-AllLlama {
  $procs = Get-Process llama-server -ErrorAction SilentlyContinue
  if ($procs) {
    $procs | Stop-Process -Force
    Write-Host "Killed $($procs.Count) llama-server process(es)"
  }
  Start-Sleep -Seconds 2
}

function Test-LlamaReady($timeoutSeconds = 120) {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt $timeoutSeconds) {
    try {
      $r = Invoke-WebRequest -Uri "http://127.0.0.1:${port}/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
      if ($r.StatusCode -eq 200) {
        $elapsed = [math]::Round($sw.Elapsed.TotalSeconds, 1)
        Write-Host "[OK] llama ready after ${elapsed}s" -ForegroundColor Green
        return $true
      }
    } catch {}
    Start-Sleep -Seconds 3
  }
  $elapsed = [math]::Round($sw.Elapsed.TotalSeconds, 1)
  Write-Host "[ERROR] llama not ready after ${elapsed}s" -ForegroundColor Red
  return $false
}

# ========== 主流程 ==========
Write-Host "=== Llama Degraded Restart (ngl=41, batch downscaling) ===" -ForegroundColor Cyan
Write-Host "Exe:   $exe"
Write-Host "Model: $model"
Write-Host "Port:  $port"
Write-Host ""

# 先杀所有残存进程
Write-Host "Cleaning up existing processes..." -ForegroundColor Yellow
Kill-AllLlama

# ===== 统一参数解析：从 llama_config.py 获取基础参数，降级时逐级降 batch =====
$pythonExe = $null
if (Get-Command python -ErrorAction SilentlyContinue) { $pythonExe = (Get-Command python).Source }
if (-not $pythonExe -and (Get-Command python3 -ErrorAction SilentlyContinue)) { $pythonExe = (Get-Command python3).Source }

$baseArgs = $null
if ($pythonExe) {
  try {
    $llamaCfgScript = Join-Path $scriptRoot "skills\shared\llama_config.py"
    $jsonOut = & $pythonExe $llamaCfgScript --args-only 2>$null | Out-String
    $parsed = $jsonOut | ConvertFrom-Json
    if ($parsed -is [array] -and $parsed.Count -gt 0) {
      $baseArgs = @($parsed | ForEach-Object { [string]$_ })
      Write-Host "  [llama-config] profile-matched args" -ForegroundColor DarkGray
    }
  } catch {
    Write-Host "  WARNING: llama_config.py failed, using degraded fallback" -ForegroundColor Yellow
  }
}

if (-not $baseArgs) {
  # 降级：正则从 config.yaml 读取
  $llamaCtx     = & { $m = [regex]::Match($configRaw, "(?m)^llama:\s*$"); if ($m.Success) { $s = $configRaw.Substring($m.Index + $m.Length); $e = [regex]::Match($s, "(?m)^[a-z][a-z_]+:"); $sec = if ($e.Success) { $s.Substring(0, $e.Index) } else { $s }; $vm = [regex]::Match($sec, "(?m)^\s*context\s*:\s*(\d+)"); if ($vm.Success) { $vm.Groups[1].Value } else { '150000' } } else { '150000' } }
  $llamaCtk     = & { $m = [regex]::Match($configRaw, "(?m)^llama:\s*$"); if ($m.Success) { $s = $configRaw.Substring($m.Index + $m.Length); $e = [regex]::Match($s, "(?m)^[a-z][a-z_]+:"); $sec = if ($e.Success) { $s.Substring(0, $e.Index) } else { $s }; $vm = [regex]::Match($sec, "(?m)^\s*ctk\s*:\s*`"?(\S+?)`"?\s*$"); if ($vm.Success) { $vm.Groups[1].Value.Trim('"') } else { 'q8_0' } } else { 'q8_0' } }
  $llamaCtv     = & { $m = [regex]::Match($configRaw, "(?m)^llama:\s*$"); if ($m.Success) { $s = $configRaw.Substring($m.Index + $m.Length); $e = [regex]::Match($s, "(?m)^[a-z][a-z_]+:"); $sec = if ($e.Success) { $s.Substring(0, $e.Index) } else { $s }; $vm = [regex]::Match($sec, "(?m)^\s*ctv\s*:\s*`"?(\S+?)`"?\s*$"); if ($vm.Success) { $vm.Groups[1].Value.Trim('"') } else { 'q8_0' } } else { 'q8_0' } }
  $llamaCacheRam = & { $m = [regex]::Match($configRaw, "(?m)^llama:\s*$"); if ($m.Success) { $s = $configRaw.Substring($m.Index + $m.Length); $e = [regex]::Match($s, "(?m)^[a-z][a-z_]+:"); $sec = if ($e.Success) { $s.Substring(0, $e.Index) } else { $s }; $vm = [regex]::Match($sec, "(?m)^\s*cache_ram\s*:\s*(\d+)"); if ($vm.Success) { $vm.Groups[1].Value } else { '3000' } } else { '3000' } }
  $specDraftNMax = & { $m = [regex]::Match($configRaw, "(?m)^llama:\s*$"); if ($m.Success) { $s = $configRaw.Substring($m.Index + $m.Length); $e = [regex]::Match($s, "(?m)^[a-z][a-z_]+:"); $sec = if ($e.Success) { $s.Substring(0, $e.Index) } else { $s }; $vm = [regex]::Match($sec, "(?m)^\s*spec_draft_n_max\s*:\s*(\d+)"); if ($vm.Success) { $vm.Groups[1].Value } else { '1' } } else { '1' } }

  $baseArgs = @(
    '-m', $model,
    '-c', $llamaCtx,
    '--flash-attn', 'on',
    '-ctk', $llamaCtk,
    '-ctv', $llamaCtv,
    '-ngl', '41',
    '--batch-size', '0',  # placeholder, will be overwritten
    '--ubatch-size', '0', # placeholder
    '--threads', '24',
    '-rea', 'off',
    '--jinja',
    '--cache-ram', $llamaCacheRam,
    '--parallel', '1',
    '--kv-unified',
    '--no-mmap',
    '--no-warmup',
    '--port', $port
  )

  # 模型类型检测：MoE (含 cpu_moe) vs Dense
  $modelBasename = [System.IO.Path]::GetFileNameWithoutExtension($model)
  $isDenseModel = $modelBasename -match '27b|dense'
  if (-not $isDenseModel) {
    $baseArgs += '--cpu-moe'
  }

  # 模型别名 (--alias)
  $llamaModelName = & { $m = [regex]::Match($configRaw, "(?m)^\s*llama_model_name\s*:\s*`"?(.+?)`"?\s*$"); if ($m.Success) { $m.Groups[1].Value.Trim('"').Trim() } else { '' } }
  if ($llamaModelName) {
    $baseArgs += '--alias', $llamaModelName
  } else {
    $modelBasename = [System.IO.Path]::GetFileNameWithoutExtension($model)
    $baseArgs += '--alias', $modelBasename
  }

  # MTP 检测
  $modelBasename = [System.IO.Path]::GetFileNameWithoutExtension($model)
  if ($modelBasename -match 'mtp') {
    Write-Host "  MTP model detected: adding --spec-type draft-mtp --spec-draft-n-max $specDraftNMax" -ForegroundColor Cyan
    $baseArgs += '--spec-type', 'draft-mtp', '--spec-draft-n-max', $specDraftNMax
  }
}

# 降级表：三个并行数组
$batchSizes    = @(4096, 2048, 1024, 512)
$ubatchSizes   = @(2048, 1024, 512,  256)
$batchLabels   = @('4096/2048', '2048/1024', '1024/512', '512/256')
$startIdx      = 0

if ($ForceBatch -gt 0) {
  $found = $false
  for ($i = 0; $i -lt $batchSizes.Count; $i++) {
    if ($batchSizes[$i] -eq $ForceBatch) {
      $startIdx = $i
      $found = $true
      Write-Host "Using forced batch=$ForceBatch"
      break
    }
  }
  if (-not $found) {
    Write-Host "Invalid batch size $ForceBatch, using full table" -ForegroundColor Yellow
  }
}

$started = $false
$finalBatch = 0
$finalUbatch = 0

for ($i = $startIdx; $i -lt $batchSizes.Count; $i++) {
  Kill-AllLlama
  $bs = $batchSizes[$i]
  $us = $ubatchSizes[$i]
  $lb = $batchLabels[$i]
  Write-Host "Trying batch=$lb..." -ForegroundColor Yellow

  $logFile = if ($logDir) { Join-Path $logDir "llama_degraded_$(Get-Date -Format 'yyyyMMddHHmm').log" } else { $null }

  # 从 baseArgs 构建：替换 --batch-size 和 --ubatch-size 的值
  $llaArgs = @($baseArgs | ForEach-Object { [string]$_ })
  for ($j = 0; $j -lt $llaArgs.Count; $j++) {
    if ($llaArgs[$j] -eq '--batch-size' -and ($j + 1) -lt $llaArgs.Count) {
      $llaArgs[$j + 1] = "$bs"
    } elseif ($llaArgs[$j] -eq '--ubatch-size' -and ($j + 1) -lt $llaArgs.Count) {
      $llaArgs[$j + 1] = "$us"
    }
  }

  # 从 baseArgs 中分离 exe 路径（llama_config --args-only 第一个元素是 exe_path）
  $degradedExe = $baseArgs[0]
  $llaArgs = @($llaArgs | Select-Object -Skip 1)

  $proc = Start-Process -FilePath $degradedExe -ArgumentList $llaArgs -NoNewWindow -PassThru

  if (Test-LlamaReady -timeoutSeconds 120) {
    $started = $true
    $finalBatch = $bs
    $finalUbatch = $us
    break
  } else {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Write-Host "batch=$lb failed, trying next level..." -ForegroundColor DarkYellow
  }
}

if ($started) {
  Write-Host ""
  Write-Host "=== SUCCESS: ngl=41, batch=$finalBatch/$finalUbatch, port=$port ===" -ForegroundColor Green
  # 重启 watchdog
  $watchdog = Join-Path (Split-Path -Parent $scriptRoot) 'llama-watchdog.ps1'
  if (Test-Path $watchdog) {
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$watchdog`"" -WindowStyle Hidden
    Write-Host "Watchdog restarted" -ForegroundColor Green
  }
  exit 0
} else {
  Write-Host ""
  Write-Host "=== FAILED: all batch levels exhausted ===" -ForegroundColor Red
  Write-Host "Try rebooting or checking GPU status."
  exit 1
}
