#!/usr/bin/env bash
# setup-dsh.sh — AI Girlfriend · DeepSeek Harness (dsh) one-shot setup (Linux/macOS)
#
# dsh = DeepSeek's open-source agent harness (community nickname "大肥鱼"),
# the third agent runtime alongside OpenClaw / Claude Code.
#
# Usage:  bash setup-dsh.sh [--skip-install]
# Launch: dsh web        (no-install: npx @deepseek-ai/dsh web)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKIP_INSTALL=0
[[ "${1:-}" == "--skip-install" ]] && SKIP_INSTALL=1

echo "AI Girlfriend · DeepSeek Harness (dsh) setup"

# 1. Node.js >= 24
if ! command -v node >/dev/null 2>&1; then
    echo "[!] Node.js 24+ required (https://nodejs.org)"; exit 1
fi
NODE_MAJOR="$(node -v | sed 's/v\([0-9]*\).*/\1/')"
if (( NODE_MAJOR < 24 )); then
    echo "[!] Node.js 24+ required, found $(node -v)"; exit 1
fi
echo "[ok] Node.js $(node -v)"

# 2. Global install
if (( ! SKIP_INSTALL )); then
    npm install -g --allow-scripts=@deepseek-ai/dsh-subprocess-local,koffi,node-pty,@google/genai,protobufjs @deepseek-ai/dsh
fi

# 3. Verify
command -v dsh >/dev/null 2>&1 || { echo "[!] dsh not on PATH"; exit 1; }
echo "[ok] dsh $(dsh --version 2>/dev/null)"

# 4. Plugin inventory
echo ""
echo "Local dsh repos (benchmark_projects/, git-ignored):"
for p in deepseek-harness dsh-liketavern dsh-nexttavern dsh-agent-rp dsh-familiar-memory ProjectKaren dafeiyu-character-cards; do
    if [[ -d "$SCRIPT_DIR/benchmark_projects/$p" ]]; then echo "  [x] $p"; else echo "  [ ] $p"; fi
done
echo ""
echo "Launch: dsh web"
echo "Ecosystem survey: benchmark_projects/2026-11-07-dsh-roleplay-report.md"
