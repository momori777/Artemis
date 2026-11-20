#!/usr/bin/env bash
# download-models.sh
# AI Girlfriend 四季夏目 — One-click model download script (Linux / macOS)
#
# Downloads the same model set as download-models.ps1 (~72 GB):
#   LLM x3 + ComfyUI x6 (WAI + qwen-image/anima suite) + SoVITS x2 + Live2D archive
# Requires: huggingface-cli (pip install huggingface_hub)
#
# Usage:
#   bash download-models.sh                 # download into ./ (project-relative layout)
#   bash download-models.sh /path/to/base   # download into another base directory
#   MODEL_DIR=/data/models bash download-models.sh    # put the GGUFs elsewhere
#   bash download-models.sh --dry-run       # show the plan, touch nothing
#
# First-time setup:
#   huggingface-cli login
#   or export HF_TOKEN="hf_xxx..."

set -euo pipefail

usage() {
    sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
}

# ---- arguments -------------------------------------------------------------
BASE_DIR="."
DRY_RUN=0
for ARG in "$@"; do
    case "$ARG" in
        --dry-run|-n) DRY_RUN=1 ;;
        -h|--help) usage; exit 0 ;;
        -*) echo "[ERROR] unknown option: $ARG" >&2; usage; exit 2 ;;
        *) BASE_DIR="$ARG" ;;
    esac
done

# 国内用户通过 hf-mirror.com 加速下载
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"

