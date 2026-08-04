param(
    [Parameter(Mandatory = $true)]
    [string]$audio
)

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8

# ========== 从 config.yaml 读取路径 ==========
$workspaceRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$configPath = Join-Path $workspaceRoot 'config.yaml'
if (-not (Test-Path $configPath)) {
    Write-Output "FAILED: config.yaml not found at $configPath"
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

# ASR 用 Python 3.14（不指定特定 conda env，系统 python 即可）
$pythonExe = 'python'
$asrScript = Join-Path $PSScriptRoot 'asr_call.py'

$mediaDir = Get-YamlValue $configRaw 'media_qqbot_audio'
if (-not $mediaDir) { $mediaDir = Join-Path $workspaceRoot 'media\qqbot\audio' }

# 验证音频文件存在
if (-not (Test-Path $audio)) {
    Write-Output "FAILED: audio file not found: $audio"
    exit 1
}

Write-Output "[ASR PS] 音频: $audio"

$env:PYTHONIOENCODING = 'utf-8'

# Run ASR - stdout 是识别出的文本
$rawOutput = & $pythonExe $asrScript $audio 2>$null

# 提取 stdout 文本（第一行通常是识别结果）
$asrText = $null
foreach ($line in $rawOutput) {
    $trimmed = $line.Trim()
    if ($trimmed -and -not ($trimmed -like 'FAILED*') -and -not ($trimmed -like 'ERROR*')) {
        $asrText = $trimmed
        break
    }
}

if ($LASTEXITCODE -eq 0) {
    if ($asrText) {
        Write-Output "DONE: $asrText"
    } else {
        Write-Output "DONE: (empty)"
    }
} else {
    Write-Output "FAILED: exit=$LASTEXITCODE"
}
