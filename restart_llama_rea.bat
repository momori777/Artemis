@echo off
REM restart_llama_rea.bat — 重启 llama-server 切换 reasoning 模式
REM 用法: restart_llama_rea.bat [on|off]
REM 所有参数通过 llama_config.py 从 config.yaml + model_profiles 读取，无需硬编码

setlocal enabledelayedexpansion
set "REA_MODE=%1"
if "%REA_MODE%"=="" set "REA_MODE=off"

set "PROJECT_DIR=%~dp0"
echo [%date% %time%] Switching llama to -rea %REA_MODE% >> %PROJECT_DIR%\rea_switch.log

REM ========== 调用 llama_config.py 获取启动参数（JSON）==========
REM 优先尝试系统 python，然后尝试 config.yaml 中的 comfyui_python
set "PYTHON_CMD="
for %%e in (python python3) do (
    where %%e >nul 2>&1 && set "PYTHON_CMD=%%e" && goto :found_python
)
REM 从 config.yaml 读取 comfyui_python
for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "$y = Get-Content '%PROJECT_DIR%\config.yaml' -Raw -Encoding UTF8; $m = [regex]::Match($y, '(?m)^\s*comfyui_python\s*:\s*"?(.+?)"?\s*$'); if ($m.Success) { $m.Groups[1].Value.Trim('"').Trim() } else { '' }"`) do set "PYTHON_CMD=%%a"
if "%PYTHON_CMD%"=="" set "PYTHON_CMD=python"
:found_python

REM 获取 args JSON
set "ARGS_JSON="
for /f "usebackq delims=" %%a in (`"%PYTHON_CMD%" "%PROJECT_DIR%\skills\shared\llama_config.py" --args-only 2^>nul`) do set "ARGS_JSON=%%a"
if "%ARGS_JSON%"=="" goto :fallback_regex

REM 解析 JSON 为 PowerShell 参数（用 PS 展开数组）
REM 重写为：PS 解析 JSON，替换 -rea 值，直接启动
powershell -NoProfile -Command ^
  "$json = '%ARGS_JSON%' | ConvertFrom-Json; " ^
  "$args = @($json | ForEach-Object { [string]$_ }); " ^
  "$exePath = $args[0]; $llamaArgs = $args[1..($args.Length-1)]; " ^
  "$reaIdx = [array]::IndexOf($llamaArgs, '-rea'); " ^
  "if ($reaIdx -ge 0 -and ($reaIdx + 1) -lt $llamaArgs.Length) { $llamaArgs[$reaIdx + 1] = '%REA_MODE%'; } " ^
  "Write-Host \"Restarting llama with -rea %REA_MODE%...\"; " ^
  "taskkill /f /im llama-server.exe 2>$null; " ^
  "Start-Sleep -Seconds 2; " ^
  "$logDir = [System.IO.Path]::GetDirectoryName('%PROJECT_DIR%llama-server\restart-logs\llama-rea-out.log'); " ^
  "if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }; " ^
  "Start-Process -FilePath $exePath -ArgumentList $llamaArgs -WindowStyle Hidden -RedirectStandardError '%PROJECT_DIR%llama-server\restart-logs\llama-rea-out.log'; " ^
  "Write-Host \"Waiting for llama to be ready...\"; " ^
  "$sw = [Diagnostics.Stopwatch]::StartNew(); " ^
  "while ($sw.Elapsed.TotalSeconds -lt 180) { " ^
  "  try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8080/health' -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue; if ($r.StatusCode -eq 200) { Write-Host 'llama ready!'; exit 0 } } catch {}; " ^
  "  Start-Sleep -Seconds 3; " ^
  "}; " ^
  "Write-Host 'llama timeout!'; exit 1" ^
  && echo [%date% %time%] llama ready with -rea %REA_MODE% >> %PROJECT_DIR%\rea_switch.log ^
  && goto :eof

:fallback_regex
REM 降级：直接从 config.yaml 正则读取（无 model_profiles 支持，使用旧逻辑）
echo [%date% %time%] llama_config.py not available, using regex fallback >> %PROJECT_DIR%\rea_switch.log

