# Artemis — Usage Guide

## Launch Methods — Three Channels

Artemis provides three Agent runtimes, choose as needed:

> 📁 **Configuration examples** for all three platforms are in [`Agents/`](Agents/README.md) — copy and adapt to get started.

### Method A: OpenClaw (Production Main Channel)

```
Usage: QQ Bot, Telegram Bot, WebChat Browser Chat
Covers: Roleplay, TTS, ComfyUI, ASR, Live2D, Memory System, Scheduled Tasks

Windows: Double-click shiki-start.cmd (or system tray)
Linux:   bash start.sh

Interfaces after startup:
  WebChat → http://127.0.0.1:19270
  Task Board → http://127.0.0.1:19280
  OpenClaw Gateway → port 18789
```

### Method B: Claude Code + CCR (Terminal Dev Channel)

```
Usage: Terminal Agent, AgentRQ-style Task Board
Covers: TTS, ComfyUI, ASR, Live2D, Memory System, Task Queue
Not included: QQ/TG/WX message channels

Prerequisite: npm install -g @anthropic-ai/claude-code

Windows: .\claude-code-ccr.ps1      (CCR Gateway version, frontend uses local llama)
         .\claude-code.ps1          (No CCR, direct connect to OpenClaw)
Linux:   bash claude-code-ccr.sh
         bash claude-code.sh

Quick operations:
  .\claude-code-ccr.ps1 -BoardOnly    ← Open Task Board only (browser)
  .\claude-code-ccr.ps1 -KillBoard    ← Close Task Board
  Stop CCR: .\stop-claude-code-ccr.ps1

CCR Pipeline: Claude Code ─→ CCR Gateway (:3456) ─→ llama-server (:9931) / Strata (:8080)
Config:       Agents/claude-code-ccr/  (profile settings, .claude.json, CLAUDE.md)
Note:         CCR isolates ~/.claude into profile dirs; edit profile copies, not global
```

### Method C: DeepSeek Harness (dsh) — Community RP Focus

```
Usage: dsh CLI / Web UI, plugin-based roleplay ecosystem
Covers: LLM chat via existing backends (Strata :8080 / llama.cpp :9931), RP plugins
Not included: QQ/TG message channels, TTS, ComfyUI (use OpenClaw/Claude Code for those)

Prerequisite: Node 24+, npm install -g @deepseek-ai/dsh (or run setup-dsh.ps1)

Setup:  powershell -ExecutionPolicy Bypass -File setup-dsh.ps1
Web UI: dsh web  (npx @deepseek-ai/dsh web, no install needed)
CLI:    dsh

Config:       Agents/deepseek-harness/  (credentials, profiles, workspace)
Profiles:     ~/.dsh/profiles/<name>/  (cordis.yml + cordis.patch.yml + package.json)
Bundles:      @deepseek-ai/dsh-base + dsh-web-app (defined in profile package.json)
Patch layer:  cordis.patch.yml overrides bundle defaults (model, UI, providers)

Architecture: Layered env + YAML credentials, no monolithic system prompt.
              References existing inference backends directly — no model duplication.
              Web profile patch includes Strata :8080 as OpenAI-compatible provider.
```

### Feature Coverage Comparison

| Feature               | OpenClaw | Claude Code+CCR | DeepSeek Harness |
|-----------------------|----------|-----------------|------------------|
| QQ Bot messages       | ✅       | ❌              | ❌               |
| Telegram Bot          | ✅       | ❌              | ❌               |
| WebChat browser       | ✅       | ❌              | Web UI (dsh web) |
| Terminal chat         | ❌       | ✅              | ✅ (dsh CLI)     |
| TTS voice             | ✅       | ✅              | ❌               |
| ComfyUI image gen     | ✅       | ✅              | ❌               |
| ASR speech recognition| ✅       | ✅              | ❌               |
| Live2D desktop pet    | ✅       | ✅              | ❌               |
| Character switch      | ✅       | ✅              | ✅ (plugins)     |
| mem0 memory           | ✅       | ✅              | ❌               |
| Scheduled tasks       | ✅       | ❌              | ❌               |
| Task board            | ❌       | ✅              | ❌               |
| RP plugin ecosystem   | ❌       | ❌              | ✅               |

> 💡 **Config reference**: All three platforms' example configs are in [`Agents/`](Agents/README.md).

