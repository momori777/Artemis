@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
set "PRJ_ROOT=%~dp0"
set "SAKURA_PRJ_ROOT=%PRJ_ROOT%"

REM ============================================================
REM 检测非 ASCII 路径（PySide6 在非英文路径下会崩溃）
REM ============================================================
powershell -NoProfile -Command "$path = $env:SAKURA_PRJ_ROOT; if ($path -match '[^\x20-\x7E]') { exit 1 } else { exit 0 }" > nul 2>&1
if errorlevel 1 (
    powershell -NoProfile -Command "$path = $env:SAKURA_PRJ_ROOT; Write-Host '[错误] 项目路径包含非英文字符，PySide6 无法正常启动'; Write-Host '       请将项目移动到纯英文路径，如 D:\sakura'; Write-Host ('       当前路径: ' + $path)"
    pause
    exit /b 1
)

REM ============================================================
REM 检测 Python：runtime > Python 3.10 > Python 3.11 > Python 3.12 > 系统Python
REM PySide6 对 Python 3.13+ 兼容性不佳，优先使用 3.10-3.12
REM ============================================================
if exist "%PRJ_ROOT%\runtime\python.exe" (
    set "PYTHON_EXE=%PRJ_ROOT%\runtime\python.exe"
    echo [OK] 使用 runtime\python.exe
) else (
    set "PYTHON_EXE="
    set "PYTHON_310=!LOCALAPPDATA!\Programs\Python\Python310\python.exe"
    set "PYTHON_311=!LOCALAPPDATA!\Programs\Python\Python311\python.exe"
    set "PYTHON_312=!LOCALAPPDATA!\Programs\Python\Python312\python.exe"
    if exist "!PYTHON_310!" set "PYTHON_EXE=!PYTHON_310!"
    if exist "!PYTHON_311!" if "!PYTHON_EXE!"=="" set "PYTHON_EXE=!PYTHON_311!"
    if exist "!PYTHON_312!" if "!PYTHON_EXE!"=="" set "PYTHON_EXE=!PYTHON_312!"
    if not "!PYTHON_EXE!"=="" (
        echo [OK] 使用 !PYTHON_EXE!
    ) else (
        where python > nul 2>&1
        if errorlevel 1 (
            echo [错误] 未检测到 Python 3.10-3.12，请先运行 install.bat 安装依赖
            pause
            exit /b 1
        )
        set "PYTHON_EXE=python"
        echo [OK] 使用 PATH 中的 Python
    )
)

REM ============================================================
REM 设置 sentence-transformers 模型缓存到项目目录
REM ============================================================
set "HF_HOME=%PRJ_ROOT%\runtime\hf-cache"
set "SENTENCE_TRANSFORMERS_HOME=%PRJ_ROOT%\runtime\hf-cache"
if not exist "%HF_HOME%" mkdir "%HF_HOME%"

REM ============================================================
REM 启动
REM ============================================================
cd /d "%PRJ_ROOT%"
"%PYTHON_EXE%" main.py
pause
