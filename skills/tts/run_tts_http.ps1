#requires -Version 5.1
<#
.SYNOPSIS
    GPT-SoVITS HTTP TTS 调用脚本 — 不停 llama 版本
.DESCRIPTION
    通过 HTTP API 调用 GPT-SoVITS，不依赖 llama_lifecycle 模块，不停 llama-server。
    自动启动 GPT-SoVITS HTTP 服务（如果未运行在 9880 端口）。
.PARAMETER Text
    待朗读文本（中文/日文/英文）
.PARAMETER Lang
    语言代码: zh=中文, ja=日文(默认), en=英文, yue=粤语, ko=韩文
.PARAMETER Mood
    情绪模式: casual=日常温柔, tsundere=傲娇, romantic=深情, long=长句稳定, random=随机
.PARAMETER RefAudio
    可选：指定参考音频路径。不指定则自动根据文本情绪选择。
.PARAMETER Width, Height, Steps, Cfg, Checkpoint
    预留参数（兼容旧版 run_tts.ps1 调用签名，目前忽略）
.EXAMPLE
    .\run_tts_http.ps1 -Text "おはようございます" -Lang ja -Mood casual
.EXAMPLE
    .\run_tts_http.ps1 -Text "你好世界" -Lang zh
#>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Text,

    [Parameter(Position=1)]
    [string]$Lang = "ja",

    [Parameter(Position=2)]
    [string]$Mood = "random",

    [string]$RefAudio = "",

    [int]$Width = 0,
    [int]$Height = 0,
    [int]$Steps = 0,
    [double]$Cfg = 0,
    [string]$Checkpoint = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PythonScript = Join-Path $ScriptDir "tts_http_call.py"

# 构建 Python 参数
$PythonArgs = @($PythonScript, $Text, $Lang)
if ($Mood -and $Mood -ne "random") {
    $PythonArgs += $Mood
}
if ($RefAudio) {
    $PythonArgs += $RefAudio
}

# 执行 Python 脚本
Write-Host "[TTS-HTTP] 开始 TTS 合成 (Text=$Text, Lang=$Lang)" -ForegroundColor Cyan

$Output = & python $PythonArgs 2>&1
$ExitCode = $LASTEXITCODE

# 输出 stderr 信息
$Output | Where-Object { $_ -is [string] -and $_ -match '^\[' } | ForEach-Object {
    Write-Host $_ -ForegroundColor DarkGray
}

# 提取 stdout 路径（最后一行纯路径）
$CleanOutput = $Output | Where-Object { $_ -is [string] }
$WavPath = $CleanOutput | Where-Object { $_ -match '^C:\\.*\.wav$' } | Select-Object -Last 1

if ($WavPath) {
    Write-Host "[TTS-HTTP] DONE: $WavPath" -ForegroundColor Green
    Write-Output $WavPath
} elseif ($ExitCode -ne 0) {
    Write-Host "[TTS-HTTP] FAILED (exit code: $ExitCode)" -ForegroundColor Red
    Write-Output "FAILED"
    exit $ExitCode
} else {
    Write-Host "[TTS-HTTP] FAILED (no wav path found)" -ForegroundColor Red
    Write-Output "FAILED"
    exit 1
}
