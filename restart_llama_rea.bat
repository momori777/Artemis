@echo off
REM restart_llama_rea.bat — 重启 llama-server 切换 reasoning 模式
REM 用法: restart_llama_rea.bat [on|off]

setlocal enabledelayedexpansion
set "REA_MODE=%1"
if "%REA_MODE%"=="" set "REA_MODE=off"

set "PROJECT_DIR=%~dp0"
echo [%date% %time%] Switching llama to -rea %REA_MODE% >> %PROJECT_DIR%\rea_switch.log

REM 关掉 llama
taskkill /f /im llama-server.exe >nul 2>&1
echo Stopped llama, waiting for port release...
:wait_stop
timeout /t 1 /nobreak >nul
curl -s http://127.0.0.1:8080/health >nul 2>&1
if not errorlevel 1 goto wait_stop
echo Port 8080 released.

REM 启动 llama
start "" /B %PROJECT_DIR%\llama-server\llama-server.exe ^
  -m E:\Hermes3.6-35B-A3B-Uncensored-Genesis-V7-APEX-Compact.gguf ^
  -c 150000 --flash-attn on ^
  -ctk q8_0 -ctv q8_0 ^
  --no-mmap --cpu-moe ^
  --batch-size 2048 --ubatch-size 1024 ^
  --threads 24 ^
  -rea %REA_MODE% --reasoning-format deepseek --jinja ^
  --cache-ram 3000 ^
  --parallel 1 --kv-unified --no-mmap ^
  --port 8080 --timeout 600 ^
  > C:\Users\TK\.openclaw\workspace\llama-out.log 2>&1

echo Started llama with -rea %REA_MODE%, waiting for ready...

:wait_ready
timeout /t 2 /nobreak >nul
curl -s http://127.0.0.1:8080/health | findstr "ok" >nul 2>&1
if errorlevel 1 goto wait_ready

echo [%date% %time%] llama ready with -rea %REA_MODE% >> %PROJECT_DIR%\rea_switch.log
echo DONE: -rea %REA_MODE%
