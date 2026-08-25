---
name: mem0-bridge
description: Mem0 memory bridge for AI Girlfriend — search/read/write long-term memories from Qdrant vector DB. Works across all channels (WebChat, QQ, Telegram).
---

# mem0-bridge — 长期记忆桥接

Mem0 Qdrant 向量记忆的读/写桥接器，WebChat、QQBot、TelegramBot 共用。

## 架构

- **存储**: Qdrant (`skills/sakura/data/memory/qdrant/`)，四角色通过 `user_id` 隔离
- **嵌入**: local embedding server (port 9999)，`all-MiniLM-L6-v2`，384 维
- **读**: 向量搜索 → 返回相关记忆，可注入 system prompt
- **写**: 关键词提取 + 向量化 → 写入 Qdrant
- **同步**: 可选，导出 Qdrant → markdown 供 OpenClaw memory_search 索引

## 深度联动（每轮自动）

`mem0_behavior_integration.py` 每轮对话自动执行：行为引擎状态 → 状态驱动的 mem0 搜索 → 分级注入 LLM context。

详见 `mem0-bridge/INTEGRATION_SKILL.md`。

## 使用

> ⚠️ 模块唯一位置：`skills/shared/mem0_bridge.py`（mem0-bridge 目录内不再有副本）。
> 导入前把 workspace 根加入 sys.path，或直接把 `skills/shared` 加入 sys.path。

### 搜索记忆（每轮对话注入）
```python
from skills.shared.mem0_bridge import search_mem0_qdrant, CHARACTERS
results = search_mem0_qdrant("natsume", "今天心情怎么样", limit=5)
# returns [{"id": ..., "memory": "...", "score": 0.85, "metadata": {...}}]
```

### 写入记忆
```python
from skills.shared.mem0_bridge import add_memory
add_memory("natsume", "用户偏好: 喜欢被叫'笨蛋'")
```

### 列出所有记忆
```python
from skills.shared.mem0_bridge import list_mem0
all_memories = list_mem0("natsume", limit=50)
```

### daemon 集成（自动搜索+写入）
```python
# 搜索上下文
context = _mem0_search_context(character_id, query, limit=5)
# 写入
facts = _extract_facts_from_messages(recent_messages)
for f in facts: add_memory(character_id, f)
```

## 角色配置
| character | user_id | lang_instruction |
|-----------|---------|-----------------|
| sakura | sakura | 简体中文 |
| natsume | natsume | 简体中文，保留日文称呼 |
| enola | enola | 简体中文 |
| atori | atori | 简体中文 |

## 依赖
- Qdrant SDK (`pip install qdrant-client`)
- Embedding server running on port 9999
