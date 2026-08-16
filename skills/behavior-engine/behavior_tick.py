"""
Behavior Tick Module - 行为决策层

每条 incoming 消息进入时，按以下流程决策：

1. 检查 cold-period → level≥1且cold期未结束 → ignore (80%概率)
2. 检查 asleep → 睡眠中且非夜醒 → ignore (85%概率)
3. 检查 nightAwake → 夜间清醒 → 15%忽略 + 50%调用LLM
4. 调用LLM → 输入所有状态 → 输出JSON决策
5. 如果LLM调用失败 → 回退到默认ignore概率

输出: { intent, delaySec, bubbles, reaction, shouldReply, moodDelta }
"""

import math
import random
import datetime


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def is_asleep(state: dict) -> bool:
    """检查是否在睡眠中。

    支持两种睡眠配置：
    - 跨午夜 (sleep_from > sleep_to)，如 23→7：夜间 23:00-24:00 和凌晨 0:00-7:00
    - 白天/不跨午夜 (sleep_from < sleep_to)，如 2→10：2:00-10:00
    """
    now = datetime.datetime.now()
    sleep_from = state.get("sleep_from", 23)
    sleep_to = state.get("sleep_to", 7)

    hour = now.hour

    if sleep_from > sleep_to:
        # 跨午夜：23→7  -> 23:00-24:00 或 0:00-7:00
        return hour >= sleep_from or hour < sleep_to
    elif sleep_from < sleep_to:
        # 不跨午夜：2→10 -> 2:00-10:00
        return sleep_from <= hour < sleep_to
    else:
        # sleep_from == sleep_to：视为无睡眠时段，永不睡着
        return False


def is_night_awake(state: dict) -> bool:
    """检查是否夜间清醒。

    夜间清醒 = 处于睡眠时段但随机醒来（night_wake_chance）。
    只有处于睡眠时段内才可能夜醒，白天不判定为夜醒。
    """
    asleep = is_asleep(state)
    if not asleep:
        return False
    return random.random() < state.get("night_wake_chance", 0.15)


def get_current_hour(state: dict) -> int:
    return datetime.datetime.now().hour


def calculate_ignore_chance(
    state: dict,
    conflict_active: bool,
    cold_active: bool,
    asleep: bool,
    night_awake: bool,
) -> float:
    """
    计算忽略概率。

    基于阶段默认值、通信风格、当前状态计算每条消息的忽略概率。
    """
    stage = state.get("stage", "tg-given-cold")
    defaults = {
        "met-irl-got-tg": 0.12,
        "tg-given-cold": 0.65,
        "tg-given-warming": 0.18,
        "convinced": 0.07,
        "first-date-done": 0.05,
        "dating-early": 0.02,
        "dating-stable": 0.03,
        "long-term": 0.05,
        "dumped": 1.0,
    }
    base = defaults.get(stage, 0.12)

    # 通信风格调整
    notif = state.get("notifications", "normal")
    if notif == "priority":
        base *= 0.3
    elif notif == "muted":
        base *= 1.15
    else:
        base *= 0.75

    # 主动性调整
    init = state.get("initiative", "medium")
    if init == "high":
        base *= 0.75
    elif init == "low":
        base *= 1.15

    # 忽略倾向
    ignore_tendency = state.get("ignore_tendency", 35)
    base *= (0.35 + ignore_tendency / 35)

    # 冷处理
    if cold_active:
        base = min(1.0, base * 2)

    # 睡眠
    if asleep and not night_awake:
        base = min(1.0, base * 3)

    return clamp(base, 0, 1.0)


