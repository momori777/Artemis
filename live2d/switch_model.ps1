# Live2D model switcher
param([string]$Character)

$live2d_dir = $PSScriptRoot  # this script lives in live2d/

$switches = @{
    atri    = @{ model = "/model/atri/atri.model3.json"; title = "ATRI - yatoli" }
    natsume = @{ model = "/model/shiki_natsume/final/shiki_natsume.model3.json"; title = "shiki natsume" }
}

$info = $switches[$Character]
if (-not $info) {
    Write-Output "[ERROR] Unknown: $Character. Use: atri, natsume"
    exit 1
}

$index = Join-Path $live2d_dir "index.html"
$backup = Join-Path $live2d_dir "index_previous.html"
Copy-Item $index $backup -Force -ErrorAction SilentlyContinue

$content = Get-Content $index -Raw -Encoding UTF8
$content = $content -replace "var MODEL='.+?'", "var MODEL='$($info.model)'"
$content = $content -replace "<title>.*?</title>", "<title>$($info.title)</title>"
Set-Content $index $content -Encoding UTF8

Write-Output "[OK] Switched to $($info.title)"
Write-Output "Model: $($info.model)"
