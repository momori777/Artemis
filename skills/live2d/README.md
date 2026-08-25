# Live2D 桌面宠物控制 Skill / Live2D Desktop Pet Control Skill

## 中文

通过 HTTP API 控制屏幕上的 Live2D 桌面宠物。**不杀 llama-server，不需要 sessions_spawn**，直接 `exec` 调用即可。

- **Bridge**：`localhost:19200` (HTTP) + `19201` (WebSocket)
- **bridge 未在线时**：`Start-Process node live2d-bridge.mjs`（工作目录 `%USERPROFILE%\.openclaw\workspace\live2d`）

### API 速查

| 端点 | 参数 | 说明 |
|------|------|------|
| `/api/motion?name=X` | motion名 | 播放动作 |
| `/api/expression?name=X` | expression名 | 切换表情 |
| `/api/message?text=X&duration=毫秒` | URL编码文本 | 对话气泡（默认5000ms） |
| `/api/emotion?motion=X&expression=X&text=X` | 任意组合 | 动作+表情+气泡一次调用 |
| `/api/speak?action=start&text=X` / `end` | 文本 | 口型同步开/关 |
| `/api/status` | 无 | 检查在线状态 |

### 文件结构

| 文件/目录 | 说明 |
|-----------|------|
| `SKILL.md` | 完整手册（Motion 速查表、情绪映射、TTS 口型联动、角色切换） |
| `scripts/` | 控制脚本 |
| `media/` | 媒体资源 |

### 快速使用

```powershell
# 表情/动作/气泡 三合一
Invoke-WebRequest -Uri "http://localhost:19200/api/emotion?motion=Tap摸头&text=主人~" -Method GET | Out-Null
```

## English

Controls the on-screen Live2D desktop pet via HTTP API. **Does NOT kill llama-server; no sessions_spawn needed** — call directly with `exec`.

- **Bridge**: `localhost:19200` (HTTP) + `19201` (WebSocket)
- **If bridge is offline**: `Start-Process node live2d-bridge.mjs` (working dir `%USERPROFILE%\.openclaw\workspace\live2d`)

### API Reference

| Endpoint | Params | Description |
|----------|--------|-------------|
| `/api/motion?name=X` | motion name | Play motion |
| `/api/expression?name=X` | expression name | Switch expression |
| `/api/message?text=X&duration=ms` | URL-encoded text | Speech bubble (default 5000ms) |
| `/api/emotion?motion=X&expression=X&text=X` | any combo | Motion + expression + bubble in one call |
| `/api/speak?action=start&text=X` / `end` | text | Lip-sync on/off |
| `/api/status` | none | Check online status |

### Files

| File/Dir | Description |
|----------|-------------|
| `SKILL.md` | Full manual (motion tables, emotion mapping, TTS lip-sync, character switching) |
| `scripts/` | Control scripts |
| `media/` | Media assets |

### Quick Start

```powershell
# Motion + expression + bubble in one call
Invoke-WebRequest -Uri "http://localhost:19200/api/emotion?motion=TapHead&text=Master~" -Method GET | Out-Null
```
