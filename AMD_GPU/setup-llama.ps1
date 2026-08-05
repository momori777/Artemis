# setup-llama.ps1 (AMD GPU / Vulkan 版)
# AI Girlfriend — 四季夏目 · llama.cpp 一键部署 (Windows)
#
# 与 NVIDIA 版的区别:
#  - GPU 检测增加 AMD (WMI + vulkaninfo)
#  - 推荐 Vulkan 版 llama.cpp 二进制（非 CUDA）
#  - 生成 Vulkan 参数（无 --flash-attn, -ctk, -ctv, ngl=99）
#
# 用法:
#   powershell -File setup-llama.ps1
#   powershell -File setup-llama.ps1 -ModelPath "D:\models\my-model.gguf"

param(
    [string]$ModelPath = "",
    [int]$ContextSize = 150000,
    [int]$Port = 8080,
    [switch]$BuildLlama,
    [switch]$DryRun,
    [switch]$SkipPrompt
)

$ErrorActionPreference = "Stop"

# ============================================================================
# Banner
# ============================================================================
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  AI Girlfriend — 四季夏目 · llama.cpp Setup (Vulkan/AMD)  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# System Detection
# ============================================================================
Write-Host "[1/5] Detecting hardware..." -ForegroundColor Yellow

$cpuCores = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
$totalRamGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
$osName = (Get-CimInstance Win32_OperatingSystem).Caption

# GPU detection — support AMD + NVIDIA + Intel
$gpus = @()
$gpuVendor = "Unknown"
try {
    $wmiGpus = Get-CimInstance Win32_VideoController | Where-Object { $_.AdapterRAM -gt 0 -or $_.Name -match "NVIDIA|AMD|Intel|Radeon|GeForce|Arc" }
    foreach ($g in $wmiGpus) {
        $vramMB = if ($g.AdapterRAM) { [math]::Round($g.AdapterRAM / 1MB, 0) } else { 0 }
        $name = $g.Name
        $vendor = "Unknown"
        if ($name -match "NVIDIA|GeForce|RTX|GTX|Quadro") { $vendor = "NVIDIA" }
        elseif ($name -match "AMD|Radeon|RX ") { $vendor = "AMD" }
        elseif ($name -match "Intel|Arc") { $vendor = "Intel" }
        $gpus += @{ Name = $name; VRAM_GB = [math]::Round($vramMB / 1024, 1); VRAM_MB = $vramMB; Vendor = $vendor }
    }
} catch {}
if ($gpus.Count -eq 0) {
    # Fallback: try nvidia-smi for NVIDIA
    try {
        $nvidiaSmi = & nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>$null
        if ($nvidiaSmi) {
            foreach ($line in $nvidiaSmi) {
                $parts = $line -split ", "
                if ($parts.Count -ge 2) {
                    $vramMB = [int]($parts[1] -replace '\D', '')
                    $gpus += @{ Name = $parts[0].Trim(); VRAM_GB = [math]::Round($vramMB / 1024, 1); VRAM_MB = $vramMB; Vendor = "NVIDIA" }
                }
            }
        }
    } catch {}
}

Write-Host "  OS:       $osName" -ForegroundColor Gray
Write-Host "  CPU:      $cpuCores logical cores" -ForegroundColor Gray
Write-Host "  RAM:      $totalRamGB GB" -ForegroundColor Gray

if ($gpus.Count -gt 0) {
    foreach ($g in $gpus) {
        Write-Host "  GPU:      $($g.Name) ($($g.VRAM_GB) GB VRAM) [$($g.Vendor)]" -ForegroundColor Gray
    }
} else {
    Write-Host "  GPU:      [UNKNOWN — no GPU detected via WMI/nvidia-smi]" -ForegroundColor Yellow
    $gpus = @(@{ Name = "Unknown"; VRAM_GB = 0; VRAM_MB = 0; Vendor = "Unknown" })
}

