@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo.
echo   ========================================
echo     Shiki Service Shutdown
echo   ========================================
echo.

REM Find python (skip WindowsApps stub)
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
    echo ERROR: Python not found in PATH
    pause
    exit /b 1
)

echo   Stopping all services via shutdown_all.py...
%PEXE% "%~dp0shutdown_all.py"

echo.
echo   Done. All services stopped.
timeout /t 2 >nul
