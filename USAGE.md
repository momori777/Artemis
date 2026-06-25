# Artemis — Usage Guide

## 启动方式 — 两条通道

Artemis 提供两种 Agent 运行时，按需选用：

### 方式 A：OpenClaw（生产主通道）

```
用途：QQ Bot、Telegram Bot、WebChat 浏览器聊天
涵盖：角色扮演、TTS、ComfyUI、ASR、Live2D、记忆系统、定时任务

Windows: 双击 shiki.cmd
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

Windows: .\claude-code.ps1
Linux:   bash claude-code.sh

快捷操作：
  .\claude-code.ps1 -BoardOnly    ← 只开任务看板（浏览器）
  .\claude-code.ps1 -KillBoard    ← 关闭任务看板
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

## 2. Stop

Windows: 双击 shiki-stop.cmd（或 shiki.cmd 托盘右键 Stop All）

Linux:   参考 start.ps1 / start.sh

## 3. Debugging

The project has four layers. Debug bottom-up:

| Layer  | Component            | Check |
|--------|----------------------|-------|
| GPU    | llama.cpp            | `http://127.0.0.1:8080/health` |
| Visual | Live2D / Sakura      | Live2D: `http://localhost:19200/api/status`; Sakura: just look at your desktop |
| Skills | TTS / ComfyUI / ASR  | Run `skills/tts/tts_call.py`, `skills/comfyui/comfyui_call.py`, or `skills/asr/asr_call.py <audio>` directly |
| Hub    | OpenClaw Gateway     | `openclaw gateway status`; logs at `%TEMP%\openclaw\` |
| MCP    | Claude Code          | `python .claude/artemis_mcp_server.py` (stdin: `{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}`) |
| Board  | Task Board           | `http://127.0.0.1:19280` — AgentRQ-style task queue UI |
| Ports  | Dashboard            | Shiki Daemon dashboard at `http://127.0.0.1:19260` shows all service statuses |

**Common issues:**
- llama won't start → check `llama_exe` / `llama_model` paths in `config.yaml`
- ComfyUI/TTS returns a file path but no actual file → run `sync_qqbot_workspace.py`
- Sakura crashes on launch → run `start.bat` directly inside `skills/sakura/` to see the error
- Task Board not loading → check if `python .claude/task_board_api.py` is running (port 19280)
- Claude Code MCP tools not responding → artemis_mcp_server.py crashes on startup. Run `python .claude/artemis_mcp_server.py` directly and paste `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}` to see the error
