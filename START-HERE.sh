#!/usr/bin/env bash
# ===========================================================================
#  AI Girlfriend — START HERE (Linux / macOS / Git-Bash / WSL)
#
#  Picks the LLM model / engine, the ComfyUI model, the GPT-SoVITS voice and
#  the service ports, writes them into config.yaml, then starts and connects
#  the whole stack (Strata -> daemon/llama.cpp -> ComfyUI -> GPT-SoVITS).
#
#      ./START-HERE.sh                 menu, then start
#      ./START-HERE.sh --status        what is up right now
#      ./START-HERE.sh --stop          stop everything
#      ./START-HERE.sh --list          show available models and voices
#      ./START-HERE.sh --help
#
#  Same implementation as START-HERE.bat — this file only finds Python.
# ===========================================================================
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

PY=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
        PY="$candidate"
        break
    fi
done

if [ -z "$PY" ]; then
    cat >&2 <<'EOF'

  Python 3.10+ was not found on PATH.
  Install it (apt install python3 / brew install python) and run this again.

EOF
    exit 1
fi

exec "$PY" "$SCRIPT_DIR/start_here.py" "$@"
