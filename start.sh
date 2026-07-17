#!/usr/bin/env bash
# ============================================================
#  AI Girlfriend — 一键启动 (Linux/macOS)
#  Usage: bash start.sh
#
#  启动顺序:
#   1. llama-server
#   2. Embedding Server (optional)
#   3. Live2D Bridge (optional)
#   4. OpenClaw Gateway
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; MAGENTA='\033[0;35m'; GRAY='\033[0;90m'; NC='\033[0m'

echo -e "${MAGENTA}============================================${NC}"
echo -e "${MAGENTA}  AI Girlfriend — Startup${NC}"
echo -e "${MAGENTA}============================================${NC}"
echo ""

# ── Config ──────────────────────────────────────────────
CONFIG="$SCRIPT_DIR/config.yaml"
if [[ ! -f "$CONFIG" ]]; then
    echo -e "  ${RED}ERROR: config.yaml not found${NC}"
    echo -e "  ${YELLOW}Run: bash quick_setup.sh  (or manually copy config.example.yaml → config.yaml)${NC}"
    exit 1
fi

# Simple YAML value extraction (no external parser needed)
get_yaml() {
    local key="$1"
    grep -E "^\s*${key}\s*:" "$CONFIG" | head -1 | sed -E 's/^[^:]*:\s*"?([^"]*)"?\s*$/\1/' | xargs
}

LLAMA_EXE="$(get_yaml 'llama_exe')"
LLAMA_MODEL="$(get_yaml 'llama_model')"
LLAMA_PORT="$(get_yaml 'llama_port')"
LLAMA_LOG_DIR="$(get_yaml 'llama_log_dir')"
WORKSPACE="$(get_yaml 'workspace')"
EMBED_SCRIPT="$(get_yaml 'embedding_server')"

[[ -z "$LLAMA_PORT" ]] && LLAMA_PORT=8080
[[ -z "$LLAMA_LOG_DIR" ]] && LLAMA_LOG_DIR="$SCRIPT_DIR/llama-server/restart-logs"

# ── Helpers ──────────────────────────────────────────────
check_port() {
    local port="$1"
    if command -v ss &>/dev/null; then
        ss -tlnp 2>/dev/null | grep -q ":$port " && return 0
    elif command -v netstat &>/dev/null; then
        netstat -tlnp 2>/dev/null | grep -q ":$port " && return 0
    elif command -v lsof &>/dev/null; then
        lsof -i ":$port" -sTCP:LISTEN &>/dev/null && return 0
    fi
    return 1
}

wait_health() {
    local port="$1" label="$2" max_wait="${3:-60}"
    echo -n "  Waiting for $label (port $port)"
    for ((i=0; i<max_wait; i++)); do
        if check_port "$port"; then
            echo -e " ${GREEN}ready${NC} (${i}s)"
            return 0
        fi
        sleep 1
        [[ $((i % 5)) -eq 0 ]] && echo -n "."
    done
    echo -e " ${YELLOW}timeout${NC}"
    return 1
}

# ═══════════════════════════════════════════════════════════
# 1. llama-server
# ═══════════════════════════════════════════════════════════
echo -e "${YELLOW}[1/4] llama-server${NC}"

if check_port "$LLAMA_PORT"; then
    echo -e "  ${GREEN}llama-server already online (port $LLAMA_PORT)${NC}"
else
    if [[ ! -f "$LLAMA_EXE" ]]; then
        echo -e "  ${RED}ERROR: llama-server not found: $LLAMA_EXE${NC}"
        echo -e "  ${YELLOW}Check config.yaml → llama_exe${NC}"
        exit 1
    fi
    if [[ ! -f "$LLAMA_MODEL" ]]; then
        echo -e "  ${RED}ERROR: Model not found: $LLAMA_MODEL${NC}"
        echo -e "  ${YELLOW}Check config.yaml → llama_model${NC}"
        exit 1
    fi

    echo "  Starting llama-server..."

    # Kill any stale instance
    pkill -f "llama-server" 2>/dev/null || true
    sleep 1

    mkdir -p "$LLAMA_LOG_DIR"

    # Detect CUDA
    NGL=""
    if command -v nvidia-smi &>/dev/null; then
        NGL="--n-gpu-layers 999"
    fi

    nohup "$LLAMA_EXE" \
        -m "$LLAMA_MODEL" \
        -c 120000 \
        --flash-attn on \
        -ctk q8_0 -ctv q8_0 \
        --batch-size 2048 \
        --ubatch-size 1024 \
        --threads "$(nproc)" \
        --jinja \
        --cache-ram 3000 \
        --parallel 1 \
        --port "$LLAMA_PORT" \
        --timeout 600 \
        ${NGL:-} \
        > "$LLAMA_LOG_DIR/llama-out.log" 2> "$LLAMA_LOG_DIR/llama-err.log" &

    wait_health "$LLAMA_PORT" "llama-server" 180
