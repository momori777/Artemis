#!/usr/bin/env bash
# download-models.sh
# AI Girlfriend 四季夏目 — One-click model download script (Linux / macOS)
#
# Downloads all 5 model files (~31.7 GB) from HuggingFace
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
echo "║  $HF_REPO                                          ║"
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
    echo "    export HF_TOKEN=\\
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
echo "Total: ~31.7 GB — this may take 30-90 minutes depending on network"
echo ""

# Model file list: repo_path|local_path|description
MODELS=(
    "llm/LuffyTheFoxQwen3.6-35B-A3B-Uncensored-Genesis-Hermes-V3-GGUF.gguf|LuffyTheFoxQwen3.6-35B-A3B-Uncensored-Genesis-Hermes-V3-GGUF.gguf|LLM GGUF — LuffyTheFox Genesis Hermes V3 (16.11 GB)"
    "comfyui-checkpoints/WAI-Nsfw-Illustrious-17.safetensors|comfyui-checkpoints/WAI-Nsfw-Illustrious-17.safetensors|ComfyUI Checkpoint — WAI (6.46 GB)"
    "comfyui-checkpoints/miaomiaoHarem_v20.safetensors|comfyui-checkpoints/miaomiaoHarem_v20.safetensors|ComfyUI Checkpoint — Miaomiao (6.46 GB)"
    "gpt-sovits-weights/GPT_weights_v2Pro/xxx-e30.ckpt|gpt-sovits-weights/GPT_weights_v2Pro/xxx-e30.ckpt|GPT-SoVITS ckpt (~155 MB)"
    "gpt-sovits-weights/SoVITS_weights_v2Pro/xxx_e20_s6240.pth|gpt-sovits-weights/SoVITS_weights_v2Pro/xxx_e20_s6240.pth|GPT-SoVITS pth (~135 MB)"
    "live2d-model/shiki_natsume.tar.gz|live2d-model/shiki_natsume.tar.gz|Live2D Model — Shiki Natsume (~209 MB)"
)

TOTAL=${#MODELS[@]}
CURRENT=0
FAILED=()

for ENTRY in "${MODELS[@]}"; do
    CURRENT=$((CURRENT + 1))
    IFS='|' read -r REPO_PATH LOCAL_PATH DESC <<< "$ENTRY"
    FULL_LOCAL="$BASE_DIR/$LOCAL_PATH"
    
    # Check if already exists
    if [ -f "$FULL_LOCAL" ]; then
        echo "[$CURRENT/$TOTAL] $DESC — already exists, skipping"
        continue
    fi
    
    echo "[$CURRENT/$TOTAL] Downloading $DESC..."
    echo "         From: $REPO_PATH"
    echo "         To:   $FULL_LOCAL"
    
    START=$(date +%s)
    
    if $HF_CMD download "$HF_REPO" "$REPO_PATH" --local-dir "$BASE_DIR" --local-dir-use-symlinks False; then
        END=$(date +%s)
        ELAPSED=$((END - START))
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
