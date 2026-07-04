@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo.
echo   ========================================
echo     Shiki AI Girlfriend — Shutdown
echo   ========================================

REM  Find python (prefer py launcher, avoid Windows Store stub)
set PEXE=
for /f "delims=" %%i in ('where py 2^>nul') do (
    echo %%i | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        set "PEXE=py"
        goto :found
    )
)
for /f "delims=" %%i in ('where python 2^>nul') do (
    echo %%i | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        set "PEXE=python"
        goto :found
    )
)
:found
if "%PEXE%"=="" (
    echo   ERROR: Python not found in PATH
    echo   Running fallback PowerShell cleanup...
    powershell -ExecutionPolicy Bypass -File "%~dp0skills\cleanup_orphans.ps1"
    pause
    exit /b 1
)

echo.
echo   Stopping all services via shutdown_all.py...
%PEXE% "%~dp0shutdown_all.py"

echo.
echo   ========================================
echo     All services stopped.
echo   ========================================
timeout /t 2 >nul