def calculate_reply_delay(
    state: dict,
    intent: str,
    is_active_dialog: bool = False,
) -> int:
    """
    计算回复延迟（秒）。
    """
    stage = state.get("stage", "tg-given-cold")
    defaults = {
        "met-irl-got-tg": (15, 600),
        "tg-given-cold": (600, 14400),
        "tg-given-warming": (30, 1200),
        "convinced": (10, 420),
        "first-date-done": (8, 300),
        "dating-early": (3, 120),
        "dating-stable": (3, 240),
        "long-term": (5, 900),
        "dumped": (99999, 99999),
    }
    lo, hi = defaults.get(stage, (30, 300))

    delay = random.randint(lo, hi) if lo < hi else lo

    # 通信风格调整
    notif = state.get("notifications", "normal")
    if notif == "priority":
        delay *= 0.45
    elif notif != "muted":
        delay *= 0.8

    init = state.get("initiative", "medium")
    if init == "high":
        delay *= 0.85

    # 活跃对话缩短延迟
    if is_active_dialog:
        base = 8 if notif != "priority" else 3
        spread = 40
        delay = min(delay, base + random.randint(0, spread))

    return clamp(delay, 0, 3600)


def sample_bubbles(state: dict, is_active_dialog: bool = False) -> int:
    """
    采样消息分片数（bubbles）。
    """
    style = state.get("message_style", "balanced")
    r = random.random()

    if style == "one-liners":
        return 1 if not is_active_dialog or r > 0.82 else 2
    elif style == "bursty":
        if is_active_dialog:
            return 2 + random.randint(0, 3)
        return 1 if r < 0.18 else 2 + random.randint(0, 2)
    elif style == "longform":
        if is_active_dialog:
            return 1 if r < 0.2 else 2 + random.randint(0, 1)
        return 1 if r < 0.45 else 2
    else:  # balanced
        if is_active_dialog:
            return 1 if r < 0.3 else (2 if r < 0.82 else 3)
        return 1 if r < 0.55 else (2 if r < 0.9 else 3)


def behavior_tick(
    state: dict,
    incoming_text: str = "",
    is_active_dialog: bool = False,
) -> dict:
    """
    行为决策。每条消息进入时调用。

    参数:
        state: 角色状态字典
        incoming_text: 当前消息文本
        is_active_dialog: 是否正在活跃对话（用户在连续发多条）

    返回:
        {
            "should_reply": bool,
            "delay_sec": int,
            "bubbles": int,
            "typing": bool,
            "intent": str,
            "reaction": str | None,
            "ignore_reason": str | None,
            "mood_delta": dict,
        }
    """
    # 1. 冷处理
    conflict = state.get("conflict", {})
    cold_active = False
    cold_until = conflict.get("cold_until")
    if cold_until:
        try:
            cut = datetime.datetime.fromisoformat(cold_until)
            cold_active = cut > datetime.datetime.now()
        except (ValueError, TypeError):
            pass

    if cold_active and conflict.get("level", 0) >= 1:
        if random.random() < 0.8:
            # cold期间80%忽略
            return {
                "should_reply": False,
                "delay_sec": 0,
                "bubbles": 1,
                "typing": False,
                "intent": "ignore",
                "reaction": None,
                "ignore_reason": "conflict-cold",
                "mood_delta": {},
            }

    # 2. 睡眠
    asleep = is_asleep(state)
    night_awake = is_night_awake(state)

    if asleep and not night_awake:
        if random.random() < 0.85:
            return {
                "should_reply": False,
                "delay_sec": 0,
                "bubbles": 1,
                "typing": False,
                "intent": "left-on-read",
                "reaction": None,
                "ignore_reason": "asleep",
                "mood_delta": {},
            }

    # 3. 夜间清醒
    if night_awake:
        if random.random() < 0.15:
            return {
                "should_reply": False,
                "delay_sec": 0,
                "bubbles": 1,
                "typing": False,
                "intent": "ignore",
                "reaction": None,
                "ignore_reason": "night-fell-asleep",
                "mood_delta": {"annoyance": 5},
            }
        # 50%调用LLM（此处简化为直接返回）
        delay = calculate_reply_delay(state, "short", is_active_dialog)
        return {
            "should_reply": True,
            "delay_sec": clamp(delay, 10, 120),
            "bubbles": 1,
            "typing": True,
            "intent": "short",
            "reaction": None,
            "ignore_reason": None,
            "mood_delta": {"annoyance": 3},
        }

    # 4. 检查是否忽略
    ignore_chance = calculate_ignore_chance(state, conflict.get("level", 0) > 0, cold_active, asleep, night_awake)
    if random.random() < ignore_chance:
        return {
            "should_reply": False,
            "delay_sec": 0,
            "bubbles": 1,
            "typing": False,
            "intent": "ignore",
            "reaction": None,
            "ignore_reason": "normal-ignore",
            "mood_delta": {},
        }

    # 5. 回复决策
    # 检查活跃对话状态
    if is_active_dialog and conflict.get("level", 0) == 0:
        delay = calculate_reply_delay(state, "reply", True)
        bubbles = sample_bubbles(state, True)
        return {
            "should_reply": True,
            "delay_sec": delay,
            "bubbles": bubbles,
            "typing": True,
            "intent": "reply",
            "reaction": None,
            "ignore_reason": None,
            "mood_delta": {"interest": 1},
        }

    # 正常回复
    delay = calculate_reply_delay(state, "reply", is_active_dialog)
    bubbles = sample_bubbles(state, is_active_dialog)

    # 根据当前状态决定表情反应（简化版）
    score = state.get("score", {})
    stage = state.get("stage", "tg-given-cold")
    is_warm = score.get("attraction", 0) > 30 or stage in ("dating-early", "dating-stable", "long-term")
    is_cold = score.get("annoyance", 0) > 40 or stage == "tg-given-cold"

    reaction = None
    if is_warm:
        warm_reactions = ["😊", "🥰", "💕", "🤗", "💖"]
        reaction = random.choice(warm_reactions)
    elif is_cold:
        cold_reactions = ["😒", "😑", "🙄", "😤"]
        reaction = random.choice(cold_reactions)

    return {
        "should_reply": True,
        "delay_sec": delay,
        "bubbles": bubbles,
        "typing": True,
        "intent": "reply",
        "reaction": reaction,
        "ignore_reason": None,
        "mood_delta": {},
    }


