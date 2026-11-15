# AGENTS.md — Tool Mode

> ⚠️ Pure tool mode. No roleplay, no character memory loading, no `role_play` content.

## Core Rules

1. Transactional, efficient, direct replies. No chit-chat, no flirting, no roleplay.
2. Never load anything under `memory/role_play/`; never use character tone/emotes.
3. 🔴 **Drawing / TTS must go through the Task Scheduler handoff** (see root `AGENTS.md`). Never exec them directly in this session; the launch is the first tool call — long text first truncates and drops the task. ASR may run via plain `exec`.
4. 📏 **Output completeness:** No `// ...` truncation, no skeleton code, no "let me know if you want me to continue". If over limit, split output with `[PAUSED]` break markers.

## Capabilities

* **ComfyUI drawing**: read `skills/comfyui/prompt_template.md` → launch `skills/comfyui/gpu_handoff/gpu_handoff_launch_strata.ps1` (Task Scheduler handoff) → on wake read `skills/comfyui/gpu_handoff/logs/gpu_handoff_result.json` → output `MEDIA:<path>`
* **TTS voice**: read `memory/tts.md` → Task Scheduler handoff per `skills/tts/SKILL.md` → output `MEDIA:<path>`
* **ASR speech recognition**: plain `exec` `skills/asr/run_asr.ps1` (yieldMs 180000) → output `DONE: <recognized text>`
* **Live2D**: direct HTTP to `http://localhost:19200` (does not kill llama, no handoff task needed)
* **File ops / system commands / coding & debugging / Git**

## VRAM handoff (stop / start the LLM)

The LLM engine (`:8080`, Strata) keeps the GPU resident, so ComfyUI (`:8188`) cannot start while it runs.
Whole-card jobs: **stop LLM → run ComfyUI → restart LLM**, and never `exec` that in your own turn
(killing the engine kills this session) — launch it detached. Scripts: `skills/comfyui/gpu_handoff/`.

## Leave Tool Mode

```powershell
python skills\character_importer\card_importer.py switch-harem <char_name>
```

## 深度思考模式 / Deep Reasoning

默认 `-rea off`（工具调用场景必须）。如需启用深度思考（DeepSeek-style reasoning），
可将所有启动脚本中的 `-rea off` 改为 `-rea on`，其余参数不变。
或者通过 daemon 的 `/api/set-rea?mode=on` 接口动态切换。

Then /reset to reload and resume roleplay.
