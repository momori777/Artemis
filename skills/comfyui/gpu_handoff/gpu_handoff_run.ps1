<#
  GPU handoff orchestrator: pause the local LLM engine so ComfyUI can have the whole
  GPU, run ONE workflow, then bring the LLM back up.

  WHY THIS EXISTS
    The LLM engine that serves this very session holds the GPU resident, so ComfyUI
    cannot start while it is up - and killing that engine kills the session that asked
    for the job. So this script must NOT be run by exec inside a live agent turn:
    launch it detached (see gpu_handoff_launch.ps1).

  PATHS
    Nothing here is absolute. ComfyUI comes from config.yaml (comfyui_root /
    comfyui_python), the LLM engine from strata_dir / strata_config / strata_port.
    config.yaml is gitignored, so per-machine paths stay out of the repo.
    A gitignored gpu_handoff.local.ps1 next to this script may set $ComfyRoot /
    $StrataDir / $StrataConfig for a checkout that has no config.yaml.

  MEASURED (2026-10-20, one workflow 832x1216 / 25 steps): ~2 min 18 s total,
    of which ~70 s is the LLM being unavailable.

  ASCII-only comments: Windows PowerShell 5.1 reads .ps1 as ANSI without a BOM.
#>
param(
    # API-format (not UI-format) workflow JSON. Node ids must be "1".."n".
    [string]$WorkflowJson = (Join-Path $PSScriptRoot 'workflow_sdxl_example.json'),
    # SaveImage filename_prefix inside the workflow JSON; used to find the output file.
    [string]$Prefix       = 'agenttest',
    [string]$TaskName     = 'ComfyGpuHandoff',
    # Optional overrides; default is read from config.yaml.
    [string]$ComfyRoot    = '',
    [string]$ComfyPython  = '',
    [string]$StrataDir    = '',
    [string]$StrataConfig = '',
    [string]$LogDir       = (Join-Path $PSScriptRoot 'logs'),
    # Skip the run but still restart the engine (used when the pre-check fails).
    [switch]$SkipJob
)

$ErrorActionPreference = 'Continue'

# Per-machine overrides (gitignored): may pre-set $ComfyRoot / $StrataDir / $StrataConfig.
$local = Join-Path $PSScriptRoot 'gpu_handoff.local.ps1'
if (Test-Path $local) { . $local }

# ---- repo root: skills/comfyui/gpu_handoff -> three levels up ----
$repoRoot   = (Get-Item $PSScriptRoot).Parent.Parent.Parent.FullName
$configPath = Join-Path $repoRoot 'config.yaml'
if (-not (Test-Path $configPath) -and -not ($ComfyRoot -and $StrataDir -and $StrataConfig)) {
    throw "config.yaml not found at $configPath - either run quick_setup.ps1, or set ComfyRoot/StrataDir/StrataConfig (params or gpu_handoff.local.ps1)"
}
$configRaw = if (Test-Path $configPath) { Get-Content $configPath -Raw -Encoding UTF8 } else { '' }