def build_behavior_prompt(state: dict, incoming: str, context: dict = None) -> str:
    """
    构建行为决策的 prompt，用于注入 LLM。

    参数:
        state: 角色状态
        incoming: 当前消息
        context: 额外上下文 {presence, conflict, daily_life}

    返回:
        prompt 字符串
    """
    score = state.get("score", {})
    stage = state.get("stage", "tg-given-cold")
    conflict = state.get("conflict", {})
    hormones = state.get("hormones", {})

    lines = [
        f"关系阶段: {stage}",
        f"评分: 兴趣={score.get('interest', 0)}, 信任={score.get('trust', 0)}, "
        f"吸引={score.get('attraction', 0)}, 烦躁={score.get('annoyance', 0)}, 尴尬={score.get('cringe', 0)}",
        f"荷尔蒙: 能量={hormones.get('energy', 0):.2f}, 易怒={hormones.get('irritability', 0):.2f}, "
        f"亲密度={hormones.get('affection', 0):.2f}, 性欲={hormones.get('libido', 0):.2f}",
        f"心情: {hormones.get('mood', 0):.2f}",
    ]

    # 冲突
    if conflict.get("level", 0) > 0:
        ac = active_conflict(conflict)
        if ac["cold_active"]:
            lines.append(f"当前处于冷处理中（level {conflict.get('level', 0)}）")

    # 在线状态
    asleep = is_asleep(state)
    night_awake = is_night_awake(state)
    if asleep and not night_awake:
        lines.append("正在睡觉，不在线")
    elif night_awake:
        lines.append("夜间清醒")
    else:
        lines.append(f"在线 (当前{get_current_hour(state)}:00)")

    lines.append(f"\n当前消息: {incoming}")

    return "\n".join(lines)


# 从 conflict.py 导入的辅助函数
def active_conflict(conflict: dict, now = None) -> dict:
    """检查冲突活跃状态。"""
    if now is None:
        import datetime
        now = datetime.datetime.now()

    cold = False
    cold_until = conflict.get("cold_until")
    if cold_until:
        try:
            cut = datetime.datetime.fromisoformat(cold_until)
            cold = cut > now
        except (ValueError, TypeError):
            cold = False

    return {
        "active": conflict.get("level", 0) > 0,
        "cold_active": cold,
    }