for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "$y = Get-Content '%PROJECT_DIR%\config.yaml' -Raw -Encoding UTF8; $m = [regex]::Match($y, '(?m)^\s*llama_model\s*:\s*"?(.+?)"?\s*$'); if ($m.Success) { $m.Groups[1].Value.Trim('"').Trim() } else { 'models/default.gguf' }"`) do set "MODEL_PATH=%%a"

for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "$y = Get-Content '%PROJECT_DIR%\config.yaml' -Raw -Encoding UTF8; $m = [regex]::Match($y, '(?m)^\s*llama_port\s*:\s*"?(\d+)"?\s*$'); if ($m.Success) { $m.Groups[1].Value } else { '8080' }"`) do set "PORT=%%a"

for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "$y = Get-Content '%PROJECT_DIR%\config.yaml' -Raw -Encoding UTF8; $m = [regex]::Match($y, '(?m)^\s*llama\s*:\s*$'); if (-not $m.Success) { '150000' } else { $s = $y.Substring($m.Index); $m2 = [regex]::Match($s, '(?m)^\s*context\s*:\s*(\d+)'); if ($m2.Success) { $m2.Groups[1].Value } else { '150000' } }"`) do set "CTX=%%a"

for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "$y = Get-Content '%PROJECT_DIR%\config.yaml' -Raw -Encoding UTF8; $m = [regex]::Match($y, '(?m)^\s*llama\s*:\s*$'); if (-not $m.Success) { '2048' } else { $s = $y.Substring($m.Index); $m2 = [regex]::Match($s, '(?m)^\s*batch_size\s*:\s*(\d+)'); if ($m2.Success) { $m2.Groups[1].Value } else { '2048' } }"`) do set "BATCH=%%a"

for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "$y = Get-Content '%PROJECT_DIR%\config.yaml' -Raw -Encoding UTF8; $m = [regex]::Match($y, '(?m)^\s*llama\s*:\s*$'); if (-not $m.Success) { '1024' } else { $s = $y.Substring($m.Index); $m2 = [regex]::Match($s, '(?m)^\s*ubatch_size\s*:\s*(\d+)'); if ($m2.Success) { $m2.Groups[1].Value } else { '1024' } }"`) do set "UBATCH=%%a"

for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "$y = Get-Content '%PROJECT_DIR%\config.yaml' -Raw -Encoding UTF8; $m = [regex]::Match($y, '(?m)^\s*llama\s*:\s*$'); if (-not $m.Success) { '24' } else { $s = $y.Substring($m.Index); $m2 = [regex]::Match($s, '(?m)^\s*threads\s*:\s*(\d+)'); if ($m2.Success) { $m2.Groups[1].Value } else { '24' } }"`) do set "THREADS=%%a"

for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "$y = Get-Content '%PROJECT_DIR%\config.yaml' -Raw -Encoding UTF8; $m = [regex]::Match($y, '(?m)^\s*llama\s*:\s*$'); if (-not $m.Success) { '3000' } else { $s = $y.Substring($m.Index); $m2 = [regex]::Match($s, '(?m)^\s*cache_ram\s*:\s*(\d+)'); if ($m2.Success) { $m2.Groups[1].Value } else { '3000' } }"`) do set "CACHE_RAM=%%a"

for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "$y = Get-Content '%PROJECT_DIR%\config.yaml' -Raw -Encoding UTF8; $m = [regex]::Match($y, '(?m)^\s*llama\s*:\s*$'); if (-not $m.Success) { 'q8_0' } else { $s = $y.Substring($m.Index); $m2 = [regex]::Match($s, '(?m)^\s*ctk\s*:\s*"?(\S+?)"?\s*$'); if ($m2.Success) { $m2.Groups[1].Value.Trim('"') } else { 'q8_0' } }"`) do set "CTK=%%a"

for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "$y = Get-Content '%PROJECT_DIR%\config.yaml' -Raw -Encoding UTF8; $m = [regex]::Match($y, '(?m)^\s*llama\s*:\s*$'); if (-not $m.Success) { 'q8_0' } else { $s = $y.Substring($m.Index); $m2 = [regex]::Match($s, '(?m)^\s*ctv\s*:\s*"?(\S+?)"?\s*$'); if ($m2.Success) { $m2.Groups[1].Value.Trim('"') } else { 'q8_0' } }"`) do set "CTV=%%a"