fi

# ═══════════════════════════════════════════════════════════
# 2. Embedding Server
# ═══════════════════════════════════════════════════════════
echo -e "${YELLOW}[2/4] Embedding Server${NC}"

EMBED_PORT=9999

if check_port "$EMBED_PORT"; then
    echo -e "  ${GREEN}Embedding server already online (port $EMBED_PORT)${NC}"
else
    # Try the configured script, fall back to relative path
    if [[ -z "$EMBED_SCRIPT" || ! -f "$EMBED_SCRIPT" ]]; then
        EMBED_SCRIPT="$SCRIPT_DIR/skills/shared/embedding_server.py"
    fi

    if [[ -f "$EMBED_SCRIPT" ]]; then
        PYTHON=""
        for py in python3 python; do
            if command -v "$py" &>/dev/null; then PYTHON="$py"; break; fi
        done
        if [[ -n "$PYTHON" ]]; then
            echo "  Starting embedding server (port $EMBED_PORT)..."
            nohup "$PYTHON" "$EMBED_SCRIPT" > /dev/null 2>&1 &
            wait_health "$EMBED_PORT" "embedding server" 30 || \
                echo -e "  ${GRAY}Embedding server skipped (memory_search will use BM25 fallback)${NC}"
        else
            echo -e "  ${GRAY}Python not found — embedding server skipped${NC}"
        fi
    else
        echo -e "  ${GRAY}embedding_server.py not found — skipping${NC}"
    fi
fi

# ═══════════════════════════════════════════════════════════
# 3. Live2D Bridge
# ═══════════════════════════════════════════════════════════
echo -e "${YELLOW}[3/4] Live2D Bridge${NC}"

L2D_PORT=19200

if check_port "$L2D_PORT"; then
    echo -e "  ${GREEN}Live2D Bridge already online (port $L2D_PORT)${NC}"
else
    L2D_DIR="$SCRIPT_DIR/live2d"
    if [[ -f "$L2D_DIR/live2d-bridge.mjs" ]]; then
        if command -v node &>/dev/null; then
            echo "  Starting Live2D Bridge..."
            nohup node live2d-bridge.mjs > /dev/null 2>&1 &
            wait_health "$L2D_PORT" "Live2D Bridge" 10 || \
                echo -e "  ${YELLOW}Live2D Bridge not responding — continuing${NC}"
        else
            echo -e "  ${GRAY}Node.js not found — Live2D skipped${NC}"
        fi
    else
        echo -e "  ${GRAY}live2d-bridge.mjs not found — skipping${NC}"
    fi
fi

# ═══════════════════════════════════════════════════════════
# 4. OpenClaw Gateway
# ═══════════════════════════════════════════════════════════
echo -e "${YELLOW}[4/4] OpenClaw Gateway${NC}"

if command -v openclaw &>/dev/null; then
    if openclaw gateway status 2>/dev/null | grep -q "running"; then
        echo -e "  ${GREEN}Gateway already running${NC}"
    else
        echo "  Starting gateway..."
        openclaw gateway start 2>/dev/null && \
            echo -e "  ${GREEN}Gateway started${NC}" || \
            echo -e "  ${YELLOW}Gateway may not have started — check: openclaw gateway status${NC}"
    fi
else
    echo -e "  ${YELLOW}openclaw CLI not found — skip${NC}"
    echo -e "  ${GRAY}Install: npm i -g openclaw${NC}"
fi

# ═══════════════════════════════════════════════════════════
# Done
# ═══════════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  All services ready!${NC}"
echo -e "  llama-server  : http://127.0.0.1:${LLAMA_PORT}"
echo -e "  Embedding     : http://127.0.0.1:${EMBED_PORT}"
echo -e "  Live2D Bridge : http://localhost:${L2D_PORT}"
echo -e "  Gateway       : http://127.0.0.1:18789"
echo -e "${GREEN}============================================${NC}"
