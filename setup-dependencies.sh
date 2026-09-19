#!/bin/bash
# setup-dependencies.sh
# AI Girlfriend 四季夏目 — 自动下载 ComfyUI 和 GPT-SoVITS 源码
# 根据操作系统环境自动配置，无需手动安装整合包
#
# 用法: bash setup-dependencies.sh
#   -d /path/to/deps    (可选，默认安装在项目下的 deps 目录)
#   --skip-comfyui      (跳过 ComfyUI)
#   --skip-sovits       (跳过 GPT-SoVITS)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$SCRIPT_DIR/deps"
SKIP_COMFYUI=false
SKIP_SOVITS=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --skip-comfyui)
            SKIP_COMFYUI=true
            shift
            ;;
        --skip-sovits)
            SKIP_SOVITS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            shift
            ;;
    esac
done

echo "========================================"
echo "  AI Girlfriend — 依赖自动下载脚本"
echo "========================================"
echo ""
echo "安装目录: $INSTALL_DIR"
echo ""

# 确保安装目录存在
mkdir -p "$INSTALL_DIR"

# 检测操作系统
OS=$(uname -s)
IS_MAC=false
IS_LINUX=false
if [[ "$OS" == "Darwin" ]]; then
    IS_MAC=true
    echo "操作系统: macOS"
elif [[ "$OS" == "Linux" ]]; then
    IS_LINUX=true
    echo "操作系统: Linux"
else
    echo "操作系统: $OS (未知)"
fi

# 检测是否有NVIDIA GPU
HAS_NVIDIA=false
if command -v nvidia-smi &> /dev/null; then
    HAS_NVIDIA=true
    echo "检测到 NVIDIA GPU"
fi

# ComfyUI 仓库
COMFYUI_REPO="https://github.com/comfyanonymous/ComfyUI.git"
COMFYUI_DIR="$INSTALL_DIR/ComfyUI"

# GPT-SoVITS 仓库
SOVITS_REPO="https://github.com/RVC-Boss/GPT-SoVITS.git"
SOVITS_DIR="$INSTALL_DIR/GPT-SoVITS"

# ============================================
# 1. ComfyUI
# ============================================
if [[ "$SKIP_COMFYUI" == false ]]; then
    echo ""
    echo "--- ComfyUI ---"
    
    if [[ -d "$COMFYUI_DIR" ]]; then
        echo "ComfyUI 已存在: $COMFYUI_DIR"
    else
        echo "克隆 ComfyUI 源码..."
        cd "$INSTALL_DIR"
        git clone "$COMFYUI_REPO"
        if [[ $? -eq 0 ]]; then
            echo "  ComfyUI 克隆成功!"
        else
            echo "  ComfyUI 克隆失败"
        fi
    fi
    
    # 检测 Python
    if command -v python3 &> /dev/null; then
        COMFYUI_PYTHON=$(which python3)
        echo "  检测到系统 Python: $COMFYUI_PYTHON"
    fi
fi

# ============================================
# 2. GPT-SoVITS
# ============================================
if [[ "$SKIP_SOVITS" == false ]]; then
    echo ""
    echo "--- GPT-SoVITS ---"
    
    if [[ -d "$SOVITS_DIR" ]]; then
        echo "GPT-SoVITS 已存在: $SOVITS_DIR"
    else
        echo "克隆 GPT-SoVITS 源码..."
        cd "$INSTALL_DIR"
        git clone "$SOVITS_REPO"
        if [[ $? -eq 0 ]]; then
            echo "  GPT-SoVITS 克隆成功!"
        else
            echo "  GPT-SoVITS 克隆失败"
        fi
    fi
    
    # 检测 Python
    if command -v python3 &> /dev/null; then
        SOVITS_PYTHON=$(which python3)
        echo "  检测到系统 Python: $SOVITS_PYTHON"
    fi
fi

# ============================================
# 3. 更新 config.yaml
# ============================================
echo ""
echo "--- 更新 config.yaml ---"

CONFIG_PATH="$SCRIPT_DIR/config.yaml"
if [[ -f "$CONFIG_PATH" ]]; then
    if [[ "$SKIP_COMFYUI" == false ]] && [[ -d "$COMFYUI_DIR" ]]; then
        # Set comfyui_root first (takes priority)
        sed -i.bak "s|comfyui_root:.*|comfyui_root: $COMFYUI_DIR|" "$CONFIG_PATH"
        if [[ -n "$COMFYUI_PYTHON" ]]; then
            sed -i.bak "s|comfyui_python:.*|comfyui_python: $COMFYUI_PYTHON|" "$CONFIG_PATH"
        fi
        COMFYUI_CKPT_DIR="$COMFYUI_DIR/models/checkpoints"
        mkdir -p "$COMFYUI_CKPT_DIR"
        sed -i.bak "s|comfyui_checkpoints_dir:.*|comfyui_checkpoints_dir: $COMFYUI_CKPT_DIR|" "$CONFIG_PATH"
    fi
    
    if [[ "$SKIP_SOVITS" == false ]] && [[ -d "$SOVITS_DIR" ]]; then
        if [[ -n "$SOVITS_PYTHON" ]]; then
            sed -i.bak "s|sovits_python:.*|sovits_python: $SOVITS_PYTHON|" "$CONFIG_PATH"
        fi
        sed -i.bak "s|sovits_weights_dir:.*|sovits_weights_dir: $SOVITS_DIR|" "$CONFIG_PATH"
    fi
    
    echo "config.yaml 已更新: $CONFIG_PATH"
else
    echo "config.yaml 不存在，跳过更新"
fi

# ============================================
# 4. 后续步骤提示
# ============================================
echo ""
echo "========================================"
echo "  依赖下载完成!"
echo "========================================"
echo ""

if [[ "$SKIP_COMFYUI" == false ]]; then
    echo "ComfyUI 后续步骤:"
    echo "  1. 安装 Python 依赖: cd $COMFYUI_DIR && python3 -m pip install -r requirements.txt"
    echo "  2. 下载模型到 models/checkpoints/ 目录"
fi

if [[ "$SKIP_SOVITS" == false ]]; then
    echo ""
    echo "GPT-SoVITS 后续步骤:"
    echo "  1. 安装 Python 依赖: cd $SOVITS_DIR && python3 -m pip install -r requirements.txt"
    echo "  2. 下载预训练模型到 GPT_weights_v2Pro/ 和 SoVITS_weights_v2Pro/ 目录"
fi

echo ""
echo "如需进一步配置，运行: bash quick_setup.sh"
