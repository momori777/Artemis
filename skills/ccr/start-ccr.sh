#!/usr/bin/env bash
# start-ccr.sh - Start CCR (Claude Code Router)
# ==============================================
# Reads ports from project-root config.yaml (no hardcoding).
# `ccr start` reuses any running service (writes service.json), safe to re-run.
#
# Usage:
#   ./skills/ccr/start-ccr.sh
#   ./skills/ccr/start-ccr.sh --no-gateway   # management UI only

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_PATH="$PROJECT_ROOT/config.yaml"

# Read a scalar value from config.yaml (key: value or key: "value")
get_yaml_value() {
    local raw="$1" key="$2"
    # match "key: value" (optionally quoted), value may be a port number or string
    local val
    val=$(printf '%s\n' "$raw" | sed -nE "s/^[[:space:]]*${key}[[:space:]]*:[[:space:]]*\"?([^\"#[:space:]]+)\"?.*$/\1/p" | head -n1)
    printf '%s' "$val"
}

if [[ ! -f "$CONFIG_PATH" ]]; then
    echo -e "\033[31m[ERROR] config.yaml not found: $CONFIG_PATH\033[0m" >&2
    exit 1
fi
CFG_RAW="$(cat "$CONFIG_PATH" | tr -d '\r')"

# Ports from config.yaml, falling back to CCR defaults
WEB_PORT="$(get_yaml_value "$CFG_RAW" 'ccr_web_port')";      [[ -z "$WEB_PORT" ]] && WEB_PORT=3458
GW_PORT="$(get_yaml_value "$CFG_RAW" 'ccr_port')";           [[ -z "$GW_PORT" ]]  && GW_PORT=3456
UP_PORT="$(get_yaml_value "$CFG_RAW" 'ccr_upstream_port')";  [[ -z "$UP_PORT" ]]  && UP_PORT=8080

# Check ccr command
if ! command -v ccr &>/dev/null; then
    echo -e "\033[31m[ERROR] ccr command not found.\033[0m" >&2
    echo -e "  Install: npm install -g @musistudio/claude-code-router" >&2
    exit 1
fi

echo -e "\033[36m=== CCR start ===\033[0m"
echo -e "  project root: $PROJECT_ROOT"
echo -e "  gateway port: $GW_PORT (upstream llama: $UP_PORT)"
echo -e "  web port:     $WEB_PORT"
echo ""

ARGS=("start" "--host" "127.0.0.1" "--port" "$WEB_PORT" "--no-open")
if [[ "${1:-}" == "--no-gateway" ]]; then
    ARGS+=("--no-gateway")
fi

ccr "${ARGS[@]}"

echo ""
echo -e "\033[32mCCR started.\033[0m"
echo -e "  management UI: http://127.0.0.1:$WEB_PORT"
echo -e "  model gateway: http://127.0.0.1:$GW_PORT  (upstream http://127.0.0.1:$UP_PORT/v1)"
