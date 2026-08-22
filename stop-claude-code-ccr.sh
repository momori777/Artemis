#!/usr/bin/env bash
# stop-claude-code-ccr.sh - Stop Claude Code sidecar services (task board + CCR)
# ================================================================================
# Stops the visual task board (started by claude-code-ccr.sh) and, optionally, CCR.
# Reads ports from config.yaml (no hardcoding).
#
# Note: the Claude Code process itself is foreground/interactive; close it with Ctrl+C
#       or its own /exit command. This script only manages the sidecar services.
#
# Usage:
#   ./stop-claude-code-ccr.sh          # stop task board only
#   ./stop-claude-code-ccr.sh --all    # also stop CCR gateway

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH="$PROJECT_ROOT/config.yaml"

get_yaml_value() {
    local raw="$1" key="$2"
    printf '%s\n' "$raw" | sed -nE "s/^[[:space:]]*${key}[[:space:]]*:[[:space:]]*\"?([^\"#[:space:]]+)\"?.*$/\1/p" | head -n1
}

ALL=false
for arg in "$@"; do
    [[ "$arg" == "--all" ]] && ALL=true
done

BOARD_PORT=19280
if [[ -f "$CONFIG_PATH" ]]; then
    CFG_RAW="$(cat "$CONFIG_PATH" | tr -d '\r')"
    [[ -n "$(get_yaml_value "$CFG_RAW" 'task_board_port')" ]] && BOARD_PORT="$(get_yaml_value "$CFG_RAW" 'task_board_port')"
fi

echo -e "\033[36m=== Stop Claude Code sidecar services ===\033[0m"

# Stop task board (match by command line to avoid killing unrelated python)
BOARD_PIDS="$(pgrep -f 'task_board_api\.py' || true)"
if [[ -n "$BOARD_PIDS" ]]; then
    for pid in $BOARD_PIDS; do
        kill "$pid" &>/dev/null || true
        echo -e "  stopped task board (PID $pid)"
    done
else
    echo "  task board not running"
fi

# Optionally stop CCR
if [[ "$ALL" == true ]]; then
    CCR_STOP="$PROJECT_ROOT/skills/ccr/stop-ccr.sh"
    if [[ -f "$CCR_STOP" ]]; then
        echo ""
        bash "$CCR_STOP"
    else
        echo -e "  [WARN] stop-ccr.sh not found: $CCR_STOP"
    fi
fi

echo ""
echo -e "\033[32mDone. Claude Code itself: use /exit or Ctrl+C in its terminal.\033[0m"
