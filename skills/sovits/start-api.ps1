# GPT-SoVITS v2Pro API 启动脚本
# 使用 v2Pro 底模 + 自定义训练模型
# 启动后通过 http://127.0.0.1:9880/tts 调用

$baseDir = $PSScriptRoot

# 设置 GPT 和 SoVITS 模型路径
$gptModel = "$baseDir\GPT_weights_v2Pro\xxx-e30.ckpt"
$sovitsModel = "$baseDir\SoVITS_weights_v2Pro\xxx_e20_s6240.pth"

Write-Host "=== GPT-SoVITS v2Pro API Server ===" -ForegroundColor Cyan
Write-Host "GPT Model: $gptModel"
Write-Host "SoVITS Model: $sovitsModel"
Write-Host "API URL: http://127.0.0.1:9880/tts" -ForegroundColor Green
Write-Host ""

# 启动 api_v2.py，加载指定模型
$env:SOVITS_PATH = $sovitsModel
$env:GPT_PATH = $gptModel

Set-Location $baseDir
python api_v2.py -a 127.0.0.1 -p 9880