# Same scalar helper as skills/comfyui/run_comfyui.ps1
function Get-YamlValue($raw, $key) {
    $pattern = "(?m)^\s*${key}\s*:\s*`"?(.+?)`"?\s*$"
    $m = [regex]::Match($raw, $pattern)
    if ($m.Success) { return $m.Groups[1].Value.Trim('"').Trim() }
    return $null
}

# ---- ComfyUI ----
$comfyDir  = if ($ComfyRoot) { $ComfyRoot } else { Get-YamlValue $configRaw 'comfyui_root' }
if (-not $comfyDir) { $comfyDir = Join-Path $repoRoot 'deps\ComfyUI' }
$comfyPy   = if ($ComfyPython) { $ComfyPython } else { Get-YamlValue $configRaw 'comfyui_python' }
if (-not $comfyPy) { $comfyPy = 'python' }
$comfyMain = Join-Path $comfyDir 'main.py'
$comfyOut  = Join-Path $comfyDir 'output'
$comfyPort = 8188
$cp = Get-YamlValue $configRaw 'comfyui_port'; if ($cp) { $comfyPort = [int]$cp }

# ---- LLM engine (Strata; llama.cpp is a separate backend on llama_port) ----
$llmPort   = 8080
$sp = Get-YamlValue $configRaw 'strata_port'; if ($sp) { $llmPort = [int]$sp }
$strataDir = if ($StrataDir) { $StrataDir } else { Get-YamlValue $configRaw 'strata_dir' }
if (-not $strataDir) { throw "config.yaml has no strata_dir - the LLM engine install dir (see skills/strata/SKILL.md)" }
$strataCfg = if ($StrataConfig) { $StrataConfig } else { Get-YamlValue $configRaw 'strata_config' }
if (-not $strataCfg) { throw 'config.yaml has no strata_config - the engine launch config file' }
if (-not [System.IO.Path]::IsPathRooted($strataCfg)) { $strataCfg = Join-Path $strataDir $strataCfg }
$strataPy  = Join-Path $strataDir '.venv\Scripts\python.exe'
if (-not (Test-Path $strataPy)) { $strataPy = 'python' }
$strataSvc = Join-Path $strataDir 'serve\server.py'

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
$log      = Join-Path $LogDir 'gpu_handoff_run.log'
$resultF  = Join-Path $LogDir 'gpu_handoff_result.json'
$comfyLog = Join-Path $LogDir 'comfyui.log'

function Say($m) { "$(Get-Date -Format 's') $m" | Add-Content $log }
function PortListening($p) { [bool](Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue) }
function Wait-PortFree($p, $tries) { for ($i = 0; $i -lt $tries; $i++) { if (-not (PortListening $p)) { return $true }; Start-Sleep 1 }; return $false }

$imgPath = ''
$status  = 'start'
$note    = ''

Say "=== gpu_handoff start (wf=$WorkflowJson prefix=$Prefix comfy=$comfyDir llm=$llmPort) ==="
try {
    if (-not (Test-Path $WorkflowJson)) { throw "workflow json not found: $WorkflowJson" }

    if ($SkipJob) {
        $status = 'skipped'
        $note   = 'SkipJob set, only restarting the engine'
        Say "SKIP: $note"
        throw 'skip-requested'
    }

    # ---- 1. pause the LLM so the GPU is released ----
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -like "*$strataSvc*" } |
      ForEach-Object { Say "stop LLM PID $($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Get-CimInstance Win32_Process -Filter "Name='strata.exe'" -ErrorAction SilentlyContinue |
      ForEach-Object { Say "stop strata.exe PID $($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    if (-not (Wait-PortFree $llmPort 60)) { Say "WARN: $llmPort still listening after 60 s" }
    Say "LLM paused ($llmPort free: $(-not (PortListening $llmPort)))"

    # ---- 2. start ComfyUI ----
    if (-not (Test-Path $comfyMain)) { throw "ComfyUI main.py not found: $comfyMain (check config.yaml comfyui_root)" }
    Remove-Item $comfyLog,"$comfyLog.err" -Force -ErrorAction SilentlyContinue
    Start-Process -FilePath $comfyPy -ArgumentList "`"$comfyMain`"","--port","$comfyPort" `
      -WorkingDirectory $comfyDir -WindowStyle Hidden `
      -RedirectStandardOutput $comfyLog -RedirectStandardError "$comfyLog.err"
    Say 'ComfyUI launching...'
    $up = $false
    for ($i = 0; $i -lt 150; $i++) {
        Start-Sleep 2
        try { if (Invoke-RestMethod "http://127.0.0.1:$comfyPort/system_stats" -TimeoutSec 4) { $up = $true; Say "ComfyUI up after $($i*2) s"; break } } catch {}
    }
    if (-not $up) { throw "ComfyUI did not come up on $comfyPort within 300 s (see $comfyLog.err)" }

    # ---- 3. queue the workflow ----
    $body = '{"prompt": ' + (Get-Content $WorkflowJson -Raw) + '}'
    $r = Invoke-RestMethod "http://127.0.0.1:$comfyPort/prompt" -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 20
    $promptId = $r.prompt_id
    Say "queued prompt $promptId"

    # ---- 4. wait for completion ----
    $done = $false
    for ($i = 0; $i -lt 180; $i++) {
        Start-Sleep 5
        try {
            $h = Invoke-RestMethod "http://127.0.0.1:$comfyPort/history/$promptId" -TimeoutSec 10
            if ($h.$promptId) { $done = $true; Say "history ready after $($i*5) s"; break }
        } catch { Say "history poll err: $($_.Exception.Message)" }
    }
    if (-not $done) { throw 'workflow did not finish within 900 s' }

    $img = Get-ChildItem $comfyOut -Filter "$Prefix*.png" -File -ErrorAction SilentlyContinue |
      Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $img) { throw "finished but no $Prefix*.png found in $comfyOut" }
    $imgPath = $img.FullName
    Say "OUTPUT: $imgPath ($([math]::Round($img.Length/1MB,2)) MB)"
    $status = 'ok'
}
catch {
    if ($status -ne 'skipped') { $status = 'fail' }
    if (-not $note) { $note = $_.Exception.Message }
    Say "ERROR: $($_.Exception.Message)"
}
finally {
    # ---- 5. give the GPU back, then restart the LLM (always) ----
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -like "*$comfyMain*" } |
      ForEach-Object { Say "stop ComfyUI PID $($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    if (-not (Wait-PortFree $comfyPort 60)) { Say "WARN: $comfyPort still listening after 60 s" }
    Say "ComfyUI stopped ($comfyPort free: $(-not (PortListening $comfyPort)))"
    Start-Sleep 5

    Start-Process -FilePath $strataPy -ArgumentList @("`"$strataSvc`"","--engine","strata","--config","`"$strataCfg`"","--port","$llmPort") `
      -WorkingDirectory $strataDir -WindowStyle Hidden
    Say 'LLM engine relaunched, waiting for model load...'
    for ($i = 0; $i -lt 240; $i++) {
        Start-Sleep 1
        try { if (Invoke-RestMethod "http://127.0.0.1:$llmPort/v1/models" -TimeoutSec 3) { Say "LLM back up after $i s"; break } } catch {}
    }
    Say "LLM up: $(PortListening $llmPort)"

    [pscustomobject]@{
        status   = $status
        image    = $imgPath
        note     = $note
        finished = (Get-Date -Format 's')
    } | ConvertTo-Json -Compress | Set-Content $resultF
    Say "=== gpu_handoff end ($status) ==="
    if ($TaskName) { cmd /c "schtasks /delete /tn $TaskName /f >nul 2>nul" }
}