HF_REPO="TAOTAO777/ai-girlfriend-natsume"
if [[ "$DRY_RUN" -eq 1 ]]; then
    # dry run must not create anything, so resolve without mkdir
    if [[ -d "$BASE_DIR" ]]; then
        BASE_DIR="$(cd "$BASE_DIR" && pwd)"
    elif [[ "$BASE_DIR" == /* || "$BASE_DIR" =~ ^[A-Za-z]:[\\/] ]]; then
        :  # already absolute — keep as typed
    else
        BASE_DIR="$(pwd)/$BASE_DIR"
    fi
else
    BASE_DIR="$(mkdir -p "$BASE_DIR" && cd "$BASE_DIR" && pwd)"
fi
# LLM GGUF 目录：MODEL_DIR 优先，否则 <BASE_DIR>/llm（与 download-models.ps1 一致）
LLM_DIR="${MODEL_DIR:-$BASE_DIR/llm}"
if [[ "$LLM_DIR" != /* && ! "$LLM_DIR" =~ ^[A-Za-z]:[\\/] ]]; then
    LLM_DIR="$BASE_DIR/$LLM_DIR"
fi

echo "╔══════════════════════════════════════════════════════╗"
echo "║  AI Girlfriend — 四季夏目 · Model Downloader         ║"
printf '║  %-52s║\n' "$HF_REPO"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY RUN — nothing will be downloaded, nothing will be written."
    HF_CMD="(dry-run)"
else
    # ---- huggingface CLI detection ------------------------------------------
    if command -v huggingface-cli &>/dev/null; then
        HF_CMD="huggingface-cli"
    elif command -v hf &>/dev/null; then
        HF_CMD="hf"
    elif python3 -m huggingface_hub --help &>/dev/null 2>&1; then
        HF_CMD="python3 -m huggingface_hub"
    elif python -m huggingface_hub --help &>/dev/null 2>&1; then
        HF_CMD="python -m huggingface_hub"
    else
        echo "[ERROR] huggingface-cli not found. Install: pip install huggingface_hub"
        exit 1
    fi
    echo "Download tool: $HF_CMD"

    # ---- auth (public repo downloads without it) ----------------------------
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
fi

# ---- target directories (same layout as the PowerShell script) -------------
if [[ "$DRY_RUN" -eq 0 ]]; then
    for DIR in \
        "$LLM_DIR" \
        "$BASE_DIR/comfyui/checkpoints" \
        "$BASE_DIR/comfyui/diffusion_models" \
        "$BASE_DIR/comfyui/text_encoders" \
        "$BASE_DIR/comfyui/vae" \
        "$BASE_DIR/gpt-sovits-weights/GPT_weights_v2Pro" \
        "$BASE_DIR/gpt-sovits-weights/SoVITS_weights_v2Pro" \
        "$BASE_DIR/live2d-model" \
        "$BASE_DIR/live2d/model"; do
        mkdir -p "$DIR"
    done
fi

echo ""
echo "Download directory: $BASE_DIR"
echo "LLM directory:      $LLM_DIR"
echo "Target: $HF_REPO"
echo "Total: ~72 GB (LLM x3 + ComfyUI x6 [WAI + qwen-image/anima 套件] + SoVITS + Live2D) — may take 30-90 min"
echo ""

# ---- model list: repo|repo_path|local_path|description ---------------------
# 与 download-models.ps1 保持一致（同样 11 个文件 + Live2D 归档）。
# ComfyUI 除 WAI (SDXL/Illustrious) 外均为 qwen-image/anima 架构，共用 qwen_image_vae。
MODELS=(
    "llm/Hermes3.6-35B-A3B-Uncensored-Genesis-Final-MTP-APEX.gguf|$LLM_DIR/Hermes3.6-35B-A3B-Uncensored-Genesis-Final-MTP-APEX.gguf|LLM GGUF — Hermes3.6-35B-A3B Genesis Final MTP APEX (~24.9 GB, 主模型)"
    "llm/Qwen3.8-27B-Ultimate-Heretic-Uncn-Turbo-Brilli-50x-AGI-NEO-MTP-Q4_K_M.gguf|$LLM_DIR/Qwen3.8-27B-Ultimate-Heretic-Uncn-Turbo-Brilli-50x-AGI-NEO-MTP-Q4_K_M.gguf|LLM GGUF — Qwen3.8-27B Ultimate Heretic MTP Q4_K_M (~15.7 GB, 工具模型, 24G显存级)"
    "llm/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic-Q4_K_M.gguf|$LLM_DIR/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic-Q4_K_M.gguf|LLM GGUF — DeepSeek-V4-Pro-Qwen3.5-9B heretic Q4_K_M (~6.1 GB, 8G显存可全装)"
    "comfyui/checkpoints/WAI-Nsfw-Illustrious-17.safetensors|$BASE_DIR/comfyui/checkpoints/WAI-Nsfw-Illustrious-17.safetensors|ComfyUI Checkpoint — WAI SDXL/Illustrious (6.46 GB)"
    "comfyui/diffusion_models/miaomiaoHarem_29BBETA10.safetensors|$BASE_DIR/comfyui/diffusion_models/miaomiaoHarem_29BBETA10.safetensors|ComfyUI Diffusion — Miaomiao Harem 29B anima/qwen (5.44 GB)"
    "comfyui/diffusion_models/oneObsession_anima29BV1.safetensors|$BASE_DIR/comfyui/diffusion_models/oneObsession_anima29BV1.safetensors|ComfyUI Diffusion — oneObsession anima 29B (5.44 GB)"
    "comfyui/diffusion_models/qwen-image-2.1-Q6_K.gguf|$BASE_DIR/comfyui/diffusion_models/qwen-image-2.1-Q6_K.gguf|ComfyUI Diffusion GGUF — qwen-image-2.1 Q6_K (5.47 GB)"
    "comfyui/text_encoders/qwen3vl_8b_int8_convrot.safetensors|$BASE_DIR/comfyui/text_encoders/qwen3vl_8b_int8_convrot.safetensors|ComfyUI Text Encoder — qwen3vl_8b int8 convrot (8.71 GB, qwen-image-2.1 用)"
    "comfyui/vae/qwen_image_vae.safetensors|$BASE_DIR/comfyui/vae/qwen_image_vae.safetensors|ComfyUI VAE — qwen_image_vae (242 MB, 所有非 WAI 模型共用)"
    "gpt-sovits-weights/GPT_weights_v2Pro/xxx-e30.ckpt|$BASE_DIR/gpt-sovits-weights/GPT_weights_v2Pro/xxx-e30.ckpt|GPT-SoVITS ckpt (155 MB)"
    "gpt-sovits-weights/SoVITS_weights_v2Pro/xxx_e20_s6240.pth|$BASE_DIR/gpt-sovits-weights/SoVITS_weights_v2Pro/xxx_e20_s6240.pth|GPT-SoVITS pth (135 MB)"
)

# Live2D 归档单独处理（tar.gz 需要解压，与 .ps1 相同）
LIVE2D_REPO_PATH="live2d-model/shiki_natsume.tar.gz"
LIVE2D_ARCHIVE="$BASE_DIR/live2d-model/shiki_natsume.tar.gz"
LIVE2D_EXTRACT_DIR="$BASE_DIR/live2d/model"
LIVE2D_MARKER="$LIVE2D_EXTRACT_DIR/shiki_natsume/final/shiki_natsume.model3.json"
LIVE2D_DESC="Live2D Model — Shiki Natsume (~209 MB)"

TOTAL=$(( ${#MODELS[@]} + 1 ))
CURRENT=0
FAILED=()

# download_one <repo_path> <local_path> <download_dir> <description>
download_one() {
    local REPO_PATH="$1" LOCAL_PATH="$2" DOWNLOAD_DIR="$3" DESC="$4"
    local START END ELAPSED LEAF CAND

    echo "         From: $HF_REPO/$REPO_PATH"
    echo "         To:   $LOCAL_PATH"
    START=$(date +%s)

    mkdir -p "$DOWNLOAD_DIR"
    if $HF_CMD download "$HF_REPO" "$REPO_PATH" --local-dir "$DOWNLOAD_DIR"; then
        END=$(date +%s); ELAPSED=$((END - START))
        # 落点可能带 repo 子路径（llm/ …），移动/覆盖到目标位置
        if [[ ! -f "$LOCAL_PATH" ]]; then
            LEAF="$(basename "$REPO_PATH")"
            for CAND in "$DOWNLOAD_DIR/$REPO_PATH" "$DOWNLOAD_DIR/$LEAF"; do
                if [[ -f "$CAND" ]]; then
                    mkdir -p "$(dirname "$LOCAL_PATH")"
                    mv -f "$CAND" "$LOCAL_PATH"
                    break
                fi
            done
        fi
        echo "         OK (${ELAPSED}s)"
        return 0
    fi
    END=$(date +%s); ELAPSED=$((END - START))
    echo "         FAILED (${ELAPSED}s)"
    return 1
}

# ---- regular files ---------------------------------------------------------
for ENTRY in "${MODELS[@]}"; do
    CURRENT=$((CURRENT + 1))
    IFS='|' read -r REPO_PATH LOCAL_PATH DESC <<< "$ENTRY"

    if [[ -f "$LOCAL_PATH" ]]; then
        echo "[$CURRENT/$TOTAL] $DESC — already exists, skipping"
        continue
    fi

    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "[$CURRENT/$TOTAL] would download $DESC"
        echo "         From: $HF_REPO/$REPO_PATH"
        echo "         To:   $LOCAL_PATH"
        continue
    fi

    echo "[$CURRENT/$TOTAL] Downloading $DESC..."
    if ! download_one "$REPO_PATH" "$LOCAL_PATH" "$(dirname "$LOCAL_PATH")" "$DESC"; then
        FAILED+=("$DESC")
    fi
    echo ""
done

# ---- Live2D archive (download + extract) -----------------------------------
CURRENT=$((CURRENT + 1))
if [[ -f "$LIVE2D_MARKER" ]]; then
    echo "[$CURRENT/$TOTAL] $LIVE2D_DESC — already exists, skipping"
elif [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[$CURRENT/$TOTAL] would download $LIVE2D_DESC"
    echo "         From: $HF_REPO/$LIVE2D_REPO_PATH"
    echo "         To:   $LIVE2D_ARCHIVE  →  extract to $LIVE2D_EXTRACT_DIR"
else
    echo "[$CURRENT/$TOTAL] Downloading $LIVE2D_DESC..."
    if download_one "$LIVE2D_REPO_PATH" "$LIVE2D_ARCHIVE" "$BASE_DIR" "$LIVE2D_DESC"; then
        echo "         Extracting to $LIVE2D_EXTRACT_DIR ..."
        if tar -xzf "$LIVE2D_ARCHIVE" -C "$LIVE2D_EXTRACT_DIR"; then
            echo "         Extracted OK"
        else
            echo "         Extract FAILED"
            FAILED+=("$LIVE2D_DESC (extract)")
        fi
    else
        FAILED+=("$LIVE2D_DESC")
    fi
    echo ""
fi

# ---- summary ---------------------------------------------------------------
echo "══════════════════════════════════════════════════════"
SUCCESS=$((TOTAL - ${#FAILED[@]}))
echo "Done: $SUCCESS / $TOTAL items"

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
    if [[ "$LLM_DIR" != "$BASE_DIR/llm" ]]; then
        echo "  (LLM GGUFs: $LLM_DIR)"
    fi
    echo ""
    echo "Next step: open models.yaml and update local_path fields"
    echo "to match your directory structure."
fi
