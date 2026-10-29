<#
  GPU handoff orchestrator for GPT-SoVITS: pause the LLM engine (Strata) so the
  SoVITS api_v2 service can have the GPU, synthesize the end-to-end test lines for
  every requested character, then give the GPU back and bring the LLM engine up.

  WHY THIS EXISTS
    The LLM engine serving this very session holds the whole GPU (strata-iq3_s.json
    loads the model resident), and SoVITS needs ~4 GB of it. The api service also
    cannot be started from exec inside a live agent turn, because stopping the
    engine kills the turn that asked for the job and the "restart the engine" step
    would never run. So run this detached (see tts_handoff_launch.ps1).

  PATHS
    Nothing here is absolute except what config.yaml provides (strata_dir /
    strata_config / strata_port / sovits_python / tts_temp_output_dir).

  ASCII-ONLY comments: Windows PowerShell 5.1 reads .ps1 as ANSI without a BOM.
#>
param(
    [string]$TaskName     = 'SovitsTtsHandoff',
    [string]$E2EScript    = (Join-Path $PSScriptRoot 'tts_e2e_test.py'),
    [string]$TestIds      = '',            # comma separated ids; empty = all
    [string]$StrataDir    = '',
    [string]$StrataConfig = '',
    [string]$SovitsPython = '',
    [string]$LogDir       = (Join-Path $PSScriptRoot 'handoff_logs'),
    [switch]$SkipJob
)

$ErrorActionPreference = 'Continue'

$local = Join-Path $PSScriptRoot 'tts_handoff.local.ps1'
if (Test-Path $local) { . $local }

# ---- repo root: skills/sovits -> two levels up ----
$repoRoot   = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$configPath = Join-Path $repoRoot 'config.yaml'
if (-not (Test-Path $configPath)) { throw "config.yaml not found at $configPath" }
$configRaw = Get-Content $configPath -Raw -Encoding UTF8

