@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM  Set UTF-8
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo.
echo   ========================================
echo     Shiki AI Girlfriend — Startup
echo   ========================================
echo.

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
    echo   Install Python from https://python.org
    pause
    exit /b 1
)
echo   Python: %PEXE%

REM  Check pystray (needed for tray icon)
%PEXE% -c "import pystray" >nul 2>&1
if errorlevel 1 (
    echo   Installing pystray + pillow...
    %PEXE% -m pip install pystray pillow -q
)

echo.
echo   Starting Shiki Daemon (tray icon + auto-start services)...
echo   Services: llama-server, Embedding, Live2D, Artemis Bridge, Gateway, Task Board, WebChat
echo.
echo   --- Close this window or right-click tray ^> Quit to stop ---
echo.

REM  Launch daemon (runs with tray icon, auto-starts all services)
REM  Pass all arguments through (e.g. --no-auto-start, --no-llama)
%PEXE% "%~dp0shiki_daemon.py" %*
set DAEMON_EXIT=%errorlevel%

echo.
echo   Shutting down services...
%PEXE% "%~dp0shutdown_all.py" --quiet
echo   All services stopped. Goodbye~

exit /b %DAEMON_EXIT%
