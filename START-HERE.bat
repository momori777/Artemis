@echo off
rem ===========================================================================
rem  AI Girlfriend - START HERE (Windows)
rem
rem  Picks the LLM model / engine, the ComfyUI model, the GPT-SoVITS voice and
rem  the service ports, writes them into config.yaml, then starts and connects
rem  the whole stack (Strata -> daemon/llama.cpp -> ComfyUI -> GPT-SoVITS).
rem
rem  Double-click it, or run from a terminal:
rem      START-HERE.bat                 menu, then start
rem      START-HERE.bat --status        what is up right now
rem      START-HERE.bat --stop          stop everything
rem      START-HERE.bat --list          show available models and voices
rem      START-HERE.bat --help
rem ===========================================================================
chcp 65001 >nul 2>&1
setlocal
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"

rem ---- find a real Python 3.10+ (the Microsoft Store stub is not one) ------
set "PYCMD="
py -3 -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
if not errorlevel 1 set "PYCMD=py -3"
if not defined PYCMD (
    python -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
    if not errorlevel 1 set "PYCMD=python"
)
if not defined PYCMD (
    echo.
    echo   Python 3.10+ was not found on PATH.
    echo   Install it from https://www.python.org/downloads/
    echo   and tick "Add python.exe to PATH", then run this file again.
    echo.
    pause
    exit /b 1
)

%PYCMD% "%~dp0start_here.py" %*
set "CODE=%ERRORLEVEL%"

if not "%CODE%"=="0" (
    echo.
    echo   START-HERE exited with code %CODE%.
    echo   Logs: %~dp0logs\start-here\
    echo.
    pause
    exit /b %CODE%
)

rem Double-clicked (no arguments): keep the summary on screen.
if "%~1"=="" (
    echo.
    pause
)
exit /b 0