function Get-YamlValue($raw, $key) {
    $pattern = "(?m)^\s*${key}\s*:\s*`"?(.+?)`"?\s*$"
    $m = [regex]::Match($raw, $pattern)
    if ($m.Success) { return $m.Groups[1].Value.Trim('"').Trim() }
    return $null
}

function PortListening($p) { [bool](Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue) }
function Wait-PortFree($p, $tries) { for ($i = 0; $i -lt $tries; $i++) { if (-not (PortListening $p)) { return $true }; Start-Sleep 1 }; return $false }
function Kill-ByCommandLine($needle, $msg) {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -and $_.CommandLine -like "*$needle*" -and $_.Name -match '\.(exe|py)$' } |
      ForEach-Object { Say "stop $msg PID $($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

# ---- LLM engine (Strata) ----
$llmPort   = 8080
$sp = Get-YamlValue $configRaw 'strata_port'; if ($sp) { $llmPort = [int]$sp }
$strataDir = if ($StrataDir) { $StrataDir } else { Get-YamlValue $configRaw 'strata_dir' }
if (-not $strataDir) { throw 'config.yaml has no strata_dir' }
$strataCfg = if ($StrataConfig) { $StrataConfig } else { Get-YamlValue $configRaw 'strata_config' }
if (-not $strataCfg) { throw 'config.yaml has no strata_config' }
if (-not [System.IO.Path]::IsPathRooted($strataCfg)) { $strataCfg = Join-Path $strataDir $strataCfg }
$strataPy  = Join-Path $strataDir '.venv\Scripts\python.exe'
if (-not (Test-Path $strataPy)) { $strataPy = 'python' }
$strataSvc = Join-Path $strataDir 'serve\server.py'

# ---- SoVITS ----
$sovitsRoot = Join-Path $repoRoot 'skills\sovits'
$apiV2      = Join-Path $sovitsRoot 'api_v2.py'
$sovitsPy   = if ($SovitsPython) { $SovitsPython } else { Get-YamlValue $configRaw 'sovits_python' }
if (-not $sovitsPy -or -not (Test-Path $sovitsPy)) { throw "sovits_python not usable: $sovitsPy" }
$ttsPort = 9880
$outDir  = Get-YamlValue $configRaw 'tts_temp_output_dir'
if (-not $outDir) { $outDir = Join-Path $repoRoot 'media\qqbot\audio' }

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
$log      = Join-Path $LogDir 'tts_handoff_run.log'
$resultF  = Join-Path $LogDir 'tts_handoff_result.json'
$reportF  = Join-Path $LogDir 'tts_e2e_result.json'
$apiLog   = Join-Path $LogDir 'api_v2.log'

function Say($m) { "$(Get-Date -Format 's') $m" | Add-Content $log }

$status = 'start'; $note = ''; $cases = @()

Say "=== tts_handoff start (sovits=$sovitsRoot port=$ttsPort llm=$llmPort ids='$TestIds') ==="
try {
    if ($SkipJob) { $status = 'skipped'; $note = 'SkipJob set, only restarting the engine'; throw 'skip-requested' }
    if (-not (Test-Path $apiV2))     { throw "api_v2.py not found: $apiV2" }
    if (-not (Test-Path $E2EScript)) { throw "e2e script not found: $E2EScript" }

    # ---- 1. pause the LLM so the GPU is released ----
    Kill-ByCommandLine $strataSvc 'strata server.py'
    Get-CimInstance Win32_Process -Filter "Name='strata.exe' or Name='strata-vision.exe'" -ErrorAction SilentlyContinue |
      ForEach-Object { Say "stop $($_.Name) PID $($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    if (-not (Wait-PortFree $llmPort 90)) { Say 'WARN: LLM port still listening after 90 s' }
    Say "LLM paused ($llmPort free: $(-not (PortListening $llmPort)))"

    # ---- 2. start api_v2 on the SoVITS venv (cwd = engine root, config.py lives there) ----
    $env:PYTHONIOENCODING = 'utf-8'
    $env:PYTHONPATH = "$sovitsRoot;$sovitsRoot\GPT_SoVITS" + $(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { '' })
    Remove-Item $apiLog,"$apiLog.err" -Force -ErrorAction SilentlyContinue
    Start-Process -FilePath $sovitsPy -ArgumentList "`"$apiV2`"","-a","127.0.0.1","-p",$ttsPort,"-c","GPT_SoVITS/configs/tts_infer.yaml" `
      -WorkingDirectory $sovitsRoot -WindowStyle Hidden `
      -RedirectStandardOutput $apiLog -RedirectStandardError "$apiLog.err"
    Say 'api_v2 launching (loads GPT + SoVITS + bert, expect 1-3 min)...'
    $up = $false
    for ($i = 0; $i -lt 300; $i++) {
        Start-Sleep 2
        try {
            $r = Invoke-WebRequest "http://127.0.0.1:$ttsPort/docs" -TimeoutSec 5 -UseBasicParsing
            if ($r.StatusCode -eq 200) { $up = $true; Say "api_v2 up after $($i*2) s"; break }
        } catch {}
    }
    if (-not $up) { throw "api_v2 did not come up on $ttsPort within 600 s (see $apiLog.err)" }

    # ---- 3. run the end-to-end checks (weights hot-swap + synthesis per character) ----
    $e2eArgs = @("`"$E2EScript`"", '--report', "`"$reportF`"")
    if ($TestIds) { $e2eArgs += @('--only', $TestIds) }
    $e2eLog = Join-Path $LogDir 'tts_e2e_run.log'
    Say "running e2e: python $($e2eArgs -join ' ')"
    & $sovitsPy @e2eArgs 2>&1 | Out-File -FilePath $e2eLog -Encoding UTF8
    Say "e2e exit code: $LASTEXITCODE"
    if (Test-Path $reportF) {
        $rep = Get-Content $reportF -Raw -Encoding UTF8 | ConvertFrom-Json
        $cases = $rep.cases
        if ($rep.fail -and $rep.ok) { $status = 'partial'; $note = "$($rep.ok) ok / $($rep.fail) fail" }
        elseif ($rep.fail)          { $status = 'fail';   $note = "all $($rep.fail) cases failed" }
        else                        { $status = 'ok' }
        foreach ($c in $cases) { Say ("case {0} ok={1} wav={2} sec={3} err={4}" -f $c.id, $c.ok, $c.wav, $c.seconds, $c.error) }
    } else {
        $status = 'fail'; $note = "no report json at $reportF (see $e2eLog)"
    }
}
catch {
    if ($status -ne 'skipped') { $status = 'fail' }
    if (-not $note) { $note = $_.Exception.Message }
    Say "ERROR: $($_.Exception.Message)"
}
finally {
    # ---- 4. stop api_v2, give the GPU back, restart the LLM engine (always) ----
    Kill-ByCommandLine 'api_v2.py' 'api_v2'
    if (-not (Wait-PortFree $ttsPort 60)) { Say "WARN: $ttsPort still listening after 60 s" }
    Say "api_v2 stopped ($ttsPort free: $(-not (PortListening $ttsPort)))"
    Start-Sleep 5

    Start-Process -FilePath $strataPy -ArgumentList @("`"$strataSvc`"","--engine","strata","--config","`"$strataCfg`"","--port","$llmPort") `
      -WorkingDirectory $strataDir -WindowStyle Hidden
    Say 'LLM engine relaunched, waiting for model load...'
    for ($i = 0; $i -lt 600; $i++) {
        Start-Sleep 1
        try { if (Invoke-RestMethod "http://127.0.0.1:$llmPort/v1/models" -TimeoutSec 3) { Say "LLM back up after $i s"; break } } catch {}
    }
    Say "LLM up: $(PortListening $llmPort)"

    [pscustomobject]@{
        status   = $status
        note     = $note
        cases    = $cases
        report   = $reportF
        out_dir  = $outDir
        llm_up   = (PortListening $llmPort)
        finished = (Get-Date -Format 's')
    } | ConvertTo-Json -Depth 6 -Compress | Set-Content $resultF -Encoding UTF8
    Say "=== tts_handoff end ($status) ==="
    if ($TaskName) { cmd /c "schtasks /delete /tn $TaskName /f >nul 2>nul" }
}
