# Behavior Engine — AI Girlfriend 行为引擎 / Behavior Engine

## 中文

借鉴 girl-agent 的行为引擎设计，为 Artemis 多角色系统添加独立决策层。
每个角色有独立的评分、冲突、阶段、荷尔蒙状态。

### 架构概览

```
用户消息 → behavior-tick → LLM决策 → moodDelta →
  ├→ RelationshipScore (影响阶段转换)
  ├→ ConflictState (影响冷处理)
  ├→ HormoneState (影响心理基线)
  └→ DailyLife events (影响后续日期)
```

### 文件结构

| 文件 | 说明 |
|------|------|
| `engine.py` | 核心引擎（状态读取+更新） |
| `hormones.py` | 荷尔蒙/生理周期计算（纯数学，不依赖LLM） |
| `conflict.py` | 四级冲突系统 |
| `stages.py` | 9阶段关系系统 |
| `behavior_tick.py` | 行为决策层（每条消息的决策） |
| `online_tick.py` | 在线/睡眠模拟 |
| `daily_life.py` | 每日作息生成 |
| `SKILL.md` | 使用说明 |

### 数据存储

每个角色的状态存放在 `memory/role_play/<char>/` 下：

```
memory/role_play/<char>/
├── relationship.json    # 五维评分 + 阶段 + 冲突 + 荷尔蒙
├── daily-life/          # 每日作息（每天一个 .md 文件）
└── <日期>-*.md          # 对话记忆（现有）
```

### 核心设计原则

1. **分层独立**：每层只做一件事，输出结构化 JSON 状态
2. **不依赖LLM的层先执行**：荷尔蒙(纯数学)→冲突(条件判断)→阶段(阈值检查)→在线(条件+随机)
3. **moodDelta统一入口**：每条消息的 moodDelta 通过 LLM 输出，累加到所有状态
4. **每个角色独立**：不共享评分，每个角色有自己的状态文件

## English

Behavior engine inspired by girl-agent's design, adding an independent decision layer to the Artemis multi-character system.
Each character has its own score, conflict, stage and hormone state.

### Architecture

```
User message → behavior-tick → LLM decision → moodDelta →
  ├→ RelationshipScore (drives stage transitions)
  ├→ ConflictState (drives cold-treatment behavior)
  ├→ HormoneState (drives psychological baseline)
  └→ DailyLife events (affects future days)
```

### Files

| File | Description |
|------|-------------|
| `engine.py` | Core engine (state read/update) |
| `hormones.py` | Hormone / cycle calculation (pure math, no LLM) |
| `conflict.py` | 4-level conflict system |
| `stages.py` | 9-stage relationship system |
| `behavior_tick.py` | Behavior decision layer (per-message decisions) |
| `online_tick.py` | Online/sleep simulation |
| `daily_life.py` | Daily routine generation |
| `SKILL.md` | Usage instructions |

### Data Storage

Per-character state lives under `memory/role_play/<char>/`:

```
memory/role_play/<char>/
├── relationship.json    # 5-dim scores + stage + conflict + hormones
├── daily-life/          # daily routines (one .md per day)
└── <date>-*.md          # conversation memory (existing)
```

### Core Design Principles

1. **Layered independence**: each layer does one thing, emits structured JSON state
2. **LLM-free layers run first**: hormones (math) → conflict (rules) → stages (thresholds) → online (rules + random)
3. **moodDelta as single entry point**: every message's moodDelta comes from LLM output, accumulated into all states
4. **Per-character isolation**: no shared scores; each character has its own state files
