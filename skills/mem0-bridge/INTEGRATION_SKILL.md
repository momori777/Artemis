# Mem0 × Behavior Engine 深度联动

每轮对话时自动执行：行为引擎状态 → 状态驱动的 mem0 搜索 → 分级注入 LLM context → 写回。

## 核心文件

- `mem0_behavior_integration.py` — 联动模块（每轮调用入口）
- `mem0_bridge.py` — mem0 Qdrant 读写（原有）
- `../behavior-engine/engine.py` — 行为引擎状态管理
- `../behavior-engine/hormines.py` — 荷尔蒙/周期
- `../behavior-engine/conflict.py` — 四级冲突
- `../behavior-engine/stages.py` — 9阶段关系

## 每轮调用

```python
from skills.mem0_bridge import mem0_behavior_integration as mbi

# 每轮对话调用
context = mbi.run_integration(
    character="atori",        # natsume/enola/sakura/atori
    query="用户消息文本",
    messages=[               # 可选，用于状态更新
        {"role": "user", "content": "..." },
        {"role": "assistant", "content": "..." },
    ]
)
# context 应注入到 LLM prompt 前面

# 可选：写回 mem0 + 更新状态
facts = mbi.extract_mem0_facts_from_messages(messages, "atori")
new_state = mbi.sync_to_behavior_state("atori", messages, current_state)
```

## 状态驱动的搜索策略

| 状态条件 | 搜索词 | limit |
|---------|--------|-------|
| cold 期/annoyance>50 | {角色} 喜欢 讨厌 记忆 回忆 | 3 |
| dating 期 | {角色} 约会 约定 承诺 回忆 习惯 | 5 |
| long-term | {角色} 习惯 日常 未来 回忆 | 4 |
| 回暖期/affection>0.6 | {角色} 爱好 兴趣 习惯 回忆 | 5 |
| affection<0.3 | {角色} 印象 感觉 记忆 | 3 |
| 其他 | {角色} {query} | 5 |

## 分级注入

| 分数 | 注入方式 |
|------|---------|
| >=0.7 | 必须体现（强相关） |
| >=0.5 | 自然融入 |
| >=0.3 | 可选参考 |
| <0.3 | 忽略 |

**当所有 score=0.0（embedding server 离线）时**：全部作为参考注入。

## 前提条件

- **embedding server** 必须运行在 port 9999
- Qdrant 数据在 `skills/sakura/data/memory/qdrant/`
- 每个角色有 `memory/role_play/<char>/relationship.json`

## CLI

```bash
# 搜索
python skills/mem0-bridge/mem0_behavior_integration.py natsume "今天心情怎么样"
# 手动添加记忆
python skills/mem0-bridge/mem0_bridge.py add natsume "喜欢甜食，讨厌下雨天"
# 列出记忆
python skills/mem0-bridge/mem0_bridge.py list natsume --limit 10
```
