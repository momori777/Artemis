# AI Girlfriend 四季夏目 — 一键路径配置脚本
# 自动检测已安装的工具路径，没找到的交互式填写，最终生成 config.yaml
#
# 用法: powershell -ExecutionPolicy Bypass -File quick_setup.ps1

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI Girlfriend 四季夏目 — 一键路径向导" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# 0. Language Selection: ZH / JA / EN
# ============================================================
Write-Host "--- Default Agent Language ---" -ForegroundColor Green
$lang = ""
while ($lang -notmatch '^[123]$') {
    Write-Host ""
    Write-Host "  [1] Chinese (AGENTS.md) - current default" -ForegroundColor White
    Write-Host "  [2] Japanese (AGENTS_JA.md)" -ForegroundColor White
    Write-Host "  [3] English (AGENTS_EN.md)" -ForegroundColor White
    Write-Host ""
    Write-Host "Select default Agent language (enter 1/2/3): " -NoNewline -ForegroundColor Yellow
    $input = Read-Host
    if ($input -match '^[123]$') {
        $lang = $input
    } else {
        Write-Host "  Invalid input, please enter 1, 2, or 3" -ForegroundColor Red
    }
}

$selectedAgent = "AGENTS.md"
$langLabel = "ZH"
$langMap = @{
    "1" = @{ Agent="AGENTS.md";     Label="ZH" }
    "2" = @{ Agent="AGENTS_JA.md";  Label="JA" }
    "3" = @{ Agent="AGENTS_EN.md";  Label="EN" }
}
$selectedAgent = $langMap[$lang].Agent
$langLabel = $langMap[$lang].Label

# 将选定的 AGENTS 文件复制为 DEFAULT_AGENT.md
$defaultAgentPath = Join-Path $scriptDir "DEFAULT_AGENT.md"
if (Test-Path (Join-Path $scriptDir $selectedAgent)) {
    Copy-Item (Join-Path $scriptDir $selectedAgent) $defaultAgentPath -Force
    Write-Host ""
    Write-Host "  Set default Agent: $langLabel -> DEFAULT_AGENT.md" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  Warning: $selectedAgent not found, keeping current DEFAULT_AGENT.md" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "正在扫描已安装的工具……" -ForegroundColor Yellow
Write-Host ""

# ============================================================
# 辅助函数
# ============================================================
function Find-Exe($name, $searchPaths) {
    foreach ($dir in $searchPaths) {
        $candidate = Join-Path $dir $name
        if (Test-Path $candidate) { return $candidate }
        # 也递归一层
        try {
            $found = Get-ChildItem $dir -Filter $name -Recurse -Depth 2 -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) { return $found.FullName }
        } catch {}
    }
    return $null
}

function Find-Dir($name, $searchRoots) {
    foreach ($root in $searchRoots) {
        try {
            $found = Get-ChildItem $root -Directory -Filter $name -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) { return $found.FullName }
        } catch {}
    }
    return $null
}

function Prompt-Path($label, $default, $hint) {
    if ($hint) { Write-Host "  $hint" -ForegroundColor DarkGray }
    $val = Read-Host "$label"
    if (-not $val) { $val = $default }
    if ($val) { Write-Host "    -> $val" -ForegroundColor Green }
    else { Write-Host "    -> (未设置)" -ForegroundColor DarkGray }
    return $val
}

