# Artemis Studio Launcher
# 交互式 PySide6 GUI — TTS + ComfyUI，完全不走 llama 生命周期管理
#
# 使用方式:
#   cd D:\AI_Girlfriend
#   .\artemis_studio.ps1
#   或直接双击运行

$ErrorActionPreference = 'Continue'

# ── 1. Find workspace root ──
$workspace = $PSScriptRoot
if (-not $workspace) {
    # powershell -File <绝对路径> 时 $PSScriptRoot 为空，fallback 到 cwd
    $workspace = (Get-Location).Path
}
Set-Location $workspace

# ── 2. Find Python ──
$pythonPath = $null

# Try 1: config.yaml sovits_python
$configPath = Join-Path $workspace "config.yaml"
if (Test-Path $configPath) {
    $cfgReader = Join-Path $env:TEMP "_artemis_get_cfg.py"
    Set-Content $cfgReader -Value @'
import yaml, sys
with open(sys.argv[1], "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)
print(cfg.get("sovits_python", ""))
'@ -Encoding UTF8
    try { $pythonPath = (& $workspace\skills\sakura\runtime\python.exe $cfgReader $configPath).Trim().Trim('"') } catch { $pythonPath = $null }
    Remove-Item $cfgReader -ErrorAction SilentlyContinue
}

# Try 2: ComfyUI bundled Python (always exists)
if (-not $pythonPath -or -not (Test-Path $pythonPath)) {
    $pythonPath = "E:\comfyui\ComfyUI-aki-v3\python\python.exe"
}

# Try 3: sakura runtime
if (-not $pythonPath -or -not (Test-Path $pythonPath)) {
    $pythonPath = "$workspace\skills\sakura\runtime\python.exe"
}

# Final check
if (-not (Test-Path $pythonPath)) {
    Write-Host "[ERROR] Cannot find Python. Config, ComfyUI bundle, sakura runtime all failed." -ForegroundColor Red
    exit 1
}

Write-Host "Python: $pythonPath" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Artemis Studio - AI Girlfriend 创意工坊" -ForegroundColor Magenta
Write-Host "  llama-server 保持在线 · 独立推理通道" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── 3. Check/install PySide6 ──
$pysideCheck = & $pythonPath -c "import PySide6; print(PySide6.__version__)" 2>$null
if (-not $pysideCheck) {
    Write-Host "[WARN] PySide6 未安装，正在安装..." -ForegroundColor Yellow
    try { & $pythonPath -m pip install PySide6 -q } catch { Write-Host "[WARN] pip install 失败，继续尝试..." -ForegroundColor Yellow }
}

# ── 4. Launch GUI ──
Write-Host "Launching Artemis Studio..." -ForegroundColor Green
& $pythonPath "$workspace\artemis_studio.py"
