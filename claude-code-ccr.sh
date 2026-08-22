#!/usr/bin/env bash
# claude-code-ccr.sh - Launch Claude Code through CCR (connect to local llama)
# ==============================================================================
# Ports are read from project-root config.yaml (no hardcoding).
# Depends on CCR gateway + Claude Code + Artemis MCP task board; does NOT start OpenClaw ports.
#
# MCP: Claude Code auto-loads the project `.mcp.json` (artemis stdio server). A visual
#      task board (HTTP) is optionally started in the background.
#
# Prereqs:
#   1. llama-server running (config.yaml llama_port / ccr_upstream_port)
#   2. CCR running (./skills/ccr/start-ccr.sh)
#   3. Claude Code installed; first launch approves the artemis MCP server once.
#
# Usage:
#   ./claude-code-ccr.sh                          # interactive + start task board
#   ./claude-code-ccr.sh "draw me Natsume"        # with initial prompt
#   ./claude-code-ccr.sh --no-task-board          # skip visual task board
#   ./claude-code-ccr.sh --no-ccr-check           # skip CCR online check

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH="$PROJECT_ROOT/config.yaml"

get_yaml_value() {
    local raw="$1" key="$2"
    printf '%s\n' "$raw" | sed -nE "s/^[[:space:]]*${key}[[:space:]]*:[[:space:]]*\"?([^\"#[:space:]]+)\"?.*$/\1/p" | head -n1
}

NO_TASK_BOARD=false
NO_CCR_CHECK=false
PROMPT=""
for arg in "$@"; do
    case "$arg" in
        --no-task-board) NO_TASK_BOARD=true ;;
        --no-ccr-check)  NO_CCR_CHECK=true ;;
        *) PROMPT="$arg" ;;
    esac
done

# Ports from config.yaml
GW_PORT=3456; UP_PORT=8080; BOARD_PORT=19280
if [[ -f "$CONFIG_PATH" ]]; then
    CFG_RAW="$(cat "$CONFIG_PATH" | tr -d '\r')"
    [[ -n "$(get_yaml_value "$CFG_RAW" 'ccr_port')" ]]          && GW_PORT="$(get_yaml_value "$CFG_RAW" 'ccr_port')"
    [[ -n "$(get_yaml_value "$CFG_RAW" 'ccr_upstream_port')" ]] && UP_PORT="$(get_yaml_value "$CFG_RAW" 'ccr_upstream_port')"
    [[ -n "$(get_yaml_value "$CFG_RAW" 'task_board_port')" ]]   && BOARD_PORT="$(get_yaml_value "$CFG_RAW" 'task_board_port')"
fi

# Check Claude Code
if ! command -v claude &>/dev/null; then
    echo -e "\033[31m[ERROR] claude command not found.\033[0m" >&2
    echo "  Install: npm install -g @anthropic-ai/claude-code" >&2
    exit 1
fi

echo -e "\033[35m=== Claude Code (via CCR) ===\033[0m"
echo -e "  project root: $PROJECT_ROOT"
echo -e "  CCR gateway:  http://127.0.0.1:$GW_PORT  (upstream llama http://127.0.0.1:$UP_PORT/v1)"
echo -e "  MCP server:   artemis (.mcp.json, auto-loaded)"
echo ""

port_open() {
    local port="$1"
    if command -v ss &>/dev/null; then
        ss -ltn "sport = :$port" 2>/dev/null | grep -q ":$port"
    elif command -v lsof &>/dev/null; then
        lsof -iTCP:"$port" -sTCP:LISTEN &>/dev/null
    else
        (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null && exec 3<&- || false
    fi
}

# Start visual task board (optional)
if [[ "$NO_TASK_BOARD" == false ]]; then
    BOARD_SCRIPT="$PROJECT_ROOT/.claude/task_board_api.py"
    if port_open "$BOARD_PORT"; then
        echo -e "  [OK] Task board already online (:$BOARD_PORT)"
    elif [[ -f "$BOARD_SCRIPT" ]]; then
        ARTEMIS_TASK_PORT="$BOARD_PORT" nohup python "$BOARD_SCRIPT" >/dev/null 2>&1 &
        echo -e "  [OK] Task board started: http://127.0.0.1:$BOARD_PORT"
    else
        echo -e "  [WARN] Task board script not found: $BOARD_SCRIPT"
    fi
fi

# Check CCR gateway online (skippable)
if [[ "$NO_CCR_CHECK" == false ]]; then
    if port_open "$GW_PORT"; then
        echo -e "  [OK] CCR gateway online (:$GW_PORT)"
    else
        echo -e "  [WARN] CCR gateway not responding (:$GW_PORT)"
        echo -e "         run ./skills/ccr/start-ccr.sh first"
    fi
    echo ""
fi

# Launch Claude Code (via CCR; Artemis MCP auto-loads from .mcp.json)
cd "$PROJECT_ROOT"
if [[ -n "$PROMPT" ]]; then
    exec claude -p "$PROMPT"
else
    exec claude
fi
