#!/usr/bin/env bash
# stop-ccr.sh - Stop CCR (Claude Code Router)
# =============================================
# Reads ports from config.yaml (consistent with start-ccr.sh).
# Prefers `ccr stop`; falls back to cleaning up stray serve/start processes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_PATH="$PROJECT_ROOT/config.yaml"

get_yaml_value() {
    local raw="$1" key="$2"
    printf '%s\n' "$raw" | sed -nE "s/^[[:space:]]*${key}[[:space:]]*:[[:space:]]*\"?([^\"#[:space:]]+)\"?.*$/\1/p" | head -n1
}

WEB_PORT=3458; GW_PORT=3456
if [[ -f "$CONFIG_PATH" ]]; then
    CFG_RAW="$(cat "$CONFIG_PATH" | tr -d '\r')"
    [[ -n "$(get_yaml_value "$CFG_RAW" 'ccr_web_port')" ]] && WEB_PORT="$(get_yaml_value "$CFG_RAW" 'ccr_web_port')"
    [[ -n "$(get_yaml_value "$CFG_RAW" 'ccr_port')" ]]     && GW_PORT="$(get_yaml_value "$CFG_RAW" 'ccr_port')"
fi

echo -e "\033[36m=== CCR stop ===\033[0m"

# Preferred: official stop
if command -v ccr &>/dev/null; then
    ccr stop &>/dev/null || true
    sleep 2
fi

# Fallback: clean up stray ccr serve/start processes
LINGERING="$(pgrep -f 'claude-code-router.*(serve|start)' || true)"
if [[ -n "$LINGERING" ]]; then
    for pid in $LINGERING; do
        kill "$pid" &>/dev/null || true
        echo -e "  stopped stray CCR process (PID $pid)"
    done
else
    echo "  no stray CCR process"
fi

sleep 1

# Confirm ports are released (Linux: ss / lsof, macOS: lsof)
released=true
for port in "$GW_PORT" "$WEB_PORT"; do
    if command -v ss &>/dev/null; then
        if ss -ltn "sport = :$port" 2>/dev/null | grep -q ":$port"; then
            released=false
        fi
    elif command -v lsof &>/dev/null; then
        if lsof -iTCP:"$port" -sTCP:LISTEN &>/dev/null; then
            released=false
        fi
    fi
done

if [[ "$released" == true ]]; then
    echo -e "\033[32mCCR stopped (ports $GW_PORT / $WEB_PORT released)\033[0m"
else
    echo -e "\033[33m[WARN] ports still in use ($GW_PORT / $WEB_PORT)\033[0m"
fi