# ============================================================
# 搜索根目录
# ============================================================
$desktop = [Environment]::GetFolderPath("Desktop")
$searchRoots = @("C:\", "D:\", "E:\", $desktop, $env:USERPROFILE, "$env:USERPROFILE\Desktop\vllm")
$defaultLlamaLogDir = "$desktop\vllm\restart-logs"

# ============================================================
# 1. OpenClaw workspace（手动输入）
# ============================================================
Write-Host "--- OpenClaw Workspace ---" -ForegroundColor Green
Write-Host "  请输入你准备存放所有 AI 文件的「工作区」目录路径。" -ForegroundColor White
Write-Host "  例如: D:\Artemis_demo\workspace" -ForegroundColor DarkGray
Write-Host "  建议选一个单独的目录，不要和其他项目混用。" -ForegroundColor DarkGray

# 默认建议
$workspacePrompt = Prompt-Path "  Workspace 路径" "$env:USERPROFILE\.openclaw\workspace" "按 Enter 使用默认，或输入自定义路径"
$workspace = $workspacePrompt
if (-not (Test-Path $workspace)) {
    Write-Host "  目录不存在，自动创建..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $workspace -ErrorAction SilentlyContinue | Out-Null
}
Write-Host "  workspace: $workspace" -ForegroundColor $(if (Test-Path $workspace) { 'Green' } else { 'Red' })

# 媒体目录（基于用户输入的 workspace）
$mediaAudio = Join-Path $workspace "media\qqbot\audio"
$mediaImages = Join-Path $workspace "media\qqbot\images"
# 确保存在
New-Item -ItemType Directory -Force -Path $mediaAudio -ErrorAction SilentlyContinue | Out-Null
New-Item -ItemType Directory -Force -Path $mediaImages -ErrorAction SilentlyContinue | Out-Null
Write-Host "  audio out: $mediaAudio" -ForegroundColor Green
Write-Host "  image out: $mediaImages" -ForegroundColor Green

# ============================================================
# 2. ComfyUI（自动检测 + 手动补填）
# ============================================================
Write-Host ""
Write-Host "--- ComfyUI ---" -ForegroundColor Green

$comfyuiRoot = Find-Dir "ComfyUI" $searchRoots
$comfyuiPython = Find-Exe "python.exe" @("$comfyuiRoot\..\python", "$comfyuiRoot\python", "E:\comfyui\ComfyUI-aki-v3\python")
$comfyuiCheckpoints = if ($comfyuiRoot) { Join-Path $comfyuiRoot "models\checkpoints" } else { $null }
$comfyuiConfigure = Find-Exe "A绘世启动器.exe" @("$comfyuiRoot\..", "$comfyuiRoot\..\..", "E:\comfyui\ComfyUI-aki-v3")

if (-not $comfyuiRoot) {
    Write-Host "  未自动检测到 ComfyUI，请手动填写：" -ForegroundColor Yellow
    $comfyuiRoot = Prompt-Path "  ComfyUI 根目录 (含 models/checkpoints/)" $null ""
    $comfyuiPython = Prompt-Path "  Python 路径 (秋叶整合包: .../python/python.exe)" $null ""
    $comfyuiCheckpoints = Prompt-Path "  checkpoints 目录" $null ""
    $comfyuiConfigure = Prompt-Path "  A绘世启动器.exe (秋叶整合包一键启动)" $null ""
} else {
    $comfyuiCheckpoints = if ($comfyuiRoot) { Join-Path $comfyuiRoot "models\checkpoints" } else { $null }
    Write-Host "  root:      $comfyuiRoot" -ForegroundColor $(if (Test-Path $comfyuiRoot) { 'Green' } else { 'Yellow' })
    Write-Host "  python:    $comfyuiPython" -ForegroundColor $(if (Test-Path $comfyuiPython) { 'Green' } else { 'Yellow' })
    Write-Host "  ckpt dir:  $comfyuiCheckpoints" -ForegroundColor $(if (Test-Path $comfyuiCheckpoints) { 'Green' } else { 'Yellow' })
    Write-Host "  launcher:  $comfyuiConfigure" -ForegroundColor $(if ($comfyuiConfigure -and (Test-Path $comfyuiConfigure)) { 'Green' } else { 'DarkGray' })
    # 没找到的单独问
    if (-not $comfyuiConfigure) {
        $comfyuiConfigure = Prompt-Path "  A绘世启动器.exe (秋叶整合包一键启动，可跳过)" $null ""
    }
}

# ============================================================
# 3. GPT-SoVITS v2 Pro（自动检测 + 手动补填）
# ============================================================
Write-Host ""
Write-Host "--- GPT-SoVITS v2 Pro (TTS) ---" -ForegroundColor Green

$sovitsRoot = Find-Dir "GPT-SoVITS-v2pro*" $searchRoots
if (-not $sovitsRoot) { $sovitsRoot = Find-Dir "GPT-SoVITS*" $searchRoots }
$sovitsPython = if ($sovitsRoot) { Join-Path $sovitsRoot "runtime\python.exe" } else { $null }

if (-not $sovitsRoot) {
    Write-Host "  未自动检测到 GPT-SoVITS，请手动填写：" -ForegroundColor Yellow
    $sovitsRoot = Prompt-Path "  GPT-SoVITS 安装目录" $null ""
    $sovitsPython = Prompt-Path "  runtime/python.exe 完整路径" $null ""
} else {
    Write-Host "  root:   $sovitsRoot" -ForegroundColor $(if (Test-Path $sovitsRoot) { 'Green' } else { 'Yellow' })
    Write-Host "  python: $sovitsPython" -ForegroundColor $(if (Test-Path $sovitsPython) { 'Green' } else { 'Yellow' })
}

# ============================================================
# 4. llama.cpp（自动检测 + 手动补填）
# ============================================================
Write-Host ""
Write-Host "--- llama.cpp (本地 LLM) ---" -ForegroundColor Green

$llamaExe = Find-Exe "llama-server.exe" $searchRoots
$llamaModel = Find-Exe "*.gguf" $searchRoots  # 可能有多个，取第一个

# 如果有 vllm 目录
$vllmDir = Find-Dir "vllm" $searchRoots
if (-not $vllmDir) { $vllmDir = Find-Dir "vllm" @($desktop) }
$llamaLogDir = if ($vllmDir) { Join-Path $vllmDir "restart-logs" } else { $defaultLlamaLogDir }
$restartScript = Find-Exe "restart-llama.ps1" @($vllmDir, "$workspace\skills\shared")

if (-not $llamaExe) {
    Write-Host "  未自动检测到 llama.cpp，请手动填写：" -ForegroundColor Yellow
    $llamaExe = Prompt-Path "  llama-server.exe 路径" $null ""
    $llamaModel = Prompt-Path "  GGUF 模型文件路径" $null ""
    $llamaLogDir = Prompt-Path "  日志目录" $defaultLlamaLogDir ""
    $restartScript = Prompt-Path "  restart-llama.ps1 路径" $null ""
} else {
    Write-Host "  exe:     $llamaExe" -ForegroundColor $(if (Test-Path $llamaExe) { 'Green' } else { 'Yellow' })
    Write-Host "  model:   $llamaModel" -ForegroundColor $(if ($llamaModel -and (Test-Path $llamaModel)) { 'Green' } else { 'Yellow' })
    Write-Host "  log dir: $llamaLogDir" -ForegroundColor Green
    Write-Host "  restart: $restartScript" -ForegroundColor $(if ($restartScript -and (Test-Path $restartScript)) { 'Green' } else { 'DarkGray' })
    # 模型可能有多个
    if ($llamaModel -and (Test-Path $llamaModel)) {
        # 只取第一个
    } else {
        # 让用户选
        $llamaModel = Prompt-Path "  GGUF 模型文件路径 (检测到多个或路径不对)" $llamaModel ""
    }
    if (-not $restartScript) {
        $restartScript = Prompt-Path "  restart-llama.ps1 路径 (可跳过，使用内置降级重启)" $null ""
    }
}

# ============================================================
# 5. Memory & Embedding（自动检测 + 手动补填）
# ============================================================
Write-Host ""
Write-Host "--- Memory & Embedding ---" -ForegroundColor Green

# 角色记忆目录
$roleMemoryDir = Join-Path $workspace "memory\role_play"
if (-not (Test-Path $roleMemoryDir)) { New-Item -ItemType Directory -Force -Path $roleMemoryDir -ErrorAction SilentlyContinue | Out-Null }

# Mem0 Qdrant 向量库
$mem0QdrantDir = Join-Path $workspace "skills\sakura\data\memory\qdrant"

# mem0 bridge 脚本
$mem0Bridge = Join-Path $workspace "skills\shared\mem0_bridge.py"
$mem0SyncCron = Join-Path $workspace "skills\shared\mem0_sync_cron.py"

# Embedding Server 路径
$embeddingDir = Find-Dir "all-MiniLM-L6-v2" $searchRoots
if (-not $embeddingDir) {
    $embeddingDir = Find-Dir "all-MiniLM-L6-v2" @("$workspace\models", "$ScriptDir\models", "$desktop\vllm\models")
}
$embeddingServer = Find-Exe "start_embedding_server.ps1" @($workspace, "$workspace\skills\shared")
if (-not $embeddingServer) { $embeddingServer = Join-Path $workspace "skills\shared\start_embedding_server.ps1" }

Write-Host "  role_memory:   $roleMemoryDir" -ForegroundColor $(if (Test-Path $roleMemoryDir) { 'Green' } else { 'Yellow' })
Write-Host "  mem0_qdrant:   $mem0QdrantDir" -ForegroundColor $(if (Test-Path $mem0QdrantDir) { 'Green' } else { 'Yellow' })
Write-Host "  mem0_bridge:   $mem0Bridge" -ForegroundColor $(if (Test-Path $mem0Bridge) { 'Green' } else { 'Yellow' })
Write-Host "  mem0_sync:     $mem0SyncCron" -ForegroundColor $(if (Test-Path $mem0SyncCron) { 'Green' } else { 'Yellow' })
Write-Host "  embedding_dir: $embeddingDir" -ForegroundColor $(if ($embeddingDir -and (Test-Path $embeddingDir)) { 'Green' } else { 'DarkGray' })
Write-Host "  embed_server:  $embeddingServer" -ForegroundColor $(if (Test-Path $embeddingServer) { 'Green' } else { 'DarkGray' })

# ============================================================
# 6. 生成 config.yaml
# ============================================================
Write-Host ""
Write-Host "生成 config.yaml..." -ForegroundColor Cyan

# 确保路径用双反斜杠
$esc = { param($p) if ($p) { $p.Replace('\', '\\') } else { '' } }

$yaml = @"
# AI Girlfriend 四季夏目 - 路径配置文件
# 由 quick_setup.ps1 自动生成 $(Get-Date -Format 'yyyy-MM-dd HH:mm')
# 重新运行 quick_setup.ps1 可修改路径

# ============================================================
# OpenClaw workspace (agent 工作区)
# ============================================================
workspace: "$(& $esc $workspace)"

# ============================================================
# 媒体输出目录 (qqbot channel 的发文件目录)
# ============================================================
media_qqbot_audio: "$(& $esc $mediaAudio)"
media_qqbot_images: "$(& $esc $mediaImages)"

# ============================================================
# ComfyUI 文生图
# ============================================================
comfyui_root: "$(& $esc $comfyuiRoot)"
comfyui_python: "$(& $esc $comfyuiPython)"
comfyui_checkpoints_dir: "$(& $esc $comfyuiCheckpoints)"
comfyui_temp_output_dir: "$workspace\comfyui"
comfyui_launcher: "$(& $esc $comfyuiConfigure)"

# ============================================================
# GPT-SoVITS v2 Pro (TTS)
# ============================================================
sovits_root: "$(& $esc $sovitsRoot)"
sovits_python: "$(& $esc $sovitsPython)"
tts_temp_output_dir: "$workspace\media\qqbot\audio"

# ============================================================
# llama.cpp (本地 LLM)
# ============================================================
llama_exe: "$(& $esc $llamaExe)"
llama_model: "$(& $esc $llamaModel)"
llama_log_dir: "$(& $esc $llamaLogDir)"
restart_script: "$(& $esc $restartScript)"
llama_port: 8080

# ============================================================
# Memory & Embedding（长期记忆 + 向量库 + 文本压缩）
# ============================================================
role_memory_dir: "$(& $esc $roleMemoryDir)"
mem0_qdrant_dir: "$(& $esc $mem0QdrantDir)"
mem0_bridge: "$(& $esc $mem0Bridge)"
mem0_sync_cron: "$(& $esc $mem0SyncCron)"
embedding_dir: "$(& $esc $embeddingDir)"
embedding_server: "$(& $esc $embeddingServer)"

# ============================================================
# Headroom SmartCrusher + CCR 配置（长期记忆整理参数）
# ============================================================
headroom:
  smart_crusher:
    min_tokens_to_crush: 150
    max_items_after_crush: 10
    first_fraction: 0.3
    last_fraction: 0.1
    variance_threshold: 2.0
    preserve_change_points: true
  ccr:
    max_entries: 500
    ttl_seconds: 300
"@

$configPath = Join-Path $scriptDir "config.yaml"
Set-Content -Path $configPath -Value $yaml -Encoding UTF8

# ============================================================
# 6. 验证总结
# ============================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  config.yaml 已生成: $configPath" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$checks = @(
    @{Label="ComfyUI root";    Path=$comfyuiRoot},
    @{Label="ComfyUI python";  Path=$comfyuiPython},
    @{Label="ComfyUI ckpt";    Path=$comfyuiCheckpoints},
    @{Label="ComfyUI launcher";Path=$comfyuiConfigure},
    @{Label="SovITS root";     Path=$sovitsRoot},
    @{Label="SovITS python";   Path=$sovitsPython},
    @{Label="llama exe";       Path=$llamaExe},
    @{Label="llama model";     Path=$llamaModel},
    @{Label="workspace";       Path=$workspace},
    @{Label="media audio";     Path=$mediaAudio},
    @{Label="media images";    Path=$mediaImages},
    @{Label="llama log dir";   Path=$llamaLogDir},
    @{Label="role memory";     Path=$roleMemoryDir},
    @{Label="mem0 qdrant";     Path=$mem0QdrantDir},
    @{Label="mem0 bridge";     Path=$mem0Bridge},
    @{Label="mem0 sync cron";  Path=$mem0SyncCron},
    @{Label="embedding dir";   Path=$embeddingDir},
    @{Label="embed server";    Path=$embeddingServer}
)

$ok = 0
$bad = 0
Write-Host "路径验证:" -ForegroundColor Yellow
foreach ($c in $checks) {
    if ($c.Path -and (Test-Path $c.Path)) {
        Write-Host "  [OK]   $($c.Label)" -ForegroundColor Green
        $ok++
    } elseif ($c.Path) {
        Write-Host "  [MISS] $($c.Label): $($c.Path)" -ForegroundColor Red
        $bad++
    } else {
        Write-Host "  [SKIP] $($c.Label) (未设置)" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "结果: $ok 个就绪, $bad 个缺失" -ForegroundColor $(if ($bad -eq 0) { 'Green' } else { 'Yellow' })

if ($bad -gt 0) {
    Write-Host ""
    Write-Host "缺失路径请手动编辑 config.yaml 补充。" -ForegroundColor Yellow
    Write-Host "或重新运行: powershell -ExecutionPolicy Bypass -File quick_setup.ps1" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "所有路径验证通过！" -ForegroundColor Green
    Write-Host "下一步: 运行 download-models.ps1 下载模型" -ForegroundColor White
}

Write-Host ""
Write-Host "降级重启 llama: .\skills\shared\restart_llama_degraded.ps1" -ForegroundColor DarkGray
