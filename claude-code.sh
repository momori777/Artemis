#!/usr/bin/env bash
# Artemis Claude Code Launcher (Linux/macOS)
set -e

echo -e "\033[35m🌸 Artemis × Claude Code\033[0m"
echo -e "\033[90m=========================\033[0m"
echo ""

# Check Claude Code
if ! command -v claude &>/dev/null; then
    echo -e "\033[31m❌ Claude Code not found!\033[0m"
    echo "   Install: npm install -g @anthropic-ai/claude-code"
    exit 1
fi

echo -e "\033[32m✅ Claude Code installed\033[0m"

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo ""
echo -e "\033[36m📂 Project: $PROJECT_DIR\033[0m"
echo -e "\033[90m🔧 MCP tools: tts_generate, comfyui_generate, live2d_emotion, switch_character, memory_search\033[0m"
echo ""

cd "$PROJECT_DIR"

if [ -n "$1" ]; then
    echo -e "\033[35m🚀 Launching Claude Code with prompt: $1\033[0m"
    exec claude --dangerously-load-development-channels server:artemis -p "$1"
else
    echo -e "\033[35m🚀 Launching Claude Code...\033[0m"
    exec claude --dangerously-load-development-channels server:artemis
fi