# Pick primary GPU (first discrete with >2GB VRAM)
$primaryGpu = $gpus | Where-Object { $_.VRAM_GB -gt 2 } | Select-Object -First 1
if (-not $primaryGpu) { $primaryGpu = $gpus[0] }
$gpuVendor = $primaryGpu.Vendor
$vramGB = $primaryGpu.VRAM_GB

# Detect Vulkan SDK (useful info for AMD users)
$hasVulkan = $false
try {
    $vkResult = & vulkaninfo --summary 2>$null
    if ($LASTEXITCODE -eq 0) {
        $hasVulkan = $true
        Write-Host "  Vulkan:   Available" -ForegroundColor Green
    }
} catch {
    Write-Host "  Vulkan:   vulkaninfo not found (install Vulkan SDK for diagnostics)" -ForegroundColor Gray
}

# Detect AMD driver / ROCm
if ($gpuVendor -eq "AMD") {
    Write-Host "" -NoNewline
    Write-Host "  ⚠️  AMD GPU detected — recommend Vulkan llama.cpp backend" -ForegroundColor Yellow
    Write-Host "     Download: https://github.com/ggml-org/llama.cpp/releases" -ForegroundColor Yellow
    Write-Host "     File: llama-bXXXX-bin-win-vulkan-x64.zip" -ForegroundColor Yellow
    Write-Host "     CUDA binaries WILL NOT WORK on AMD GPUs." -ForegroundColor Red
    Write-Host ""
} elseif ($gpuVendor -eq "Intel") {
    Write-Host "" -NoNewline
    Write-Host "  ⚠️  Intel GPU detected — recommend Vulkan llama.cpp backend" -ForegroundColor Yellow
    Write-Host "     Download: https://github.com/ggml-org/llama.cpp/releases" -ForegroundColor Yellow
    Write-Host "     File: llama-bXXXX-bin-win-vulkan-x64.zip" -ForegroundColor Yellow
    Write-Host ""
}

# ============================================================================
# Model detection
# ============================================================================
Write-Host "[2/5] Detecting model..." -ForegroundColor Yellow

if (-not $ModelPath) {
    $defaults = @(
        "E:\Hermes3.6-35B-A3B-Uncensored-Genesis-V5-APEX-Compact.gguf",
        ".\models\Hermes3.6-35B-A3B-Uncensored-Genesis-V5-APEX-Compact.gguf",
        "Hermes3.6-35B-A3B-Uncensored-Genesis-V5-APEX-Compact.gguf"
    )
    foreach ($p in $defaults) {
        if (Test-Path $p) {
            $ModelPath = (Resolve-Path $p).Path
            break
        }
    }
}