for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "$y = Get-Content '%PROJECT_DIR%\config.yaml' -Raw -Encoding UTF8; $m = [regex]::Match($y, '(?m)^\s*llama\s*:\s*$'); if (-not $m.Success) { '41' } else { $s = $y.Substring($m.Index); $m2 = [regex]::Match($s, '(?m)^\s*ngl\s*:\s*(\d+)'); if ($m2.Success) { $m2.Groups[1].Value } else { '41' } }"`) do set "NGL=%%a"

for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "$y = Get-Content '%PROJECT_DIR%\config.yaml' -Raw -Encoding UTF8; $m = [regex]::Match($y, '(?m)^\s*llama_log_dir\s*:\s*"?(.+?)"?\s*$'); if ($m.Success) { $m.Groups[1].Value.Trim('"').Trim() } else { 'llama-server\restart-logs' }"`) do set "LOG_DIR=%%a"

REM ========== MTP 自动检测 ==========
set "MTP_EXTRA="
for /f "usebackq tokens=1,2" %%a in (`powershell -NoProfile -Command "$y = Get-Content '%PROJECT_DIR%\config.yaml' -Raw -Encoding UTF8; $mn = [regex]::Match($y, '(?m)^\s*llama_model_name\s*:\s*"?(.+?)"?\s*$'); if ($mn.Success) { $n = $mn.Groups[1].Value.Trim('"').Trim() } else { $mp = [regex]::Match($y, '(?m)^\s*llama_model\s*:\s*"?(.+?)"?\s*$'); if ($mp.Success) { $n = [System.IO.Path]::GetFileNameWithoutExtension($mp.Groups[1].Value.Trim('"').Trim()) } else { $n = '' } }; $s = $n -match 'mtp'; $mtpN = 1; $m = [regex]::Match($y, '(?m)^\s*llama\s*:\s*$'); if ($m.Success) { $s2 = $y.Substring($m.Index); $m2 = [regex]::Match($s2, '(?m)^\s*spec_draft_n_max\s*:\s*(\d+)'); if ($m2.Success) { $mtpN = $m2.Groups[1].Value } }; if ($s) { Write-Output (\"1 $mtpN\") } else { Write-Output '0 0' }"`) do set "MTP_ENABLED=%%a" & set "MTP_N=%%b"
if "!MTP_ENABLED!"=="1" (
    echo MTP model detected: adding --spec-type draft-mtp --spec-draft-n-max !MTP_N!
    set "MTP_EXTRA=--spec-type draft-mtp --spec-draft-n-max !MTP_N!"
)

REM ========== 关掉 llama ==========
taskkill /f /im llama-server.exe >nul 2>&1
echo Stopped llama, waiting for port release...
:wait_stop
timeout /t 1 /nobreak >nul
curl -s http://127.0.0.1:%PORT%/health >nul 2>&1
if not errorlevel 1 goto wait_stop
echo Port %PORT% released.

REM ========== 启动 llama ==========
set "LLM_ARGS=-m "%MODEL_PATH%" -c %CTX% --flash-attn on -ctk %CTK% -ctv %CTV% --no-mmap --cpu-moe --batch-size %BATCH% --ubatch-size %UBATCH% --threads %THREADS% -ngl %NGL% -rea %REA_MODE% --reasoning-format deepseek --jinja --cache-ram %CACHE_RAM% --parallel 1 --kv-unified --no-mmap --port %PORT% --timeout 600"
if defined MTP_EXTRA set "LLM_ARGS=!LLM_ARGS! !MTP_EXTRA!"
start "" /B %PROJECT_DIR%\llama-server\llama-server.exe !LLM_ARGS! > "%PROJECT_DIR%!LOG_DIR!\llama-rea-out.log" 2>&1

echo Started llama with -rea %REA_MODE%, port=%PORT%, waiting for ready...

:wait_ready
timeout /t 2 /nobreak >nul
curl -s http://127.0.0.1:%PORT%/health | findstr "ok" >nul 2>&1
if errorlevel 1 goto wait_ready

echo [%date% %time%] llama ready with -rea %REA_MODE% >> %PROJECT_DIR%\rea_switch.log
echo DONE: -rea %REA_MODE%