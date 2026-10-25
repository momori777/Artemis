# AI Girlfriend — 资产下载（ComfyUI 套件 + SoVITS 权重 + Embedding）
# LLM 跳过：flash-next 由 Strata 引擎(8080)提供服务，已在运行
$ErrorActionPreference = "Continue"
$env:PSNativeCommandUseErrorActionPreference = "0"
$repo = "TAOTAO777/ai-girlfriend-natsume"
$root = Split-Path $PSScriptRoot -Parent   # repo root (.deploy\..)
# hf.exe: PATH 中的 hf 优先，否则需设置 $env:HF_EXE
$hf = if ($env:HF_EXE) { $env:HF_EXE } else { (Get-Command hf -ErrorAction SilentlyContinue).Source }
if ($env:HF_TOKEN_FILE) { $env:HF_TOKEN = (Get-Content $env:HF_TOKEN_FILE -Raw).Trim() }
$log  = Join-Path $PSScriptRoot "download.log"
function Log($m) { "[$(Get-Date -Format 'HH:mm:ss')] $m" | Tee-Object -FilePath $log -Append }

$dl = if ($env:DOWNLOAD_CACHE_DIR) { $env:DOWNLOAD_CACHE_DIR } else { Join-Path $env:USERPROFILE "ai_girlfriend_downloads" }
New-Item -ItemType Directory -Force -Path $dl | Out-Null

# repo_path -> local base dir (files land preserving repo layout)
$Items = @(
  "comfyui/checkpoints/WAI-Nsfw-Illustrious-17.safetensors",
  "comfyui/diffusion_models/miaomiaoHarem_29BBETA10.safetensors",
  "comfyui/diffusion_models/oneObsession_anima29BV1.safetensors",
  "comfyui/diffusion_models/qwen-image-2.1-Q6_K.gguf",
  "comfyui/text_encoders/qwen3vl_8b_int8_convrot.safetensors",
  "comfyui/vae/qwen_image_vae.safetensors"
  # SoVITS 权重已在 repo: skills\sovits\weights\ 全部存在，无需下载
)
foreach ($rp in $Items) {
  $target = Join-Path $dl ($rp -replace '/','\')
  if (Test-Path $target) { Log "SKIP (exists): $rp"; continue }
  Log "DL: $rp"
  & $hf download $repo $rp --local-dir $dl 2>&1 | Out-File $log -Append
  if ($LASTEXITCODE -eq 0 -and (Test-Path $target)) { Log "OK: $rp" } else { Log "FAIL($LASTEXITCODE): $rp" }
}

# Embedding 模型 -> deps\embedding\{all-MiniLM-L6-v2,bge-small-zh-v1.5}
$depsDir = Join-Path $root "deps"
foreach ($folder in @("embedding/all-MiniLM-L6-v2","embedding/bge-small-zh-v1.5")) {
  $marker = Join-Path $depsDir ($folder -replace 'embedding/','embedding\')
  if (Test-Path (Join-Path $marker "config.json")) { Log "SKIP (exists): $folder"; continue }
  Log "DL folder: $folder"
  & $hf download $repo $folder --local-dir $depsDir 2>&1 | Out-File $log -Append
  if ($LASTEXITCODE -eq 0) { Log "OK: $folder" } else { Log "FAIL($LASTEXITCODE): $folder" }
}

# SoVITS 权重摆位：skills\sovits\weights\（weight_*.json 相对此目录解析）+ deps\GPT-SoVITS\weights\ 兼容副本
$wDir = Join-Path $root "skills\sovits\weights"
$sovitsCompat = Join-Path $depsDir "GPT-SoVITS\weights"
New-Item -ItemType Directory -Force -Path $wDir | Out-Null
New-Item -ItemType Directory -Force -Path $sovitsCompat | Out-Null
$map = @{
  "gpt-sovits-weights\GPT_weights_v2Pro\xxx-e30.ckpt"                 = "xxx-e30.ckpt"
  "gpt-sovits-weights\SoVITS_weights_v2Pro\xxx_e20_s6240.pth"         = "xxx_e20_s6240.pth"
  "gpt-sovits-weights\GPT_weights_v2Pro\sakura\Sakura-e15.ckpt"       = "Sakura-e15.ckpt"
  "gpt-sovits-weights\SoVITS_weights_v2Pro\sakura\Sakura_e8_s7176.pth"= "Sakura_e8_s7176.pth"
}
foreach ($k in $map.Keys) {
  $src = Join-Path $dl $k
  if (Test-Path $src) {
    Copy-Item $src (Join-Path $wDir $map[$k]) -Force
    Copy-Item $src (Join-Path $sovitsCompat $map[$k]) -Force
    Log "PLACED: $($map[$k])"
  }
}

Log "ALL DONE"
