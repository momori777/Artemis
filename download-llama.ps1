# download-llama.ps1
# 自动下载最新版 llama-server (CUDA 12.x, Windows x64)
# 解压到当前目录的 llama-server\ 下

$ErrorActionPreference = "Stop"

$OutDir = Join-Path $PSScriptRoot "llama-server"

# 1. 获取最新 release tag
Write-Host "Fetching latest llama.cpp release..." -ForegroundColor Cyan
$apiUrl = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"
$release = Invoke-RestMethod -Uri $apiUrl -Headers @{ "User-Agent" = "PowerShell" }
$tag = $release.tag_name
Write-Host "  Latest: $tag" -ForegroundColor Green

# 2. 找到 CUDA Windows zip
$asset = $release.assets | Where-Object { $_.name -match "^llama-b[0-9]+-bin-win-cuda-1[2-9]\.[0-9]-x64\.zip$" } | Select-Object -First 1
if (-not $asset) {
    Write-Host "ERROR: No CUDA Windows asset found for $tag" -ForegroundColor Red
    exit 1
}
Write-Host "  Found: $($asset.name) ($([math]::Round($asset.size/1MB,1)) MB)" -ForegroundColor Gray

# 3. 下载
$zip = "$env:TEMP\llama-server-$tag.zip"
Write-Host "Downloading..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip

# 4. 解压
Write-Host "Extracting to $OutDir..." -ForegroundColor Yellow
if (Test-Path $OutDir) { Remove-Item $OutDir -Recurse -Force }
Expand-Archive -Path $zip -DestinationPath $OutDir -Force
Remove-Item $zip

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Write-Host "  $OutDir\llama-server.exe" -ForegroundColor Green
