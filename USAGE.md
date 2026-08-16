# Artemis — Usage Guide

## 启动方式 — 两条通道

Artemis 提供两种 Agent 运行时，按需选用：

### 方式 A：OpenClaw（生产主通道）

```
用途：QQ Bot、Telegram Bot、WebChat 浏览器聊天
涵盖：角色扮演、TTS、ComfyUI、ASR、Live2D、记忆系统、定时任务

Windows: 双击 shiki-start.cmd（或待机托盘）
Linux:   bash start.sh

启动后可用界面：
  WebChat → http://127.0.0.1:19270
  任务看板 → http://127.0.0.1:19280
  OpenClaw Gateway → port 18789
```

### 方式 B：Claude Code（终端开发通道）

```
用途：终端 Agent、AgentRQ 风格任务看板
涵盖：TTS、ComfyUI、ASR、Live2D、记忆系统、任务队列
不含：QQ/TG/WX 消息通道

前提：npm install -g @anthropic-ai/claude-code

Windows: .\claude-code-ccr.ps1      (CCR 网关版，前端走本地 llama)
         .\claude-code.ps1          (无 CCR，直连 OpenClaw)
Linux:   bash claude-code-ccr.sh
         bash claude-code.sh

快捷操作：
  .\claude-code-ccr.ps1 -BoardOnly    ← 只开任务看板（浏览器）
  .\claude-code-ccr.ps1 -KillBoard    ← 关闭任务看板
  停止CCR: .\stop-claude-code-ccr.ps1

CCR 链路：Claude Code ─→ CCR 网关(:3456) ─→ llama-server(:8080)
```

### 功能覆盖对比

| 功能            | OpenClaw | Claude Code |
|-----------------|----------|-------------|
| QQ Bot 消息     | ✅       | ❌          |
| Telegram Bot    | ✅       | ❌          |
| WebChat 浏览器  | ✅       | ❌          |
| 终端对话        | ❌       | ✅          |
| TTS 语音        | ✅       | ✅          |
| ComfyUI 画图    | ✅       | ✅          |
| ASR 语音识别    | ✅       | ✅          |
| Live2D 桌宠     | ✅       | ✅          |
| 角色切换        | ✅       | ✅          |
| mem0 记忆       | ✅       | ✅          |
| 定时任务        | ✅       | ❌          |
| 任务看板        | ❌       | ✅          |

## 模型配置（改 config.yaml 就能换模型）

所有启动入口（`shiki_daemon.py` / `start.ps1` / `restart_llama_rea.bat` /
`restart_llama_degraded.ps1` / `llama_lifecycle.py`）统一走 `skills/shared/llama_config.py`
解析启动参数，**无硬编码模型路径**。换模型只需改 `config.yaml`：

```yaml
llama_model: "E:\\Qwen3.6-27B-Fable-MTP-Q4_K_S.gguf"   # GGUF 文件路径（唯一真源）
llama_model_name: "qwen3.6-27b"                        # API alias（留空自动取文件名）
llama_model_id: "llama/qwen3.6-27b"                    # model id（留空自动 = local/<name>）
```

关键机制：

| 机制 | 说明 |
|------|------|
| **model_profiles 预设匹配** | 按 `llama_model` 文件名关键字自动匹配启动参数（`ctk/ctv/batch/cpu_moe/spec_draft_n_max/rea`），无需手动调参数表 |
| **MTP 自动检测** | 模型名含 `mtp` 时自动加 `--spec-type draft-mtp`，非 MTP 模型不会误加 |
| **model_id 自动校准** | 若 `llama_model_id` 后缀与 `llama_model_name` 不一致（例如残留旧值 `…/qwen3.6-35b`），会自动修正为 `…/<name>` |
| **llama_model_map** | 运行时切换模型用（`shiki_daemon` 的 `/switch_model` 接口） |

> ⚠️ **停启调试**（2026-08 已验证）：改 `llama_model` 后，`python skills/shared/llama_lifecycle.py stop 8080` 停旧模型，再 `start 8080` 拉新模型，`/v1/models` 即返回新 alias，推理链路（含 MTP draft）正常。

## 2. Stop

Windows: 双击 shiki-stop.cmd

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
