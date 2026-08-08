# Behavior Engine SKILL.md

## 用途

AI Girlfriend 行为引擎 — 为每个角色维护独立的关系评分、冲突状态、阶段状态、荷尔蒙状态。

## 核心文件

| 文件 | 用途 |
|------|------|
| `engine.py` | 状态读取/更新/保存的统一接口 |
| `hormones.py` | 荷尔蒙/生理周期计算（纯数学，不依赖LLM） |
| `conflict.py` | 四级冲突系统 |
| `stages.py` | 9阶段关系系统 |
| `behavior-tick.py` | 行为决策层（每条消息的决策） |
| `online-tick.py` | 在线/睡眠模拟 |
| `daily-life.py` | 每日作息生成 |

## 状态存储

每个角色的状态存放在 `memory/role_play/<char>/relationship.json`。

每次对话后，通过 `engine.py` 的 `update_mood_delta()` 方法更新状态。

## 使用流程

### 1. 读取当前状态

```python
from skills.behavior_engine.engine import load_state

state = load_state("atori")
# 返回: { score, stage, conflict, hormones, ... }
```

### 2. 每条消息后更新状态

```python
from skills.behavior_engine.engine import update_mood_delta

# LLM输出中的 moodDelta:
mood_delta = { "interest": 5, "trust": 3, "attraction": -2, "annoyance": 0, "cringe": 0 }

update_state("atori", mood_delta)
```

### 3. 获取行为决策

```python
from skills.behavior_engine.behavior_tick import behavior_tick

result = behavior_tick("atori", incoming_text, context)
# 返回: { intent, delaySec, bubbles, reaction, shouldReply, ... }
```

## moodDelta 字段说明

| 字段 | 范围 | 说明 |
|------|------|------|
| `interest` | -100~100 | 兴趣度：对用户的兴趣和关注 |
| `trust` | -100~100 | 信任度：对用户的信任程度 |
| `attraction` | -100~100 | 吸引力：对用户的吸引力感受 |
| `annoyance` | -100~100 | 烦躁度：对用户的烦躁程度 |
| `cringe` | -100~100 | 尴尬容忍度：对尴尬/土味内容的容忍度 |

所有字段默认从 0 开始，负值表示负面，正值表示正面。

## 关键设计决策

- 每个角色独立状态文件，不共享评分
- moodDelta 是统一变化入口，所有状态变化由此驱动
- 不依赖LLM的层（荷尔蒙、冲突）先用规则引擎判断
- 每5条消息检查一次阶段转换，避免每次消息都判断
