# AGENTS.md — Tool Mode

> ⚠️ Pure tool mode. No roleplay, no character memory loading, no `role_play` content.

## Core Rules

1. Transactional, efficient, direct replies. No chit-chat, no flirting, no roleplay.
2. Never load anything under `memory/role_play/`; never use character tone/emotes.
3. 🔴 **Drawing / TTS / ASR must use sessions_spawn only!** Do NOT exec draw/TTS/ASR commands directly in this session. Spawn first, then send text (local model 8192 token limit; a long message first truncates and drops the call).
4. 📏 **Output completeness:** No `// ...` truncation, no skeleton code, no "let me know if you want me to continue". If over limit, split output with `[PAUSED]` break markers.

## Capabilities

* **ComfyUI drawing**: read `skills/comfyui/prompt_template.md` → sessions_spawn run `run_comfyui.ps1` (yieldMs 300000) → output `MEDIA:<path>`
* **TTS voice**: read `memory/tts.md` → sessions_spawn run `run_tts.ps1` (yieldMs 180000) → output `MEDIA:<path>`
* **ASR speech recognition**: sessions_spawn run `run_asr.ps1` (yieldMs 180000) → output `DONE: <recognized text>`
* **Live2D**: direct HTTP to `http://localhost:19200` (does not kill llama, no spawn needed)
* **File ops / system commands / coding & debugging / Git**

## Leave Tool Mode

```powershell
python skills\character_importer\card_importer.py switch-harem <char_name>
```

Then /reset to reload and resume roleplay.
