# VRAM Levels — Skill vs. Llama Lifecycle Strategy
# ==================================================
# Artemis runs multiple AI workloads on a single GPU.
# Choose a level based on your VRAM budget. Default: Level 2.
#
# How it works:
#   - "Llama lifecycle" = stop llama-server before inference, restart after
#   - This frees ~4-8GB VRAM for heavy inference, at cost of ~5s round-trip
#   - Lower levels = more aggressive stops, more stable, but slower
#   - Higher levels = everything stays online, but risks OOM on small GPUs
#
# Your GPU: RTX 5070 12GB → Level 2 recommended (32GB system RAM compensates)

Level 0: ALL_STOP (Safe — <8GB VRAM cards)
  ┌─────────────────────────────────────────────────┐
  │ llama-server: STOP before any skill             │
  │ TTS (GPT-SoVITS): STOP llama, hog GPU           │
  │ ComfyUI (image gen): STOP llama, hog GPU        │
  │ ASR (Whisper): STOP llama (safe mode)           │
  │ Live2D: no impact (CPU/light GPU)               │
  │                                                 │
  │ Concurrency: None — one task at a time          │
  │ VRAM peak: ~8GB (single heavy workload)         │
  │ Latency hit: +5s per task (llama restart)       │
  └─────────────────────────────────────────────────┘

Level 1: TTS_STOP_ONLY (<12GB VRAM cards)
  ┌─────────────────────────────────────────────────┐
  │ llama-server: KEPT for ASR/Live2D               │
  │ TTS (GPT-SoVITS): STOP llama, restore after     │
  │ ComfyUI (image gen): STOP llama, restore after  │
  │ ASR (Whisper): KEEP llama (small model ~1.5GB)  │
  │ Live2D: KEEP llama (negligible GPU)             │
  │                                                 │
  │ Concurrency: ASR + llama, Live2D + llama OK     │
  │ VRAM peak: ~10GB (TTS + llama reserved)         │
  │ Latency hit: +3s only for TTS/ComfyUI           │
  └─────────────────────────────────────────────────┘

Level 2: ALL_ONLINE (Recommended — 12GB+ VRAM)
  ┌─────────────────────────────────────────────────┐
  │ llama-server: ALWAYS KEPT online                │
  │ TTS (GPT-SoVITS): --no-manage-llama, share VRAM │
  │ ComfyUI (image gen): --no-manage-llama, share   │
  │ ASR (Whisper): KEEP llama (independent VRAM)    │
  │ Live2D: KEEP llama                              │
  │                                                 │
  │ Concurrency: All skills + llama coexist         │
  │ VRAM peak: ~11.5GB (llama + TTS active)         │
  │ Latency hit: 0s (no stop/restart cycles)        │
  │ Risk: OOM if llama + TTS exceed 12GB            │
  │                                                 │
  │ NOTE: ASR model (faster-whisper-small ~1.5GB)   │
  │ and GPT-SoVITS (~3-4GB) can coexist with llama  │
  │ on 12GB cards when quantized Q4/Q5.             │
  └─────────────────────────────────────────────────┘

Level 3: LEGACY (Original behavior — 8GB cards)
  ┌─────────────────────────────────────────────────┐
  │ TTS: STOP llama, restore after                  │
  │ ComfyUI: STOP llama, restore after              │
  │ ASR: STOP llama (old safe path)                 │
  │ Live2D: KEEP llama                              │
  │                                                 │
  │ Same as Level 0 but Live2D keeps llama.         │
  │ This was the original Artemis behavior.         │
  └─────────────────────────────────────────────────┘

# ==================================================
# Implementation
# ==================================================
# Skills declare their llama lifecycle behavior via:
#   --manage-llama       (default: stop/restart)
#   --no-manage-llama    (keep llama online)
#
# AGENTS.md reads VRAM_LEVEL from config or env.
# Set via environment variable:
#   $env:VRAM_LEVEL = "2"   # PowerShell
#   export VRAM_LEVEL=2     # bash
#
# Or add to config.yaml:
#   vram_level: 2
#
# Current active level is resolved by skills/shared/vram.py

# Current settings on this machine (RTX 5070 12GB):
VRAM_LEVEL=2
