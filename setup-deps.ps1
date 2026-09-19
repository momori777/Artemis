# setup-deps.ps1 - AI Girlfriend dependency downloader
# Clones ComfyUI and GPT-SoVITS from git, updates config.yaml
# Usage: powershell -ExecutionPolicy Bypass -File setup-deps.ps1

param(
    [string]$InstallDir = "",
    [switch]$SkipComfyUI = $false,
    [switch]$SkipSovits = $false
)

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not $InstallDir) {
    $InstallDir = Join-Path $scriptDir "deps"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI Girlfriend - Dependency Downloader" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Install dir: $InstallDir" -ForegroundColor Yellow
Write-Host ""

# Ensure install dir exists
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    Write-Host "Created: $InstallDir" -ForegroundColor Green
}

# Detect OS and GPU
$os = $env:OS
Write-Host "OS: $os" -ForegroundColor Gray

$hasNvidia = $false
try {
    $nvidiaDevices = Get-PnpDevice | Where-Object { $_.FriendlyName -like "*NVIDIA*" }
    if ($nvidiaDevices) {
        $hasNvidia = $true
        Write-Host "NVIDIA GPU detected: $($nvidiaDevices[0].FriendlyName)" -ForegroundColor Green
    }
} catch {
    Write-Host "Could not detect GPU" -ForegroundColor DarkGray
}

# Repo URLs
$comfyuiRepo = "https://github.com/comfyanonymous/ComfyUI.git"
$comfyuiDir = Join-Path $InstallDir "ComfyUI"
$sovitsRepo = "https://github.com/RVC-Boss/GPT-SoVITS.git"
$sovitsDir = Join-Path $InstallDir "GPT-SoVITS"

# ComfyUI
if (-not $SkipComfyUI) {
    Write-Host ""
    Write-Host "--- ComfyUI ---" -ForegroundColor Green
    
    if (Test-Path $comfyuiDir) {
        Write-Host "Already exists: $comfyuiDir" -ForegroundColor DarkGray
    } else {
        Write-Host "Cloning ComfyUI..." -ForegroundColor Yellow
        Push-Location $InstallDir
        try {
            git clone $comfyuiRepo 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  OK" -ForegroundColor Green
            } else {
                Write-Host "  FAILED" -ForegroundColor Red
            }
        } finally {
            Pop-Location
        }
    }
    
    # Detect Python
    $comfyuiPython = ""
    $systemPython = Get-Command python -ErrorAction SilentlyContinue
    if ($systemPython) {
        $comfyuiPython = $systemPython.Source
        Write-Host "  Python: $comfyuiPython" -ForegroundColor Green
    }
}

# GPT-SoVITS
if (-not $SkipSovits) {
    Write-Host ""
    Write-Host "--- GPT-SoVITS ---" -ForegroundColor Green
    
    if (Test-Path $sovitsDir) {
        Write-Host "Already exists: $sovitsDir" -ForegroundColor DarkGray
    } else {
        Write-Host "Cloning GPT-SoVITS..." -ForegroundColor Yellow
        Push-Location $InstallDir
        try {
            git clone $sovitsRepo 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  OK" -ForegroundColor Green
            } else {
                Write-Host "  FAILED" -ForegroundColor Red
            }
        } finally {
            Pop-Location
        }
    }
    
    # Detect Python
    $sovitsPython = ""
    $systemPython = Get-Command python -ErrorAction SilentlyContinue
    if ($systemPython) {
        $sovitsPython = $systemPython.Source
        Write-Host "  Python: $sovitsPython" -ForegroundColor Green
    }
}

# Update config.yaml
Write-Host ""
Write-Host "--- Updating config.yaml ---" -ForegroundColor Green

$configPath = Join-Path $scriptDir "config.yaml"
if (Test-Path $configPath) {
    $configContent = Get-Content $configPath -Encoding UTF8
    
    if (-not $SkipComfyUI -and (Test-Path $comfyuiDir)) {
        # Set comfyui_root first (takes priority)
        $configContent = $configContent -replace 'comfyui_root:.*', ("comfyui_root: " + $comfyuiDir.Replace('\', '\\'))
        if ($comfyuiPython) {
            $configContent = $configContent -replace 'comfyui_python:.*', ("comfyui_python: " + $comfyuiPython.Replace('\', '\\'))
        }
        $comfyuiCkptDir = Join-Path $comfyuiDir "models\checkpoints"
        if (-not (Test-Path $comfyuiCkptDir)) {
            New-Item -ItemType Directory -Path $comfyuiCkptDir -Force | Out-Null
        }
        $configContent = $configContent -replace 'comfyui_checkpoints_dir:.*', ("comfyui_checkpoints_dir: " + $comfyuiCkptDir.Replace('\', '\\'))
    }
    
    if (-not $SkipSovits -and (Test-Path $sovitsDir)) {
        if ($sovitsPython) {
            $configContent = $configContent -replace 'sovits_python:.*', ("sovits_python: " + $sovitsPython.Replace('\', '\\'))
        }
        $configContent = $configContent -replace 'sovits_weights_dir:.*', ("sovits_weights_dir: " + $sovitsDir.Replace('\', '\\'))
    }
    
    Set-Content $configPath -Value $configContent -Encoding UTF8
    Write-Host "Updated: $configPath" -ForegroundColor Green
} else {
    Write-Host "config.yaml not found, skipping" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Done!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  - Install Python deps for each project" -ForegroundColor White
Write-Host "  - Download models with download-models.ps1" -ForegroundColor White
Write-Host "  - Run quick_setup.ps1 for further configuration" -ForegroundColor White
