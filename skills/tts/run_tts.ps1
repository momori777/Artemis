param(
    [string]$text,
    [string]$lang = 'ja',
    [string]$mood = 'auto',
    [string]$character = ''
)

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8

# ========== 从 config.yaml 读取路径 ==========
$workspaceRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$configPath = Join-Path $workspaceRoot 'config.yaml'
if (-not (Test-Path $configPath)) {
    Write-Output "FAILED: config.yaml not found at $configPath"
    Write-Output "Please run quick_setup.ps1 first to configure paths."
    exit 1
}
$configRaw = Get-Content $configPath -Raw -Encoding UTF8

# 辅助函数：从 YAML 提取简单标量值
function Get-YamlValue($raw, $key) {
    $pattern = "(?m)^\s*${key}\s*:\s*`"?(.+?)`"?\s*$"
    $m = [regex]::Match($raw, $pattern)
    if ($m.Success) { return $m.Groups[1].Value.Trim('"').Trim() }
    return $null
}

$sovitsPython = Get-YamlValue $configRaw 'sovits_python'
$ttsScript = Join-Path $PSScriptRoot 'tts_call.py'  # always alongside this script
$mediaDir = Get-YamlValue $configRaw 'media_qqbot_audio'
if (-not $mediaDir) { $mediaDir = Join-Path $workspaceRoot 'media\qqbot\audio' }

$taskId = 'tts_' + (Get-Date -Format 'yyyyMMddHHmmss') + '_' + (Get-Random -Minimum 1000 -Maximum 9999)
$flagDir = Join-Path $workspaceRoot '.task_flags'
$flagFile = Join-Path $flagDir "$taskId.done"
mkdir $flagDir -Force -ErrorAction SilentlyContinue | Out-Null
mkdir $mediaDir -Force -ErrorAction SilentlyContinue | Out-Null

$env:PYTHONIOENCODING = 'utf-8'
$env:HF_ENDPOINT = 'https://hf-mirror.com'

# Pass character selection to Python (TTS_CHARACTER + REF_WAVS_DIR env vars)
if ($character) {
    $env:TTS_CHARACTER = $character
    # Map frontend charId to ref_wavs directory name (some use different spelling)
    $charToRefDir = @{
        'natsume' = 'ref_wavs'
        'atori'   = 'ref_wavs_atri'
        'sakura'  = 'ref_wavs_sakura'
        'enola'   = 'ref_wavs'
        'ruruka'  = 'ref_wavs'
    }
    $charRefDirName = $charToRefDir[$character]
    if (-not $charRefDirName) { $charRefDirName = "ref_wavs_$character" }
    $charRefDir = Join-Path $PSScriptRoot $charRefDirName
    if (Test-Path $charRefDir) {
        $env:REF_WAVS_DIR = $charRefDir
        Write-Output "[CHAR] Using ref_wavs: $charRefDir"
    } else {
        Write-Output "[CHAR] No $charRefDirName dir, using default"
    }
}

# Run TTS - stderr has [LOCK]/[LLAMA] logs, stdout has the wav path
$rawOutput = & $sovitsPython $ttsScript $text $lang $mood 2>$null
# Extract the path from stdout — match absolute Windows paths ending in .wav
$wavCandidates = $rawOutput | Where-Object { $_ -match '^[A-Za-z]:\\' -and $_ -match '\.wav$' }
$wavPath = ($wavCandidates | Select-Object -Last 1) -replace '^\s+|\s+$',''

# Fallback: if extraction failed but Python exited ok, find newest wav in media dir
if ((-not $wavPath) -and ($LASTEXITCODE -eq 0)) {
    $fallback = Get-ChildItem $mediaDir -Filter '*.wav' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($fallback) {
        $wavAge = [int]((Get-Date) - $fallback.LastWriteTime).TotalSeconds
        if ($wavAge -lt 300) {
            $wavPath = $fallback.FullName
        }
    }
}

if ($wavPath -and (Test-Path $wavPath)) {
    $mediaFile = Join-Path $mediaDir ('tts_' + (Get-Date -Format 'yyyyMMddHHmmss') + '.wav')
    Copy-Item $wavPath $mediaFile -Force -ErrorAction Stop
    @{status='ok';file=$mediaFile;type='tts'} | ConvertTo-Json -Compress | Set-Content $flagFile

    # === Live2D Lip-Sync: send audio to bridge for real mouth animation ===
    $syncScript = Join-Path $PSScriptRoot 'live2d_sync.py'
    if (Test-Path $syncScript) {
        try {
            $syncResult = & $sovitsPython $syncScript $mediaFile --text $text --no-wait 2>$null
            Write-Output "[SYNC] $syncResult"
        } catch {
            Write-Output "[SYNC] Live2D sync skipped (bridge offline or error)"
        }
    }

    Write-Output "DONE: $mediaFile"
} else {
    Write-Output "FAILED: exit=$LASTEXITCODE wavPath=[$wavPath] rawLines=$($rawOutput.Count)"

    # TTS failed, ensure llama is restarted
    Write-Output 'Restarting llama after failed TTS run...'
    $restartScript = Get-YamlValue $configRaw 'restart_script'
    if ($restartScript -and (Test-Path $restartScript)) {
        & $restartScript
    }
}
