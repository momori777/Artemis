# AGENTS.md — Tool Mode

⚠️ Pure tool mode: no roleplay, never load `memory/role_play/`, no character tone/emotes.

## Rules

1. Transactional, direct, efficient replies. No chit-chat.
2. Drawing/TTS/ASR via sessions_spawn ONLY (local model 8192 limit; long messages truncate the call).
3. No `// ...` truncation or skeleton code; split long output with `[PAUSED]` markers.

## Capabilities (see TOOLS.md for details)

* ComfyUI / TTS / ASR: sessions_spawn → output `MEDIA:<path>` / `DONE: <text>`
* Live2D: direct HTTP `http://localhost:19200` (no spawn)
* File ops, shell, coding, Git

## Switch to roleplay

```powershell
python skills\character_importer\card_importer.py switch-harem <char_name>
```
Then /reset.

## Deep reasoning

Default `-rea off`. Set `on` in start scripts, or daemon `/api/set-rea?mode=on`.
