#!/usr/bin/env bash
# download-models.sh
# AI Girlfriend 四季夏目 — One-click model download script (Linux / macOS)
#
# Downloads all model files (~59 GB) from HuggingFace
# Requires: huggingface-cli (pip install huggingface_hub)
#
# Usage:
#   bash download-models.sh
#   bash download-models.sh /path/to/models
#
# First-time setup:
#   huggingface-cli login
#   or export HF_TOKEN="hf_xxx..."

set -euo pipefail

# 国内用户通过 hf-mirror.com 加速下载
export HF_ENDPOINT="https://hf-mirror.com"

HF_REPO="TAOTAO777/ai-girlfriend-natsume"
BASE_DIR="${1:-.}"
BASE_DIR="$(mkdir -p "$BASE_DIR" && cd "$BASE_DIR" && pwd)"

echo "╔══════════════════════════════════════════════════════╗"
echo "║  AI Girlfriend — 四季夏目 · Model Downloader         ║"
echo "║ $HF_REPO                                          ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Check huggingface-cli
if command -v huggingface-cli &>/dev/null; then
    HF_CMD="huggingface-cli"
elif command -v hf &>/dev/null; then
    HF_CMD="hf"
elif python3 -m huggingface_hub &>/dev/null 2>&1; then
    HF_CMD="python3 -m huggingface_hub"
elif python -m huggingface_hub &>/dev/null 2>&1; then
    HF_CMD="python -m huggingface_hub"
else
    echo "[ERROR] huggingface-cli not found. Install: pip install huggingface_hub"
    exit 1
fi

echo "Download tool: $HF_CMD"

# Check auth
echo -n "Checking auth... "
AUTH_OK=false
if $HF_CMD auth whoami &>/dev/null; then
    AUTH_OK=true
elif [[ -n "${HF_TOKEN:-}" ]] && curl -sH "Authorization: Bearer $HF_TOKEN" https://huggingface.co/api/whoami &>/dev/null; then
    AUTH_OK=true
fi
if $AUTH_OK; then
    echo "OK"
else
    echo "WARNING (download will still work for public repos)"
    echo "  For gated models, set HF_TOKEN:"
    echo "    export HF_TOKEN=\"hf_xxx...\""
fi

# Create target directories
mkdir -p "$BASE_DIR/llm"
mkdir -p "$BASE_DIR/comfyui-checkpoints"
mkdir -p "$BASE_DIR/gpt-sovits-weights/GPT_weights_v2Pro"
mkdir -p "$BASE_DIR/gpt-sovits-weights/SoVITS_weights_v2Pro"
mkdir -p "$BASE_DIR/live2d-model"

echo ""
echo "Download directory: $BASE_DIR"
echo "Target: $HF_REPO"
echo "Total: ~59 GB — this may take 30-90 minutes depending on network"
echo ""

# Model file list: repo|repo_path|local_path|description
# LLM 模型为本地文件（绝对路径）; 若缺失会尝试从 HF 补下载并移动到目标路径
# repo 字段可指向外部仓库 (如 Ternary-Bonsai PTQ1_0)，缺省仓库为 TAOTAO777/ai-girlfriend-natsume
MODELS=(
    "TAOTAO777/ai-girlfriend-natsume|llm/Hermes3.6-35B-A3B-Uncensored-Genesis-Final-MTP-APEX.gguf|E:/model3/Hermes3.6-35B-A3B-Uncensored-Genesis-Final-MTP-APEX.gguf|LLM GGUF — Hermes3.6-35B-A3B Genesis Final MTP APEX (~24.9 GB, 主模型)"
    "TAOTAO777/ai-girlfriend-natsume|llm/Qwen3.8-27B-TTURBO-Fable-C-Fusion-709-L-Uncen-NM-DAU-NEO-MTP-Q4_K_M.gguf|C:/model2/Qwen3.8-27B-TTURBO-Fable-C-Fusion-709-L-Uncen-NM-DAU-NEO-MTP-Q4_K_M.gguf|LLM GGUF — Qwen3.8-27B TTURBO Fable C-Fusion MTP Q4_K_M (~15.7 GB, 工具模型)"
    # Ternary-Bonsai PTQ1_0: 自有仓库 llm/ 镜像; 8G 显存可全量装载 (-ngl 99)
    # 原出处: https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf (PTQ1_0 三重量化版: BoldingBuilds)
    # ⚠️ 启动时必须 -ctk q4_0 -ctv q4_0 且 -c <= 75000，否则 8G 显存装不下（调参详见 LLAMA_TUNING.md）
    "TAOTAO777/ai-girlfriend-natsume|llm/Ternary-Bonsai-2-27B-PTQ1_0.gguf|E:/model3/Ternary-Bonsai-2-27B-PTQ1_0.gguf|LLM GGUF — Ternary-Bonsai-2-27B PTQ1_0 (~5.9 GB, 8G显存可全装)"
    "TAOTAO777/ai-girlfriend-natsume|comfyui-checkpoints/WAI-Nsfw-Illustrious-17.safetensors|comfyui-checkpoints/WAI-Nsfw-Illustrious-17.safetensors|ComfyUI Checkpoint — WAI (6.46 GB)"
    "TAOTAO777/ai-girlfriend-natsume|comfyui-checkpoints/miaomiaoHarem_v20.safetensors|comfyui-checkpoints/miaomiaoHarem_v20.safetensors|ComfyUI Checkpoint — Miaomiao (6.46 GB)"
    "TAOTAO777/ai-girlfriend-natsume|gpt-sovits-weights/GPT_weights_v2Pro/xxx-e30.ckpt|gpt-sovits-weights/GPT_weights_v2Pro/xxx-e30.ckpt|GPT-SoVITS ckpt (~155 MB)"
    "TAOTAO777/ai-girlfriend-natsume|gpt-sovits-weights/SoVITS_weights_v2Pro/xxx_e20_s6240.pth|gpt-sovits-weights/SoVITS_weights_v2Pro/xxx_e20_s6240.pth|GPT-SoVITS pth (~135 MB)"
    "TAOTAO777/ai-girlfriend-natsume|live2d-model/shiki_natsume.tar.gz|live2d-model/shiki_natsume.tar.gz|Live2D Model — Shiki Natsume (~209 MB)"
)

