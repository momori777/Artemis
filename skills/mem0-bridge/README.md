# mem0-bridge — 长期记忆桥接 / Long-term Memory Bridge

## 中文

Mem0 Qdrant 向量记忆的读/写桥接器，WebChat、QQBot、TelegramBot 共用。

- **存储**: Qdrant (`skills/sakura/data/memory/qdrant/`)，角色通过 `user_id` 隔离
- **嵌入**: local embedding server (port 9999)，`all-MiniLM-L6-v2`，384 维
- **读**: 向量搜索 → 返回相关记忆，可注入 system prompt
- **写**: 关键词提取 + 向量化 → 写入 Qdrant
- **同步**: 可选，导出 Qdrant → markdown 供 OpenClaw memory_search 索引

### 文件结构

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 完整使用说明（API、角色配置、依赖） |
| `mem0_behavior_integration.py` | 深度联动：行为引擎状态 → mem0 搜索 → 分级注入 LLM context |
| `INTEGRATION_SKILL.md` | 深度联动文档 |

> ⚠️ **模块代码唯一位置**：`skills/shared/mem0_bridge.py`
> （本目录内的 `mem0_bridge.py` 副本已删除，避免双份漂移。）

### 快速使用

```python
# 导入前把 workspace 根加入 sys.path
from skills.shared.mem0_bridge import search_mem0_qdrant, add_memory, list_mem0

search_mem0_qdrant("natsume", "今天心情怎么样", limit=5)
add_memory("natsume", "用户偏好: 喜欢被叫'笨蛋'")
list_mem0("natsume", limit=50)
```

## English

Mem0 Qdrant vector memory read/write bridge, shared by WebChat, QQBot and TelegramBot.

- **Storage**: Qdrant (`skills/sakura/data/memory/qdrant/`), characters isolated by `user_id`
- **Embeddings**: local embedding server (port 9999), `all-MiniLM-L6-v2`, 384-dim
- **Read**: vector search → relevant memories, injectable into system prompt
- **Write**: keyword extraction + embedding → write to Qdrant
- **Sync**: optional, export Qdrant → markdown for OpenClaw memory_search indexing

### Files

| File | Description |
|------|-------------|
| `SKILL.md` | Full usage docs (API, character config, dependencies) |
| `mem0_behavior_integration.py` | Deep integration: behavior-engine state → mem0 search → tiered LLM context injection |
| `INTEGRATION_SKILL.md` | Deep integration docs |

> ⚠️ **Single source of truth for module code**: `skills/shared/mem0_bridge.py`
> (the in-directory copy of `mem0_bridge.py` has been removed to avoid drift.)

### Quick Start

```python
# Add the workspace root to sys.path before importing
from skills.shared.mem0_bridge import search_mem0_qdrant, add_memory, list_mem0

search_mem0_qdrant("natsume", "how are you feeling today", limit=5)
add_memory("natsume", "User preference: likes being called 'baka'")
list_mem0("natsume", limit=50)
```
