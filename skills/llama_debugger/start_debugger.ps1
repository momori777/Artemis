# llama 调试面板启动器
# 用法: .\start_debugger.ps1 [端口号]

param(
    [int]$Port = 8765
)

$SCRIPT_DIR = $PSScriptRoot
$SERVER = Join-Path $SCRIPT_DIR "server.py"

Write-Host "=== llama 调试面板 ===" -ForegroundColor Cyan
Write-Host "启动中: http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host "按 Ctrl+C 停止" -ForegroundColor Yellow
Write-Host ""

# 检查 Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "错误: 未找到 python，请确保已安装 Python" -ForegroundColor Red
    exit 1
}

# 启动服务器
$proc = Start-Process -FilePath "python" -ArgumentList $SERVER, $Port -PassThru -WindowStyle Hidden

Write-Host "✅ 已在后台启动 (PID: $($proc.Id))" -ForegroundColor Green
Write-Host "   打开浏览器访问: http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host ""

# 等待用户按键后关闭
Write-Host "按任意键关闭服务器..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host "正在关闭..." -ForegroundColor Yellow
Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
Write-Host "已关闭" -ForegroundColor Green
