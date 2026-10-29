<#
  Register a ONE-SHOT scheduled task that runs tts_handoff_run.ps1 detached.

  WHY A SCHEDULED TASK AND NOT exec:
    tts_handoff_run.ps1 stops the LLM engine that is currently answering you. A child
    of your own exec turn dies together with the engine (or gets reaped), so the job
    would never reach its "restart the engine" step. Task Scheduler owns the process.

  Usage (run from anywhere; every path resolves from this script's own folder):
    powershell -ExecutionPolicy Bypass -File skills/sovits/tts_handoff_launch.ps1
    ... -TestIds atori-ja,natsume-ja -DelaySec 60
    ... -TaskName MyTtsHandoff -SkipJob      # -SkipJob only restarts the engine

  After launching: the agent is unreachable for a few minutes. Read
    skills/sovits/handoff_logs/tts_handoff_result.json
  for the verdict, and skills/sovits/handoff_logs/tts_e2e_result.json for per-case
  wav paths once the task has run.
#>
param(
    [string]$E2EScript = (Join-Path $PSScriptRoot 'tts_e2e_test.py'),
    [string]$TestIds   = '',
    [string]$TaskName  = 'SovitsTtsHandoff',
    [int]$DelaySec     = 60,
    [Nullable[DateTime]]$At = $null,
    [switch]$SkipJob
)

$ErrorActionPreference = 'Stop'

$runPs  = Join-Path $PSScriptRoot 'tts_handoff_run.ps1'
$logDir = Join-Path $PSScriptRoot 'handoff_logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
if (-not (Test-Path $runPs))  { throw "missing $runPs" }
if (-not $SkipJob -and -not (Test-Path $E2EScript)) { throw "missing e2e script: $E2EScript" }

# A .cmd wrapper avoids schtasks quoting hell (nested quotes inside /tr are unreliable).
$cmd = Join-Path $logDir "$TaskName.cmd"
$skip = if ($SkipJob) { ' -SkipJob' } else { '' }
$ids  = if ($TestIds) { " -TestIds `"$TestIds`"" } else { '' }
"@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$runPs`" -E2EScript `"$E2EScript`"$ids -TaskName $TaskName$skip`r`n" |
  Set-Content $cmd -Encoding ASCII

# Stale verdicts must not be mistaken for a fresh run.
foreach ($stale in @('tts_handoff_result.json', 'tts_e2e_result.json')) {
    Remove-Item (Join-Path $logDir $stale) -Force -ErrorAction SilentlyContinue
}

$start = if ($At) { $At } else { (Get-Date).AddSeconds($DelaySec) }
$st = $start.ToString('HH:mm')
$sd = $start.ToString('yyyy/MM/dd')

# Native schtasks writes to stderr; with ErrorActionPreference=Stop that becomes a
# terminating error, so quiet these calls explicitly via cmd.
cmd /c "schtasks /delete /tn $TaskName /f >nul 2>nul"
schtasks /create /tn $TaskName /tr "`"$cmd`"" /sc once /st $st /sd $sd /f | Out-Null
if (-not (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue)) {
    throw "scheduled task $TaskName was not created (check the /st $st /sd $sd time)"
}

"task      : $TaskName"
"runs at   : $($start.ToString('s'))"
"e2e       : $E2EScript"
"cases     : $(if ($TestIds) { $TestIds } else { 'all (atori-ja, atori-zh, natsume-ja, natsume-zh)' })"
"skip job  : $SkipJob"
"result    : $(Join-Path $logDir 'tts_handoff_result.json')"
"run log   : $(Join-Path $logDir 'tts_handoff_run.log')"
""
"NOTE: the LLM engine goes down at trigger time and comes back when the run finishes."
"      The task deletes itself in the script's finally block."
