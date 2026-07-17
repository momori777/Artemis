#!/usr/bin/env bash
# ============================================================
#  AI Girlfriend — 一键停止 (Linux/macOS)
#  Usage: bash stop.sh
#
#  停止顺序:
#   1. OpenClaw Gateway
#   2. Live2D Bridge
#   3. Embedding Server
#   4. llama-server
#   5. Orphan cleanup (.task_flags, .lock)
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; MAGENTA='\033[0;35m'; GRAY='\033[0;90m'; NC='\033[0m'

echo -e "${MAGENTA}============================================${NC}"
echo -e "${MAGENTA}  AI Girlfriend — Shutdown${NC}"
echo -e "${MAGENTA}============================================${NC}"
echo ""

# ── Helpers ──────────────────────────────────────────────
kill_port() {
    local port="$1" label="$2"
    local pid=""

    # Find PID by port
    if command -v lsof &>/dev/null; then
        pid=$(lsof -ti ":$port" 2>/dev/null || true)
    elif command -v ss &>/dev/null; then
        pid=$(ss -tlnp 2>/dev/null | grep ":$port " | grep -oP 'pid=\K[0-9]+' | head -1 || true)
    elif command -v netstat &>/dev/null; then
        pid=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $NF}' | grep -oP '[0-9]+' | head -1 || true)
    fi

    if [[ -z "$pid" ]]; then
        echo -e "  ${GRAY}$label: not running${NC}"
        return 0
    fi

    echo -n "  $label: stopping (port $port, pid $pid)..."
    kill "$pid" 2>/dev/null || true

    # Wait for graceful shutdown
    for ((i=0; i<15; i++)); do
        sleep 0.5
        if ! kill -0 "$pid" 2>/dev/null; then
            echo -e " ${GREEN}stopped${NC}"
            return 0
        fi
    done

    # Force kill
    kill -9 "$pid" 2>/dev/null || true
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
        echo -e " ${RED}STILL RUNNING${NC}"
        return 1
    else
        echo -e " ${YELLOW}force killed${NC}"
        return 0
    fi
}

# ═══════════════════════════════════════════════════════════
# 1. OpenClaw Gateway
# ═══════════════════════════════════════════════════════════
echo -e "${YELLOW}[1/5] OpenClaw Gateway${NC}"

if command -v openclaw &>/dev/null; then
    if openclaw gateway status 2>/dev/null | grep -q "running"; then
        echo -n "  Stopping gateway..."
        openclaw gateway stop 2>/dev/null && echo -e " ${GREEN}stopped${NC}" || echo -e " ${YELLOW}stop command failed${NC}"
    else
        echo -e "  ${GRAY}Gateway not running${NC}"
    fi
else
    echo -e "  ${GRAY}openclaw CLI not found — skipping${NC}"
fi

# ═══════════════════════════════════════════════════════════
# 2. Live2D Bridge
# ═══════════════════════════════════════════════════════════
echo -e "${YELLOW}[2/5] Live2D Bridge${NC}"
kill_port 19200 "Live2D Bridge"

# ═══════════════════════════════════════════════════════════
# 3. Embedding Server
# ═══════════════════════════════════════════════════════════
echo -e "${YELLOW}[3/5] Embedding Server${NC}"
kill_port 9999 "Embedding Server"

# ═══════════════════════════════════════════════════════════
# 4. llama-server
# ═══════════════════════════════════════════════════════════
echo -e "${YELLOW}[4/5] llama-server${NC}"

LLAMA_PORT=8080
CONFIG="$SCRIPT_DIR/config.yaml"
if [[ -f "$CONFIG" ]]; then
    LLAMA_PORT=$(grep -E '^\s*llama_port\s*:' "$CONFIG" | head -1 | sed -E 's/^[^:]*:\s*"?([^"]*)"?\s*$/\1/' | xargs || echo 8080)
fi

# Try graceful shutdown first
if curl -s --connect-timeout 3 "http://127.0.0.1:${LLAMA_PORT}/shutdown" >/dev/null 2>&1; then
    echo -n "  llama-server: /shutdown sent..."
    for ((i=0; i<20; i++)); do
        sleep 0.5
        if ! kill_port "${LLAMA_PORT}" "llama-server" 2>/dev/null; then
            :
        fi
        if ! curl -s --connect-timeout 1 "http://127.0.0.1:${LLAMA_PORT}/health" >/dev/null 2>&1; then
            echo -e " ${GREEN}stopped${NC}"
            break
        fi
    done
else
    # Direct kill by process name
    if pgrep -f "llama-server" >/dev/null 2>&1; then
        echo -n "  llama-server: killing..."
        pkill -f "llama-server" 2>/dev/null || true
        sleep 2
        if pgrep -f "llama-server" >/dev/null 2>&1; then
            pkill -9 -f "llama-server" 2>/dev/null || true
            sleep 1
        fi
        if pgrep -f "llama-server" >/dev/null 2>&1; then
            echo -e " ${RED}STILL RUNNING${NC}"
        else
            echo -e " ${GREEN}stopped${NC}"
        fi
    else
        echo -e "  ${GRAY}llama-server: not running${NC}"
    fi
fi

# ═══════════════════════════════════════════════════════════
# 5. Cleanup
# ═══════════════════════════════════════════════════════════
echo -e "${YELLOW}[5/5] Cleanup${NC}"

# Remove task flags
TASK_FLAGS="$SCRIPT_DIR/.task_flags"
if [[ -d "$TASK_FLAGS" ]]; then
    rm -rf "$TASK_FLAGS"
    echo -e "  ${GREEN}.task_flags cleaned${NC}"
fi

# Remove comfyui lock
COMFYUI_LOCK="$SCRIPT_DIR/comfyui_temp_output/.comfyui_running.lock"
WORKSPACE="$(grep -E '^\s*workspace\s*:' "$CONFIG" 2>/dev/null | head -1 | sed -E 's/^[^:]*:\s*"?([^"]*)"?\s*$/\1/' | xargs || echo "")"
if [[ -n "$WORKSPACE" ]]; then
    COMFYUI_LOCK="$WORKSPACE/comfyui/.comfyui_running.lock"
fi
if [[ -f "$COMFYUI_LOCK" ]]; then
    rm -f "$COMFYUI_LOCK"
    echo -e "  ${GREEN}ComfyUI lock cleaned${NC}"
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  All stopped. Goodbye!${NC}"
echo -e "${GREEN}============================================${NC}"
