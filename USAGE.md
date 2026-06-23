# Artemis — Usage Guide

## 1. Start

windows click shiki.cmd
Linux start.ps1

## 2. Stop

windows click shiki.stop

Linux please ref on start.ps1,I am only rhcsa
cd .. + rm -rf (laugh)

## 3. Debugging

The project has four layers. Debug bottom-up:

| Layer  | Component            | Check |
|--------|----------------------|-------|
| GPU    | llama.cpp            | `http://127.0.0.1:8080/health` |
| Visual | Live2D / Sakura      | Live2D: `http://localhost:19200/api/status`; Sakura: just look at your desktop |
| Skills | TTS / ComfyUI        | Run `skills/tts/tts_call.py` or `skills/comfyui/comfyui_call.py` directly with the right args |
| Hub    | OpenClaw Gateway     | `openclaw gateway status`; logs at `%TEMP%\openclaw\` |
| Ports  | dashboard          | all ports list,check what is on or off
 
**Common issues:**
- llama won't start → check `llama_exe` / `llama_model` paths in `config.yaml`
- ComfyUI/TTS returns a file path but no actual file → run `sync_qqbot_workspace.py` (qqbot agent may be on a stale workspace)
- Sakura crashes on launch → run `start.bat` directly inside `skills/sakura/` to see the error
