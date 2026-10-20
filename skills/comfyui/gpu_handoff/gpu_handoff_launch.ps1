<#
  Register a ONE-SHOT scheduled task that runs gpu_handoff_run.ps1 detached.

  WHY A SCHEDULED TASK AND NOT exec:
    gpu_handoff_run.ps1 kills the LLM engine that is answering you. Anything started
    as a child of your own exec turn dies with it (or gets reaped), so the job would
    never reach the "restart the LLM" step. Task Scheduler owns the process instead.

  Usage (run from anywhere; paths are resolved from this script's own folder):
    powershell -ExecutionPolicy Bypass -File skills/comfyui/gpu_handoff/gpu_handoff_launch.ps1
    ... -DelaySec 30 -Prefix myjob
    ... -WorkflowJson <path to an API-format workflow json> -Prefix myjob -TaskName MyHandoff

  After launching: the agent is unreachable for ~1-3 min. Read
    skills/comfyui/gpu_handoff/logs/gpu_handoff_result.json
  to get the result once it is back.
#>
param(
    [string]$WorkflowJson = (Join-Path $PSScriptRoot 'workflow_sdxl_example.json'),
    [string]$Prefix       = 'agenttest',
    [string]$TaskName     = 'ComfyGpuHandoff',
    [int]$DelaySec        = 45,
    [Nullable[DateTime]]$At = $null,
    [switch]$SkipJob
)

$ErrorActionPreference = 'Stop'

$runPs  = Join-Path $PSScriptRoot 'gpu_handoff_run.ps1'
$logDir = Join-Path $PSScriptRoot 'logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
if (-not (Test-Path $runPs))  { throw "missing $runPs" }
if (-not (Test-Path $WorkflowJson)) { throw "missing workflow json: $WorkflowJson" }

# A .cmd wrapper avoids schtasks quoting hell (nested quotes inside /tr are unreliable).
$cmd = Join-Path $logDir "$TaskName.cmd"
$skip = if ($SkipJob) { ' -SkipJob' } else { '' }
"@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$runPs`" -WorkflowJson `"$WorkflowJson`" -Prefix $Prefix -TaskName $TaskName$skip`r`n" |
  Set-Content $cmd -Encoding ASCII

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
"workflow  : $WorkflowJson"
"prefix    : $Prefix  (SaveImage filename_prefix must match)"
"skip job  : $SkipJob"
"result    : $(Join-Path $logDir 'gpu_handoff_result.json')"
"run log   : $(Join-Path $logDir 'gpu_handoff_run.log')"
""
"NOTE: the LLM engine goes down at trigger time and comes back ~1-3 min later."
"      The task deletes itself in the script's finally block."
