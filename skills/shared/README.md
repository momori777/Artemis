# shared — 共享库 / Shared Library

## 中文

跨技能共享的 Python 工具库（非独立技能，供其他技能 import）。

| 文件 | 说明 |
|------|------|
| `mem0_bridge.py` | **mem0 Qdrant 记忆桥接（唯一代码位置）**，mem0-bridge 技能的模块本体 |
| `mem0_sync_cron.py` | mem0 → markdown 定时同步脚本 |
| `llama_config.py` / `llama_utils.py` | llama-server 配置与工具 |
| `llama_lifecycle.py` | llama-server 启停生命周期管理 |
| `restart_llama_degraded.ps1` | 降级重启脚本 |
| `context_trimming.py` | 上下文裁剪（包装 headroom SmartCrusher） |
| `embedding_server.py` | 本地 embedding 服务（port 9999） |
| `start_embedding_server.ps1` | embedding 服务启动脚本 |
| `vram.py` / `VRAM_LEVELS.md` | VRAM 分级管理 |

## English

Cross-skill shared Python utilities (not a standalone skill; imported by other skills).

| File | Description |
|------|-------------|
| `mem0_bridge.py` | **mem0 Qdrant memory bridge (single source of truth)**, module body of the mem0-bridge skill |
| `mem0_sync_cron.py` | Scheduled mem0 → markdown sync script |
| `llama_config.py` / `llama_utils.py` | llama-server configuration and utilities |
| `llama_lifecycle.py` | llama-server start/stop lifecycle management |
| `restart_llama_degraded.ps1` | Degraded restart script |
| `context_trimming.py` | Context trimming (wraps headroom SmartCrusher) |
| `embedding_server.py` | Local embedding server (port 9999) |
| `start_embedding_server.ps1` | Embedding server start script |
| `vram.py` / `VRAM_LEVELS.md` | VRAM tier management |
