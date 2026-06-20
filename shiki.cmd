@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
if %errorlevel% neq 0 pause
