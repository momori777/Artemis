"""
VRAM Level Configuration — Skill lifecycle manager for multi-GPU workloads.

Resolves the current VRAM_LEVEL and provides helpers for skill scripts
to decide whether to stop/restart llama-server.

Usage:
    from skills.shared.vram import get_vram_level, should_stop_llama

    level = get_vram_level()
    if should_stop_llama("tts"):
        stop_llama()
        ...
        start_llama()

Levels (see VRAM_LEVELS.md):
    0 = ALL_STOP   — stop llama for every skill
    1 = TTS_STOP   — stop llama only for TTS/ComfyUI (keep for ASR/Live2D)
    2 = ALL_ONLINE — never stop llama (--no-manage-llama for all skills)
    3 = LEGACY     — stop for TTS/ComfyUI/ASR, keep for Live2D
"""

import os

# Skill name → stops llama at this level and below
# e.g. "tts" stops at level 0,1,3 but not at level 2
LLAMA_STOP_THRESHOLD = {
    "tts": 1,       # stops at level 0,1,3 (not at level 2)
    "comfyui": 1,   # stops at level 0,1,3 (not at level 2)
    "asr": 0,       # only stops at level 0 (safe mode)
    "live2d": -1,   # never stops
    "sakura": 0,    # stops at level 0 only
}


def get_vram_level() -> int:
    """
    Resolve current VRAM level from:
    1. Env var VRAM_LEVEL
    2. config.yaml vram_level key (if available)
    3. Default: 2 (ALL_ONLINE — RTX 5070 12GB safe)
    """
    env_val = os.environ.get("VRAM_LEVEL")
    if env_val is not None:
        try:
            return int(env_val)
        except ValueError:
            pass

    # Try config.yaml
    try:
        import yaml
        config_paths = [
            os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml"),
            os.path.join(os.path.dirname(__file__), "..", "..", "config-patch.yaml"),
        ]
        for cp in config_paths:
            if os.path.exists(cp):
                with open(cp, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                if "vram_level" in cfg:
                    return int(cfg["vram_level"])
    except Exception:
        pass

    return 2  # default: ALL_ONLINE


def should_stop_llama(skill_name: str) -> bool:
    """
    Returns True if llama-server should be stopped before running this skill.
    Skill names: 'tts', 'comfyui', 'asr', 'live2d', 'sakura'
    """
    threshold = LLAMA_STOP_THRESHOLD.get(skill_name.lower(), 0)
    return get_vram_level() <= threshold


def skill_flag() -> str:
    """
    Returns the appropriate CLI flag for --no-manage-llama based on level.
    For use in AGENTS.md spawn templates and skill scripts.
    """
    return "--no-manage-llama"


if __name__ == "__main__":
    level = get_vram_level()
    names = {0: "ALL_STOP", 1: "TTS_STOP_ONLY", 2: "ALL_ONLINE", 3: "LEGACY"}
    print(f"VRAM_LEVEL={level} ({names.get(level, 'UNKNOWN')})")
    for skill in ["tts", "comfyui", "asr", "live2d", "sakura"]:
        action = "STOP" if should_stop_llama(skill) else "KEEP"
        print(f"  {skill}: {action} llama")