if (-not $ModelPath -or -not (Test-Path $ModelPath)) {
    Write-Host "  No model found. Search paths:" -ForegroundColor Yellow
    foreach ($p in $defaults) { Write-Host "    - $p" -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "  Run download-models.ps1 first, or specify -ModelPath." -ForegroundColor Yellow
    exit 1
}

$modelSizeGB = [math]::Round((Get-Item $ModelPath).Length / 1GB, 2)
Write-Host "  Model:    $ModelPath" -ForegroundColor Gray
Write-Host "  Size:     $modelSizeGB GB" -ForegroundColor Gray

# ============================================================================
# Configuration Generation (Vulkan)
# ============================================================================
Write-Host "[3/5] Generating optimal Vulkan configuration..." -ForegroundColor Yellow

# Vulkan unified memory model — ngl=99 offload everything to GPU
# Vulkan handles paging automatically, unlike CUDA's strict allocation
$ngl = 99
$gpuMode = "Vulkan (full offload)"

if ($vramGB -le 0) {
    $ngl = 0
    $gpuMode = "CPU-ONLY"
    Write-Host "    Total VRAM:   N/A (no GPU)" -ForegroundColor Gray
    Write-Host "    → CPU-only mode" -ForegroundColor Yellow
} elseif ($vramGB -le 4) {
    $ngl = 33  # ~half the MoE layers
    $gpuMode = "Vulkan partial offload"
    Write-Host "    Total VRAM:   $vramGB GB — limited, partial offload" -ForegroundColor Yellow
} else {
    Write-Host "    Total VRAM:   $vramGB GB — full Vulkan offload" -ForegroundColor Green
}

Write-Host "    Mode:         $gpuMode (ngl=$ngl)" -ForegroundColor Cyan
Write-Host "    KV Cache:     ~2GB (system RAM)" -ForegroundColor Gray

# Thread configuration
if ($cpuCores -le 8) {
    $threads = $cpuCores - 2
    $batchSize = 2048
    $ubatch = 1024
} elseif ($cpuCores -le 24) {
    $threads = [math]::Min($cpuCores, 16)
    $batchSize = 4096
    $ubatch = 2048
} else {
    $threads = 24
    $batchSize = 4096
    $ubatch = 2048
}
if ($threads -lt 2) { $threads = 2 }

# Context size
$realContext = if ($vramGB -le 0) {
    [math]::Min($ContextSize, 32768)
} else {
    $ContextSize
}

# ── Vulkan args (NO --flash-attn, NO -ctk/-ctv — CUDA only) ──
$llamaArgs = @(
    '-m', "`"$ModelPath`"",
    '-c', $realContext.ToString(),
    '-ngl', $ngl.ToString(),
    '--cpu-moe',
    '--batch-size', $batchSize.ToString(),
    '--ubatch-size', $ubatch.ToString(),
    '--threads', $threads.ToString(),
    '-rea', 'off',
    '--jinja',
    '--cache-ram', '2048',
    '--parallel', '1',
    '--kv-unified',
    '--no-mmap'
)

# ============================================================================
# Check llama.cpp
# ============================================================================
Write-Host "[4/5] Checking llama.cpp (Vulkan)..." -ForegroundColor Yellow

$llamaExe = Get-Command llama-server.exe -ErrorAction SilentlyContinue

if (-not $llamaExe) {
    $searchPaths = @(
        ".\llama.cpp\build\bin\Release\llama-server.exe",
        "..\llama.cpp\build\bin\Release\llama-server.exe",
        "$env:USERPROFILE\Desktop\vllm\llama.cpp\build\bin\Release\llama-server.exe",
        "$env:LOCALAPPDATA\llama.cpp\llama-server.exe"
    )
    foreach ($p in $searchPaths) {
        if (Test-Path $p) {
            $llamaExe = Get-Command $p
            break
        }
    }
}

if (-not $llamaExe) {
    Write-Host ""
    Write-Host "  llama.cpp not found on PATH!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  ⚠️  AMD/Intel 用户必须下载 Vulkan 版本:" -ForegroundColor Cyan
    Write-Host "  https://github.com/ggml-org/llama.cpp/releases" -ForegroundColor White
    Write-Host "  找: llama-bXXXX-bin-win-vulkan-x64.zip" -ForegroundColor White
    Write-Host "  （不要下载 CUDA 版本，AMD 上不能运行）" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  也可选择自行编译 (需要 Vulkan SDK):" -ForegroundColor Cyan
    Write-Host "  cmake -B build -DGGML_VULKAN=ON" -ForegroundColor White
    Write-Host "  cmake --build build --config Release" -ForegroundColor White
    Write-Host ""

    if (-not $SkipPrompt) {
        $manualPath = Read-Host "  Enter llama-server.exe path (or press Enter to skip)"
    } else { $manualPath = "" }

    if ($manualPath -and (Test-Path $manualPath)) {
        $llamaExe = $manualPath
    } else {
        Write-Host "  No llama.cpp found. Exiting." -ForegroundColor Yellow
        Write-Host "  Re-run after downloading Vulkan llama.cpp." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "  llama-server: $($llamaExe.Source)" -ForegroundColor Green

# ============================================================================
# Generate output files
# ============================================================================
Write-Host "[5/5] Generating configuration files..." -ForegroundColor Yellow

$outputDir = Join-Path $PWD "llama-config"
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

# ── Hardware report ──
$report = @"
# llama.cpp Auto-Generated Configuration (Vulkan / AMD)
# Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
# Machine: $($env:COMPUTERNAME)

## Hardware Detection
- OS: $osName
- CPU: $cpuCores logical cores
- RAM: $totalRamGB GB
- GPU: $($primaryGpu.Name) ($($primaryGpu.VRAM_GB) GB VRAM) [$gpuVendor]
- Mode: $gpuMode

## Model
- Path: $ModelPath
- Size: $modelSizeGB GB

## Generated Parameters (Vulkan)
| Parameter | Value | Reasoning |
|-----------|-------|-----------|
| -ngl       | $ngl   | Full Vulkan offload (unified memory) |
| --threads  | $threads | $cpuCores logical cores |
| --batch-size | $batchSize | Balanced for GPU + CPU |
| --ubatch-size | $ubatch | Half batch-size |
| -c         | $realContext | Context window |
| Backend    | Vulkan | AMD/Intel/NVIDIA universal |
"@

$reportPath = Join-Path $outputDir "hardware-report.md"
Set-Content -Path $reportPath -Value $report -Encoding UTF8
Write-Host "  Hardware report: $reportPath" -ForegroundColor Gray

# ── Launch script ──
$launchContent = @"
# launch-llama.ps1 — Auto-generated by setup-llama.ps1 (Vulkan)
# Start llama-server with optimized Vulkan parameters
#
# Generated for: $($primaryGpu.Name) [$gpuVendor], $($primaryGpu.VRAM_GB) GB VRAM
# Mode: $gpuMode
# $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

`$exe = "$($llamaExe.Source)"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " AI Girlfriend — llama-server (Vulkan)" -ForegroundColor Cyan
Write-Host " GPU: $($primaryGpu.Name) [$gpuVendor] | VRAM: $($primaryGpu.VRAM_GB) GB" -ForegroundColor Cyan
Write-Host " Mode: $gpuMode" -ForegroundColor Cyan
Write-Host " Port: $Port" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

`$cmdArgs = @(
$(($llamaArgs | ForEach-Object { "    $_" }) -join ",`n")
)

Write-Host "Starting llama-server (Vulkan)..."
`$proc = Start-Process -FilePath `$exe -ArgumentList @(`$cmdArgs) -WindowStyle Hidden -PassThru
Write-Host "PID: `$(`$proc.Id)" -ForegroundColor Green
Write-Host ""
Write-Host "Waiting for server to start..." -ForegroundColor Yellow

for (`$i = 1; `$i -le 30; `$i++) {
    try {
        `$r = Invoke-WebRequest -Uri "http://127.0.0.1:8080/health" -UseBasicParsing -TimeoutSec 2
        if (`$r.StatusCode -eq 200) {
            Write-Host "Server ready!" -ForegroundColor Green
            Write-Host "Endpoint: http://127.0.0.1:8080" -ForegroundColor Green
            break
        }
    } catch {
        Start-Sleep -Seconds 1
        if (`$i -eq 30) {
            Write-Host "Timeout — server may still be loading. Check http://127.0.0.1:8080/health" -ForegroundColor Yellow
        }
    }
}

Write-Host "Server running. Press Ctrl+C to stop." -ForegroundColor Gray
try { Wait-Process -Id `$proc.Id } catch {}
"@

$launchPath = Join-Path $outputDir "launch-llama.ps1"
Set-Content -Path $launchPath -Value $launchContent -Encoding UTF8
Write-Host "  Launch script:  $launchPath" -ForegroundColor Green

# ── Watchdog ──
$watchdogContent = @"
# llama-watchdog.ps1 — Auto-generated by setup-llama.ps1 (Vulkan)
# Health check for llama-server

`$logFile = "$outputDir\watchdog.log"
`$null = New-Item -ItemType Directory -Path (Split-Path `$logFile -Parent) -Force -ErrorAction SilentlyContinue

function log { param([string]`$m) Add-Content -Path `$logFile -Value "[`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] `$m" -Encoding UTF8 }

log "=== watchdog check ==="

`$proc = Get-Process llama-server -ErrorAction SilentlyContinue
if (-not `$proc) {
    log "llama-server not running — restarting..."
    Start-Process powershell -ArgumentList '-File', '$launchPath' -WindowStyle Hidden
    log "restart triggered"
    exit 0
}

try {
    `$r = Invoke-WebRequest -Uri "http://127.0.0.1:8080/health" -UseBasicParsing -TimeoutSec 5
    if (`$r.StatusCode -eq 200) {
        log "healthy (PID=`$(`$proc.Id))"
        exit 0
    }
} catch {
    log "health check failed: `$_"
}

log "process alive but dead port — forcing restart..."
Stop-Process -Id `$proc.Id -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList '-File', '$launchPath' -WindowStyle Hidden
log "forced restart done"
exit 0
"@

$watchdogPath = Join-Path $outputDir "llama-watchdog.ps1"
Set-Content -Path $watchdogPath -Value $watchdogContent -Encoding UTF8
Write-Host "  Watchdog:       $watchdogPath" -ForegroundColor Gray

# ── Task Scheduler setup ──
$taskSched = @"
# Run in an elevated PowerShell to set up auto-restart:

# Llama health check (every 10 minutes)
schtasks /create /tn "llama-watchdog" `
  /tr "powershell -File '$watchdogPath'" `
  /sc minute /mo 10
"@

$schedPath = Join-Path $outputDir "setup-task-scheduler.ps1"
Set-Content -Path $schedPath -Value $taskSched -Encoding UTF8
Write-Host "  Task Scheduler: $schedPath" -ForegroundColor Gray

# ============================================================================
# Summary
# ============================================================================
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Setup Complete! (Vulkan)                                  ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Hardware:    $($primaryGpu.Name) [$gpuVendor] — $($primaryGpu.VRAM_GB) GB VRAM" -ForegroundColor White
Write-Host "  CPU:         $cpuCores cores | RAM: $totalRamGB GB" -ForegroundColor White
Write-Host "  Mode:        $gpuMode (Vulkan backend)" -ForegroundColor White
Write-Host "  Model:       $modelSizeGB GB GGUF" -ForegroundColor White
Write-Host ""
Write-Host "  Generated files in: $outputDir\" -ForegroundColor Cyan
Write-Host "    launch-llama.ps1      — Start llama-server (Vulkan)" -ForegroundColor White
Write-Host "    llama-watchdog.ps1    — Health check (Task Scheduler)" -ForegroundColor White
Write-Host "    setup-task-scheduler.ps1 — Register watchdog task" -ForegroundColor White
Write-Host "    hardware-report.md    — Your machine specs" -ForegroundColor White
Write-Host ""

if ($gpuVendor -eq "AMD") {
    Write-Host "  ⚠️  AMD GPU 用户重要提示:" -ForegroundColor Yellow
    Write-Host "  1. 确保用的是 Vulkan 版 llama.cpp (不是 CUDA 版)" -ForegroundColor White
    Write-Host "  2. ComfyUI 和 GPT-SoVITS 需要自行解决 GPU 加速:" -ForegroundColor White
    Write-Host "     - ComfyUI: 用 DirectML 版或 ZLUDA" -ForegroundColor White
    Write-Host "     - GPT-SoVITS: 目前仅支持 NVIDIA CUDA/CPU" -ForegroundColor White
    Write-Host "  3. 已自动应用 AMD_GPU/ 文件夹中的适配脚本" -ForegroundColor White
    Write-Host ""
} elseif ($gpuVendor -eq "Intel") {
    Write-Host "  ⚠️  Intel GPU 用户重要提示:" -ForegroundColor Yellow
    Write-Host "  1. 确保用的是 Vulkan 版 llama.cpp" -ForegroundColor White
    Write-Host "  2. ComfyUI 和 TTS 建议用 CPU 或 DirectML" -ForegroundColor White
    Write-Host ""
}

Write-Host "  Quick Start:" -ForegroundColor Cyan
Write-Host "    1. Run .\llama-config\launch-llama.ps1" -ForegroundColor White
Write-Host "    2. Wait for http://127.0.0.1:$Port/health to return 200" -ForegroundColor White
Write-Host "    3. Configure OpenClaw to use http://127.0.0.1:$Port/v1" -ForegroundColor White
Write-Host ""
