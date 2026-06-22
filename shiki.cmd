@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM  Set UTF-8
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo.
echo   ========================================
echo     Shiki Daemon Launcher
echo   ========================================
echo.
echo   Close this window to STOP all services.
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
    echo ERROR: Python not found in PATH
    echo Install Python from https://python.org
    pause
    exit /b 1
)
echo   Python: %PEXE%

REM  Check pystray
%PEXE% -c "import pystray" >nul 2>&1
if errorlevel 1 (
    echo   Installing pystray + pillow...
    %PEXE% -m pip install pystray pillow -q
)

echo.
echo   Starting daemon...
%PEXE% "%~dp0shiki_daemon.py" %*
set DAEMON_EXIT=%errorlevel%

echo.
echo   Shutting down services...
%PEXE% "%~dp0shutdown_all.py" --quiet
echo   Done.

exit /b %DAEMON_EXIT%