## Model Configuration (change config.yaml to swap models)

All launch entry points (`shiki_daemon.py` / `start.ps1` / `restart_llama_rea.bat` /
`restart_llama_degraded.ps1` / `llama_lifecycle.py`) use `skills/shared/llama_config.py`
for parameter parsing, with **no hardcoded model paths**. To swap models, just edit `config.yaml`:

```yaml
llama_model: "E:\\Qwen3.6-27B-Fable-MTP-Q4_K_S.gguf"   # GGUF file path (single source of truth)
llama_model_name: "qwen3.6-27b"                        # API alias (leave empty to auto-use filename)
llama_model_id: "llama/qwen3.6-27b"                    # model id (leave empty to auto-set = local/<name>)
llama_api_key: "123456"                                # API key (leave empty to skip --api-key)
```

Key mechanisms:

| Mechanism | Description |
|-----------|-------------|
| **model_profiles preset matching** | Automatically matches launch parameters (`ctk/ctv/batch/cpu_moe/spec_draft_n_max/rea`) by `llama_model` filename keywords, no manual parameter table adjustment needed |
| **MTP auto-detection** | When model name contains `mtp`, automatically adds `--spec-type draft-mtp`; non-MTP models won't get it |
| **model_id auto-calibration** | If `llama_model_id` suffix doesn't match `llama_model_name` (e.g., stale old value `…/qwen3.6-35b`), auto-corrects to `…/<name>` |
| **API key auth** | When `llama_api_key` is non-empty, adds `--api-key <key>`; inference endpoints require `Authorization: Bearer <key>`; headroom proxy / sakura / shiki_daemon automatically include key, `/health` remains unauthenticated |
| **llama_model_map** | For runtime model switching (via `shiki_daemon`'s `/switch_model` endpoint) |

> ⚠️ **Stop/start debugging** (verified 2026-08): After changing `llama_model`, run `python skills/shared/llama_lifecycle.py stop 8080` to stop the old model, then `start 8080` to load the new model, `/v1/models` returns the new alias immediately, inference chain (including MTP draft) works normally.

## 2. Stop

Windows: Double-click shiki-stop.cmd

Linux:   bash stop.sh

## 3. Debugging

The project has seven layers. Debug bottom-up:

| Layer  | Component            | Check |
|--------|----------------------|-------|
| GPU    | llama.cpp            | `http://127.0.0.1:8080/health` |
| Proxy  | Headroom Proxy       | `http://127.0.0.1:19251/api/status` — mem0 + SmartCrusher for OpenClaw Gateway |
| Visual | Live2D / Sakura      | Live2D: `http://localhost:19200/api/status`; Sakura: just look at your desktop |
| API    | Artemis Bridge       | `http://127.0.0.1:19250/api/status` — TTS + ComfyUI API (does NOT proxy LLM) |
| Skills | TTS / ComfyUI / ASR  | Run `skills/tts/tts_call.py`, `skills/comfyui/comfyui_call.py`, or `skills/asr/asr_call.py <audio>` directly |
| Hub    | OpenClaw Gateway     | `openclaw gateway status`; logs at `%TEMP%\openclaw\` |
| MCP    | Claude Code          | `python .claude/artemis_mcp_server.py` (stdin: `{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}`) |
| Board  | Task Board           | `http://127.0.0.1:19280` — AgentRQ-style task queue UI |
| Ports  | Dashboard            | Shiki Daemon dashboard at `http://127.0.0.1:19260` shows all service statuses |

**Common issues:**
- llama won't start → check `llama_exe` / `llama_model` paths in `config.yaml`
- OpenClaw local model times out → check headroom-proxy: `http://127.0.0.1:19251/api/status`; restart if needed: `python artemis_headroom_proxy.py --port 19251`
- ComfyUI/TTS returns a file path but no actual file → run `sync_qqbot_workspace.py`
- Artemis Bridge TTS/ComfyUI fails → check `http://127.0.0.1:19250/api/status`
- Sakura crashes on launch → run `start.bat` directly inside `skills/sakura/` to see the error
- Task Board not loading → check if `python .claude/task_board_api.py` is running (port 19280)
- Claude Code MCP tools not responding → artemis_mcp_server.py crashes on startup. Run `python .claude/artemis_mcp_server.py` directly and paste `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}` to see the error
