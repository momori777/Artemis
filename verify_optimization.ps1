# AI Girlfriend Optimization Verification Script
# Quick check for configuration and code changes

Write-Host "=== AI Girlfriend Optimization Check ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check config.yaml
Write-Host "[1/3] Checking config.yaml..." -ForegroundColor Yellow
$configPath = ".\config.yaml"
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw
    $hasTimeout = $config -match "api_timeout:"
    $hasConcurrent = $config -match "llama_max_concurrent:"
    
    if ($hasTimeout) {
        Write-Host "  OK: api_timeout config found" -ForegroundColor Green
    } else {
        Write-Host "  INFO: api_timeout not set (will use default 180)" -ForegroundColor Gray
    }
    
    if ($hasConcurrent) {
        Write-Host "  OK: llama_max_concurrent config found" -ForegroundColor Green
    } else {
        Write-Host "  INFO: llama_max_concurrent not set (will use default 3)" -ForegroundColor Gray
    }
} else {
    Write-Host "  ERROR: config.yaml not found" -ForegroundColor Red
    exit 1
}

# 2. Check for hardcoded URLs
Write-Host ""
Write-Host "[2/3] Checking for hardcoded URLs..." -ForegroundColor Yellow
$hardcoded = Select-String -Path ".\shiki_daemon.py" -Pattern "127\.0\.0\.1:8080" -SimpleMatch
if ($hardcoded) {
    Write-Host "  WARNING: Found hardcoded URLs:" -ForegroundColor Red
    $hardcoded | ForEach-Object { Write-Host "    Line $($_.LineNumber)" -ForegroundColor Gray }
} else {
    Write-Host "  OK: No hardcoded URLs found" -ForegroundColor Green
}

# 3. Check new features
Write-Host ""
Write-Host "[3/3] Checking new features..." -ForegroundColor Yellow
$code = Get-Content ".\shiki_daemon.py" -Raw
$hasSemaphore = $code -match "_llama_semaphore"
$hasRetry = $code -match "REQUEST_MAX_RETRIES"
$hasBaseUrl = $code -match "LLAMA_BASE_URL"

if ($hasSemaphore) {
    Write-Host "  OK: Concurrency control (semaphore) added" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Semaphore missing" -ForegroundColor Red
}

if ($hasRetry) {
    Write-Host "  OK: Retry mechanism added" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Retry mechanism missing" -ForegroundColor Red
}

if ($hasBaseUrl) {
    Write-Host "  OK: LLAMA_BASE_URL constant added" -ForegroundColor Green
} else {
    Write-Host "  ERROR: LLAMA_BASE_URL missing" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Check Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start daemon: python shiki_daemon.py" -ForegroundColor Gray
Write-Host "2. Open frontend: http://127.0.0.1:19270" -ForegroundColor Gray
Write-Host "3. Test local model: select 'Local Llama'" -ForegroundColor Gray
Write-Host "4. Test cloud model: select 'deepseek/...'" -ForegroundColor Gray
Write-Host ""