TOTAL=${#MODELS[@]}
CURRENT=0
FAILED=()

for ENTRY in "${MODELS[@]}"; do
    CURRENT=$((CURRENT + 1))
    IFS='|' read -r REPO REPO_PATH LOCAL_PATH DESC <<< "$ENTRY"
    # 绝对路径（/ 开头或 Windows 盘符 X:）直接使用，否则相对 BASE_DIR
    if [[ "$LOCAL_PATH" == /* || "$LOCAL_PATH" =~ ^[A-Za-z]:[/\\] ]]; then
        FULL_LOCAL="$LOCAL_PATH"
        DOWNLOAD_DIR="$(dirname "$FULL_LOCAL")"
    else
        FULL_LOCAL="$BASE_DIR/$LOCAL_PATH"
        DOWNLOAD_DIR="$BASE_DIR"
    fi
    
    # Check if already exists
    if [ -f "$FULL_LOCAL" ]; then
        echo "[$CURRENT/$TOTAL] $DESC — already exists, skipping"
        continue
    fi
    
    echo "[$CURRENT/$TOTAL] Downloading $DESC..."
    echo "         From: $REPO/$REPO_PATH"
    echo "         To:   $FULL_LOCAL"
    
    START=$(date +%s)
    
    mkdir -p "$DOWNLOAD_DIR"
    if $HF_CMD download "$REPO" "$REPO_PATH" --local-dir "$DOWNLOAD_DIR" --local-dir-use-symlinks False; then
        END=$(date +%s)
        ELAPSED=$((END - START))
        # 下载落点可能带 repo 子路径 (llm/)，移动到目标位置
        if [ ! -f "$FULL_LOCAL" ]; then
            LEAF="$(basename "$REPO_PATH")"
            for CAND in "$DOWNLOAD_DIR/$REPO_PATH" "$DOWNLOAD_DIR/$LEAF"; do
                if [ -f "$CAND" ]; then
                    mkdir -p "$(dirname "$FULL_LOCAL")"
                    mv -f "$CAND" "$FULL_LOCAL"
                    break
                fi
            done
        fi
        echo "         OK (${ELAPSED}s)"
    else
        END=$(date +%s)
        ELAPSED=$((END - START))
        echo "         FAILED (${ELAPSED}s)"
        FAILED+=("$DESC")
    fi
    echo ""
done

# Summary
echo "══════════════════════════════════════════════════════"
SUCCESS=$((TOTAL - ${#FAILED[@]}))
echo "Done: $SUCCESS / $TOTAL models downloaded"

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    echo "Failed models (re-run to retry):"
    for f in "${FAILED[@]}"; do
        echo "  - $f"
    done
fi

if [ "$SUCCESS" -eq "$TOTAL" ]; then
    echo ""
    echo "All models downloaded to:"
    echo "  $BASE_DIR"
    echo ""
    echo "Next step: open models.yaml and update local_path fields"
    echo "to match your directory structure."
fi
