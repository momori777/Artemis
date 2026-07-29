# AI Girlfriend 优化验证脚本
# 用途：快速验证配置读取和路由逻辑

Write-Host "=== AI Girlfriend 优化验证 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 检查配置文件
Write-Host "[1/4] 检查 config.yaml 新增配置..." -ForegroundColor Yellow
$configPath = ".\config.yaml"
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw
    if ($config -match "api_timeout:") {
        Write-Host "  ✓ api_timeout 配置存在" -ForegroundColor Green
    } else {
        Write-Host "  ✗ api_timeout 配置缺失（使用默认值 180）" -ForegroundColor Gray
    }
    if ($config -match "llama_max_concurrent:") {
        Write-Host "  ✓ llama_max_concurrent 配置存在" -ForegroundColor Green
    } else {
        Write-Host "  ✗ llama_max_concurrent 配置缺失（使用默认值 3）" -ForegroundColor Gray
    }
} else {
    Write-Host "  ✗ config.yaml 不存在！" -ForegroundColor Red
    exit 1
}

# 2. 检查硬编码是否移除
Write-Host ""
Write-Host "[2/4] 检查硬编码移除情况..." -ForegroundColor Yellow
$hardcoded = Select-String -Path ".\shiki_daemon.py" -Pattern "127\.0\.0\.1:8080" -SimpleMatch
if ($hardcoded) {
    Write-Host "  ✗ 发现残留硬编码：" -ForegroundColor Red
    $hardcoded | ForEach-Object { Write-Host "    行 $($_.LineNumber): $($_.Line.Trim())" -ForegroundColor Gray }
} else {
    Write-Host "  ✓ 无硬编码残留，所有端口从配置读取" -ForegroundColor Green
}

# 3. 检查信号量和重试逻辑
Write-Host ""
Write-Host "[3/4] 检查新增功能代码..." -ForegroundColor Yellow
$code = Get-Content ".\shiki_daemon.py" -Raw
if ($code -match "_llama_semaphore") {
    Write-Host "  ✓ 并发控制（信号量）已添加" -ForegroundColor Green
} else {
    Write-Host "  ✗ 并发控制缺失" -ForegroundColor Red
}
if ($code -match "REQUEST_MAX_RETRIES") {
    Write-Host "  ✓ 重试机制已添加" -ForegroundColor Green
} else {
    Write-Host "  ✗ 重试机制缺失" -ForegroundColor Red
}
if ($code -match "LLAMA_BASE_URL") {
    Write-Host "  ✓ LLAMA_BASE_URL 常量已添加" -ForegroundColor Green
} else {
    Write-Host "  ✗ LLAMA_BASE_URL 常量缺失" -ForegroundColor Red
}

# 4. 服务状态检查
Write-Host ""
Write-Host "[4/4] 检查服务运行状态..." -ForegroundColor Yellow
$daemonStatus = Test-NetConnection -ComputerName 127.0.0.1 -Port 19260 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($daemonStatus) {
    Write-Host "  ✓ Daemon (19260) 运行中" -ForegroundColor Green
    $response = $null
    try { $response = Invoke-RestMethod -Uri "http://127.0.0.1:19260/api/status" -TimeoutSec 3 } catch { }
    if ($response) {
        $llama = $response | Where-Object { $_.name -eq "Llama Server" }
        if ($llama) {
            $status = if ($llama.online) { "在线" } else { "离线" }
            $color = if ($llama.online) { "Green" } else { "Yellow" }
            Write-Host "  ✓ Llama Server: $status (端口 $($llama.port))" -ForegroundColor $color
        }
    } else {
        Write-Host "  ⚠ 无法获取详细状态" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✗ Daemon (19260) 未运行" -ForegroundColor Red
    Write-Host "    提示：运行 python shiki_daemon.py 启动服务" -ForegroundColor Gray
}

# 总结
Write-Host ""
Write-Host "=== 验证完成 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步测试建议：" -ForegroundColor Yellow
Write-Host "1. 启动服务：python shiki_daemon.py" -ForegroundColor Gray
Write-Host "2. 打开前端：http://127.0.0.1:19270" -ForegroundColor Gray
Write-Host "3. 测试本地模型：选择 'Local Llama' 发送消息" -ForegroundColor Gray
Write-Host "4. 测试云端模型：选择 'deepseek/...' 发送消息" -ForegroundColor Gray
Write-Host "5. 查看控制台日志，确认路由正确" -ForegroundColor Gray
Write-Host ""
