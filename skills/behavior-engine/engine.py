"""
Behavior Engine - 核心引擎模块

每个角色的关系状态存放于:
    memory/role_play/<char>/relationship.json

每个字段说明见 types.py。
"""

import json
import os
import math

# ============================================================
# 类型定义
# ============================================================

# 关系评分：每维 -100 ~ 100
class RelationshipScore:
    """五维关系评分。每维范围 -100 ~ 100。"""
    def __init__(self, interest: float = 0, trust: float = 0,
                 attraction: float = 0, annoyance: float = 0,
                 cringe: float = 0):
        self.interest = round(clamp(interest, -100, 100), 2)
        self.trust = round(clamp(trust, -100, 100), 2)
        self.attraction = round(clamp(attraction, -100, 100), 2)
        self.annoyance = round(clamp(annoyance, -100, 100), 2)
        self.cringe = round(clamp(cringe, -100, 100), 2)

    def to_dict(self) -> dict:
        return {
            "interest": self.interest,
            "trust": self.trust,
            "attraction": self.attraction,
            "annoyance": self.annoyance,
            "cringe": self.cringe,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RelationshipScore":
        return cls(
            interest=d.get("interest", 0),
            trust=d.get("trust", 0),
            attraction=d.get("attraction", 0),
            annoyance=d.get("annoyance", 0),
            cringe=d.get("cringe", 0),
        )

    def __repr__(self):
        return f"Score(i={self.interest}, t={self.trust}, a={self.attraction}, an={self.annoyance}, c={self.cringe})"


# 冲突状态
class ConflictState:
    """四级冲突系统。"""
    def __init__(self, level: int = 0, cold_until: str | None = None,
                 reason: str | None = None, since: str | None = None,
                 history: list | None = None):
        self.level = level  # 0=无, 1=小别扭, 2=闹脾气, 3=严重冷战, 4=拉黑
        self.cold_until = cold_until
        self.reason = reason
        self.since = since
        self.history = history or []

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "cold_until": self.cold_until,
            "reason": self.reason,
            "since": self.since,
            "history": self.history or [],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ConflictState":
        return cls(
            level=d.get("level", 0),
            cold_until=d.get("cold_until"),
            reason=d.get("reason"),
            since=d.get("since"),
            history=d.get("history", []),
        )


# 荷尔蒙状态（简化版）
class HormoneState:
    """简化荷尔蒙/心理状态。"""
    def __init__(self, energy: float = 0.0, mood: float = 0.0,
                 affection: float = 0.5, irritability: float = 0.2,
                 libido: float = 0.5, cycle_day: int = 1,
                 cycle_phase: str = "early-follicular",
                 pmdd: bool = False):
        self.energy = round(clamp(energy, -1, 1), 3)
        self.mood = round(clamp(mood, -1, 1), 3)
        self.affection = round(clamp(affection, 0, 1), 3)
        self.irritability = round(clamp(irritability, 0, 1), 3)
        self.libido = round(clamp(libido, 0, 1), 3)
        self.cycle_day = cycle_day
        self.cycle_phase = cycle_phase
        self.pmdd = pmdd

    def to_dict(self) -> dict:
        return {
            "energy": self.energy,
            "mood": self.mood,
            "affection": self.affection,
            "irritability": self.irritability,
            "libido": self.libido,
            "cycle_day": self.cycle_day,
            "cycle_phase": self.cycle_phase,
            "pmdd": self.pmdd,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "HormoneState":
        return cls(
            energy=d.get("energy", 0.0),
            mood=d.get("mood", 0.0),
            affection=d.get("affection", 0.5),
            irritability=d.get("irritability", 0.2),
            libido=d.get("libido", 0.5),
            cycle_day=d.get("cycle_day", 1),
            cycle_phase=d.get("cycle_phase", "early-follicular"),
            pmdd=d.get("pmdd", False),
        )


# 完整状态
class CharacterState:
    """角色完整行为状态。"""
    def __init__(self, score: RelationshipScore | None = None,
                 stage: str = "tg-given-cold",
                 conflict: ConflictState | None = None,
                 hormones: HormoneState | None = None,
                 last_updated: str | None = None,
                 birth_seed: int = 42,
                 age: int = 18,
                 sleep_from: int = 23,
                 sleep_to: int = 7,
                 night_wake_chance: float = 0.15,
                 ignore_tendency: int = 35,
                 vibe: str = "warm",
                 initiative: str = "medium",
                 message_style: str = "balanced",
                 life_sharing: str = "medium",
                 notifications: str = "normal",
                 her_messages_in_stage: int = 0,
                 his_messages_in_stage: int = 0,
                 ignores_in_stage: int = 0,
                 messages_since_last_check: int = 0):
        self.score = score or RelationshipScore()
        self.stage = stage
        self.conflict = conflict or ConflictState()
        self.hormones = hormones or HormoneState()
        self.last_updated = last_updated or None
        self.birth_seed = birth_seed
        self.age = age
        self.sleep_from = sleep_from
        self.sleep_to = sleep_to
        self.night_wake_chance = night_wake_chance
        self.ignore_tendency = ignore_tendency
        self.vibe = vibe
        self.initiative = initiative
        self.message_style = message_style
        self.life_sharing = life_sharing
        self.notifications = notifications
        self.her_messages_in_stage = her_messages_in_stage
        self.his_messages_in_stage = his_messages_in_stage
        self.ignores_in_stage = ignores_in_stage
        self.messages_since_last_check = messages_since_last_check

    def to_dict(self) -> dict:
        return {
            "score": self.score.to_dict(),
            "stage": self.stage,
            "conflict": self.conflict.to_dict(),
            "hormones": self.hormones.to_dict(),
            "last_updated": self.last_updated,
            "birth_seed": self.birth_seed,
            "age": self.age,
            "sleep_from": self.sleep_from,
            "sleep_to": self.sleep_to,
            "night_wake_chance": self.night_wake_chance,
            "ignore_tendency": self.ignore_tendency,
            "vibe": self.vibe,
            "initiative": self.initiative,
            "message_style": self.message_style,
            "life_sharing": self.life_sharing,
            "notifications": self.notifications,
            "her_messages_in_stage": self.her_messages_in_stage,
            "his_messages_in_stage": self.his_messages_in_stage,
            "ignores_in_stage": self.ignores_in_stage,
            "messages_since_last_check": self.messages_since_last_check,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CharacterState":
        return cls(
            score=RelationshipScore.from_dict(d.get("score", {})),
            stage=d.get("stage", "tg-given-cold"),
            conflict=ConflictState.from_dict(d.get("conflict", {})),
            hormones=HormoneState.from_dict(d.get("hormones", {})),
            last_updated=d.get("last_updated"),
            birth_seed=d.get("birth_seed", 42),
            age=d.get("age", 18),
            sleep_from=d.get("sleep_from", 23),
            sleep_to=d.get("sleep_to", 7),
            night_wake_chance=d.get("night_wake_chance", 0.15),
            ignore_tendency=d.get("ignore_tendency", 35),
            vibe=d.get("vibe", "warm"),
            initiative=d.get("initiative", "medium"),
            message_style=d.get("message_style", "balanced"),
            life_sharing=d.get("life_sharing", "medium"),
            notifications=d.get("notifications", "normal"),
            her_messages_in_stage=d.get("her_messages_in_stage", 0),
            his_messages_in_stage=d.get("his_messages_in_stage", 0),
            ignores_in_stage=d.get("ignores_in_stage", 0),
            messages_since_last_check=d.get("messages_since_last_check", 0),
        )


# ============================================================
# 路径与IO
# ============================================================

def get_state_path(char: str) -> str:
    """获取角色状态文件路径。

    状态文件位于项目根的 memory/role_play/<char>/relationship.json。
    engine.py 位于 skills/behavior-engine/engine.py，因此：
      dirname(dirname(__file__)) = skills/，再上翻一层 ".." = 项目根。
    """
    base = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..", "memory", "role_play", char, "relationship.json"
    )
    return os.path.normpath(base)


def load_state(char: str) -> CharacterState:
    """加载角色状态。如果不存在则返回默认状态。"""
    path = get_state_path(char)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        state = CharacterState.from_dict(d)
        return state
    return CharacterState()


def save_state(char: str, state: CharacterState) -> None:
    """保存角色状态。"""
    import datetime
    state.last_updated = datetime.datetime.now().isoformat()
    path = get_state_path(char)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)


# ============================================================
# moodDelta 更新
# ============================================================

def update_state(char: str, mood_delta: dict | None = None,
                 should_reply: bool = True,
                 intent: str = "reply") -> CharacterState:
    """
    更新角色状态。

    参数:
        char: 角色名称
        mood_delta: LLM输出的moodDelta {interest, trust, attraction, annoyance, cringe}
        should_reply: 是否回复
        intent: 意图 "reply"/"ignore"/"short"/"left-on-read"/"reaction-only"/"leave-chat"

    返回:
        更新后的状态对象
    """
    state = load_state(char)

    if mood_delta:
        # 累加评分
        for field in ["interest", "trust", "attraction", "annoyance", "cringe"]:
            old = getattr(state.score, field)
            delta = mood_delta.get(field, 0)
            # 每个delta限制在 -20~+20，避免单条消息影响过大
            delta = max(-20, min(20, delta))
            setattr(state.score, field, round(old + delta, 2))

    # 更新计数器。语义：
    # - her_messages_in_stage = 角色（她）在本阶段的发言数
    # - his_messages_in_stage = 用户（他）在本阶段的发言数
    # update_state 默认在每次产生一条角色回复后调用，因此这里递增「她」的发言数。
    state.messages_since_last_check += 1
    if not should_reply and intent in ("ignore", "left-on-read"):
        state.ignores_in_stage += 1
    if should_reply and intent in ("reply", "short"):
        state.her_messages_in_stage += 1  # 角色（她）回复了一条

    # 每5条检查一次阶段转换
    if state.messages_since_last_check >= 5:
        state.messages_since_last_check = 0

    save_state(char, state)
    return state


def reset_state(char: str) -> CharacterState:
    """重置角色状态（类似 :reset 命令）。"""
    new = CharacterState(
        score=RelationshipScore(),
        stage="tg-given-cold",
        conflict=ConflictState(),
        hormones=HormoneState(),
    )
    save_state(char, new)
    return new


# ============================================================
# 工具函数
# ============================================================

def clamp(v: float, lo: float, hi: float) -> float:
    """限制值在 [lo, hi] 范围内。"""
    return max(lo, min(hi, v))
