# ============================================================
# start-llama.ps1 — 最兼容版 llama-server 启动脚本
# 仅依赖 PowerShell，不依赖 Python / llama_config.py
# 用户只需修改顶部「配置区」即可使用
# ============================================================

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8

$scriptRoot = $PSScriptRoot
if (-not $scriptRoot) { $scriptRoot = (Get-Item $PSCommandPath).DirectoryName }

# ============================================================
# ========== 配置区 (用户在此修改) ==========
# ============================================================

# llama-server 可执行文件路径
$llamaExe = "D:\AI_Girlfriend\llama-server\llama-server.exe"

# 模型文件路径（选择一个，取消注释）
$model = "D:\model\Qwen3.8-27B-UD-Q4_K_M.gguf"
# $model = "D:\model\Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf"
# $model = "D:\model\Qwen3.8-27B-Cold-Fusion-IQ4_XS.gguf"
# $model = "D:\model\Qwen3.8-27B-Cold-Fusion-Q4_K_M.gguf"
# $model = "D:\model\Qwen3.8-27B-OBLITERATED-Q4_K_M.gguf"
# $model = "D:\model\Qwen3.8-27B-UD-IQ4_XS.gguf"
# $model = "D:\model\Qwen3.8-27B-Cold-Fusion-LOW-IQ4_XS.gguf"

# 对话模板文件（可选，Qwen3.x 推荐）
$chatTemplate = "D:\AI_Girlfriend\chat_template.jinja"

# API Key（可选，留空则不设置）
$apiKey = "123456"

# ============================================================
# 以下参数按 LLAMA_TUNING.md 推荐值设置
# 按需修改即可
# ============================================================

$context       = 100000   # 上下文窗口 (token)
$temp          = 0.6      # 温度
$topP          = 0.95     # top-p
$topK          = 40       # top-k
$minP          = 0.01     # min-p
$repeatPenalty = 1.02     # 重复惩罚
$presencePenalty = 0.0    # 存在惩罚
$ngl           = 12       # GPU 层数 (RTX 5070 8GB Qwen3.8 推荐 12)
$threads       = 24       # CPU 线程数
$batchSize     = 600      # batch-size
$ubatchSize    = 300      # ubatch-size (batch/2)
$cacheRam      = 4000     # KV cache 内存占用 (MB)
$port          = 8080     # 监听端口

# 推理模式: on / off
$reasoning     = "on"

# MTP 推测解码（如果模型有嵌入 MTP 头）
$useMtp        = $true
$specDraftNMax = 5        # MTP 每次预测 token 数
$specDraftPMin = 0.84     # MTP 接受阈值

# 是否使用 Flash Attention
$flashAttn = "on"

# ============================================================
# 构建启动参数（不要修改下方）
# ============================================================

# 检查模型是否存在
if (-not (Test-Path $model)) {
    Write-Host "ERROR: Model not found: $model" -ForegroundColor Red
    Write-Host "Edit start-llama.ps1 and set the correct path above." -ForegroundColor Yellow
    exit 1
}

# 检查 llama-server 是否存在
if (-not (Test-Path $llamaExe)) {
    Write-Host "ERROR: llama-server.exe not found: $llamaExe" -ForegroundColor Red
    Write-Host "Check the path above and adjust if needed." -ForegroundColor Yellow
    exit 1 }

# 构建参数列表
$args = @()
$args += '-m', $model
$args += '-c', "$context"
$args += '--flash-attn', $flashAttn
$args += '-ctk', 'q4_0', '-ctv', 'q4_0'
$args += '--batch-size', "$batchSize"
$args += '--ubatch-size', "$ubatchSize"
$args += '--threads', "$threads"
$args += '--api-key', $apiKey
$args += '-rea', $reasoning
$args += '--jinja'
$args += '--cache-ram', "$cacheRam"
$args += '--parallel', '1'
$args += '--kv-unified'
$args += '--no-warmup'
$args += '--reasoning-preserve'
$args += '--reasoning-format', 'deepseek'
$args += '-ngl', "$ngl"

# 可选参数（按情况取消注释或修改）
# $args += '--temp', "$temp"
# $args += '--top-p', "$topP"
# $args += '--top-k', "$topK"
# $args += '--min-p', "$minP"
# $args += '--repeat-penalty', "$repeatPenalty"
# $args += '--presence-penalty', "$presencePenalty"

# MTP 推测解码
if ($useMtp) {
    $args += '--spec-type', 'draft-mtp'
    $args += '--spec-draft-n-max', "$specDraftNMax"
    $args += '--spec-draft-p-min', "$specDraftPMin"
}

# 对话模板
if (Test-Path $chatTemplate) {
    $args += '--chat-template-file', $chatTemplate
    # 推理深度控制（按需调整）
    $args += '--chat-template-kwargs', '{"reasoning_effort":"low"}'
}

# 输出摘要
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  llama-server 启动" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Model   : $model" -ForegroundColor Gray
Write-Host "  Context : $context tokens" -ForegroundColor Gray
Write-Host "  GPU     : -ngl $ngl" -ForegroundColor Gray
Write-Host "  Threads : $threads" -ForegroundColor Gray
Write-Host "  Port    : $port" -ForegroundColor Gray
Write-Host "  MTP     : $useMtp (n=$specDraftNMax, p=$specDraftPMin)" -ForegroundColor Gray
Write-Host "  Reasoning: $reasoning" -ForegroundColor Gray
Write-Host ""

# 杀掉已有进程
Write-Host "Stopping existing llama-server..." -ForegroundColor Yellow
taskkill /f /im llama-server.exe 2>$null | Out-Null
Start-Sleep -Seconds 1

# 启动
$errLog = Join-Path $scriptRoot "llama_err.log"
Write-Host "Starting llama-server..." -ForegroundColor Yellow

$proc = Start-Process -FilePath $llamaExe -ArgumentList $args `
    -WindowStyle Hidden `
    -RedirectStandardError $errLog -PassThru

Write-Host "  PID: $($proc.Id)" -ForegroundColor Gray
Write-Host "  Waiting for service to be ready on port $port..." -ForegroundColor Gray

# 等待就绪（最多 180 秒）
$sw = [Diagnostics.Stopwatch]::StartNew()
$ready = $false
while ($sw.Elapsed.TotalSeconds -lt 180) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:${port}/health" -TimeoutSec 3 -UseBasicParsing
        if ($r.StatusCode -eq 200) {
            $took = [math]::Round($sw.Elapsed.TotalSeconds, 1)
            Write-Host "  ✅ llama-server is ready! (${took}s)" -ForegroundColor Green
            $ready = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 2
}

if (-not $ready) {
    Write-Host "  ⚠️  llama-server did not respond within 180s" -ForegroundColor Yellow
    Write-Host "  Check: $errLog" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Done. API endpoint: http://127.0.0.1:${port}/v1" -ForegroundColor Green
Write-Host "  Health check:      http://127.0.0.1:${port}/health" -ForegroundColor Green
Write-Host "  Log file:          $errLog" -ForegroundColor Green
Write-Host "  (Edit start-llama.ps1 to change model/params)" -ForegroundColor Gray
Write-Host "============================================" -ForegroundColor Green
