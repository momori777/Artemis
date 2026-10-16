# TOOLS.md — Quick Ref

## Serial rule

TTS/ComfyUI stop llama-server; ASR never does (Whisper ~1.5GB VRAM, coexists). TTS and ComfyUI can't spawn together. All via sessions_spawn(mode="run"); wait for DONE: before the next spawn that stops llama.

## ComfyUI

Read `skills/comfyui/prompt_template.md` → write prompt → spawn PS script (yieldMs 300000) → `MEDIA:<path>`.

## TTS

Read `memory/tts.md` → spawn `skills/tts/run_tts.ps1` (yieldMs 180000). Lang: ja(default)/zh/en; mood: casual/tsundere/romantic/long/random.

## ASR

Voice message → spawn `skills/asr/run_asr.ps1` (yieldMs 180000) → use `DONE:` text as input.

## Live2D

Direct HTTP, no spawn. Full table: `skills/live2d/SKILL.md`.
Idle | Tap head=shy | Tap frame=tsundere | Tap hand=tender | Start=entrance | Leave=exit

## Strata (Qwen3.8-Flash-Next)

Only Qwen3.8-Flash-Next runs on the Strata engine at **:8080** (NOT llama.cpp; llama.cpp moved to **:9931**). Health: `http://127.0.0.1:8080/health`. Start: `run-iq3_s.bat` in the Strata install dir (original path, never clone the whole repo). Full table: `skills/strata/SKILL.md`.

## Characters

Memory: `memory/role_play/<name>/`. Active char = name in SOUL.md line 1.

```powershell
python skills\character_importer\card_importer.py switch "card.png" --force
python skills\character_importer\card_importer.py switch-harem natsume
```
Then /reset.
