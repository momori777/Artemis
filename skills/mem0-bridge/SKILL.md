---
name: mem0-bridge
description: Mem0 memory bridge for AI Girlfriend — search/read/write long-term memories from Qdrant vector DB. Works across all channels (WebChat, QQ, Telegram).
---

# mem0-bridge — 长期记忆桥接

Mem0 Qdrant 向量记忆的读/写桥接器，WebChat、QQBot、TelegramBot 共用。

## 架构

- **存储**: Qdrant 嵌入式库，路径随 `OPENCLAW_WORKSPACE` 所在树：`<树>/skills/sakura/data/memory/qdrant/`。仓库侧与 OpenClaw workspace 侧（谢芙蒂那一端）**各有一份独立 store**，两端已于 2026-11-07 全链路跑通；角色通过 `user_id` 隔离
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
| character | user_id（写入域） | lang_instruction |
|-----------|---------|-----------------|
| sakura | sakura | 简体中文 |
| natsume | shiki_natsume（角色卡 id，不是 `natsume`） | 简体中文，保留日文称呼 |
| enola | enola | 简体中文 |
| atori | atori | 简体中文 |
| shifty | shifty（旧记忆在默认域 `sakura`，靠 `legacy_user_ids` 兜底读取） | 简体中文，保留群聊黑话与「指挥官」 |

> 隔离域解析链在 `mem0_bridge.py:scope_ids()`：规范小写域排第一（即写入域），角色卡 id、首字母大写、`legacy_user_ids` 等变体留在候选里，搜索用 `MatchAny`，**写入不会落到旧域**。历史上库里同时出现过 `Sakura`/`sakura`：靠这套候选不致静默 0 命中；要刷齐到规范小写域跑 `python skills/shared/qdrant_rescope.py --apply`。

## 新角色登记清单（漏了任何一步都会静默 0 命中）
1. `skills/shared/mem0_bridge.py:CHARACTERS` 加条目（旧记忆落在别的域时补 `legacy_user_ids`）
2. `artemis_headroom_proxy.py` 的 `CHARACTER_DETECT_KEYWORDS` + `CHARACTER_MEM0_ID` 加角色
3. `skills/mem0-bridge/mem0_behavior_integration.py:CHARACTER_MAP` 加中英文名
4. 重启代理（端口 19251），跑 `python skills/shared/mem0_selfcheck.py --character <新角色>` 验证

## 体检（两端均已跑通，2026-11-07）
```powershell
# 0) 嵌入服务（CPU torch，不占显存），health 应回 {"status":"ok"}
python skills/shared/embedding_server.py
curl http://127.0.0.1:9999/health

# 1) 仓库侧全链路自检（读+写+SmartCrusher/CCR，写后自清）
python skills/shared/mem0_selfcheck.py --character sakura

# 2) OpenClaw workspace 端（谢芙蒂那一侧）自己的 store
python skills/shared/mem0_selfcheck.py --root "$env:USERPROFILE\.openclaw\workspace" --character shifty

# 3) 只读盘库（不需要嵌入服务）：点数 / 隔离域 / ANN 自查询
python skills/shared/qdrant_store_inspect.py
python skills/shared/qdrant_store_inspect.py --store "$env:USERPROFILE\.openclaw\workspace\skills\sakura\data\memory\qdrant"
```
2026-11-07 实测：嵌入 dim=384、norm=1.00；仓库侧 store 5 点（全在 `sakura` 域）；workspace 侧 store 27 点（全在默认域 `sakura`，shifty 读得到）；两端自检 ALL GREEN，SmartCrusher 压缩 + CCR 回取正常。嵌入式 Qdrant 是**单写者**：桌宠/脚本不能同时持有同一个库，自检脚本已自行开关。

## 依赖
- Qdrant SDK (`pip install qdrant-client`)
- Embedding server running on port 9999

依赖装在哪个 Python 就用哪个跑自检；嵌入式 Qdrant/嵌入服务不碰显存，可与 llama 共跑。仓库自带的 `skills/sakura/runtime` venv 只在创建它的那台机器上能用，换机直接用 PATH 里的系统 Python。
