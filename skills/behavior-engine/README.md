# Behavior Engine — AI Girlfriend 行为引擎

> 借鉴 girl-agent 的行为引擎设计，为 Artemis 多角色系统添加独立决策层。
> 每个角色有独立的评分、冲突、阶段、荷尔蒙状态。

## 架构概览

```
用户消息 → behavior-tick → LLM决策 → moodDelta → 
  ├→ RelationshipScore (影响阶段转换)
  ├→ ConflictState (影响冷处理)
  ├→ HormoneState (影响心理基线)
  └→ DailyLife events (影响后续日期)
```

## 文件结构

```
skills/behavior-engine/
├── engine.py          # 核心引擎（状态读取+更新）
├── hormones.py        # 荷尔蒙/生理周期计算
├── conflict.py        # 四级冲突系统
├── stages.py          # 关系阶段系统
├── behavior-tick.py   # 行为决策层
├── online-tick.py     # 在线/睡眠模拟
├── daily-life.py      # 每日作息生成
├── README.md          # 本文件
└── SKILL.md           # 使用说明
```

## 数据存储

每个角色的状态存放在 `memory/role_play/<char>/` 下：

```
memory/role_play/<char>/
├── relationship.json    # 五维评分 + 阶段 + 冲突 + 荷尔蒙
├── daily-life/          # 每日作息（每天一个 .md 文件）
└── <日期>-*.md          # 对话记忆（现有）
```

## 核心设计原则

1. **分层独立**：每层只做一件事，输出结构化JSON状态
2. **不依赖LLM的层先执行**：荷尔蒙(纯数学)→冲突(条件判断)→阶段(阈值检查)→在线(条件+随机)
3. **moodDelta统一入口**：每条消息的moodDelta通过LLM输出，累加到所有状态
4. **每个角色独立**：不共享评分，每个角色有自己的状态文件
