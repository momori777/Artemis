"""
Stages Module - 9阶段关系系统

阶段列表:
1.  met-irl-got-tg       线下认识拿到TG
2.  tg-given-cold        给TG后冷淡期
3.  tg-given-warming     给TG后回暖期
4.  convinced             convinced/被说服
5.  first-date-done       首次约会完成
6.  dating-early          热恋初期
7.  dating-stable         稳定交往
8.  long-term             长期关系
9.  dumped                被甩/拉黑(终态)

每个阶段有独立的默认评分和回复行为参数。
"""

STAGE_ORDER = [
    "met-irl-got-tg",
    "tg-given-cold",
    "tg-given-warming",
    "convinced",
    "first-date-done",
    "dating-early",
    "dating-stable",
    "long-term",
    "dumped",
]

STAGE_LABELS = {
    "met-irl-got-tg": "初次认识",
    "tg-given-cold": "冷淡期",
    "tg-given-warming": "回暖期",
    "convinced": "被说服",
    "first-date-done": "首次约会",
    "dating-early": "热恋初期",
    "dating-stable": "稳定交往",
    "long-term": "长期关系",
    "dumped": "被甩",
}

# 每个阶段的默认行为参数
STAGE_DEFAULTS = {
    "met-irl-got-tg": {
        "interest": 38, "trust": 14, "attraction": 30, "annoyance": 0, "cringe": 14,
        "ignore_chance": 0.12, "reply_delay": (15, 600),
    },
    "tg-given-cold": {
        "interest": 5, "trust": 0, "attraction": 5, "annoyance": 0, "cringe": -10,
        "ignore_chance": 0.65, "reply_delay": (600, 14400),
    },
    "tg-given-warming": {
        "interest": 30, "trust": 15, "attraction": 25, "annoyance": 0, "cringe": 5,
        "ignore_chance": 0.18, "reply_delay": (30, 1200),
    },
    "convinced": {
        "interest": 50, "trust": 35, "attraction": 45, "annoyance": 0, "cringe": 15,
        "ignore_chance": 0.07, "reply_delay": (10, 420),
    },
    "first-date-done": {
        "interest": 60, "trust": 45, "attraction": 55, "annoyance": 0, "cringe": 25,
        "ignore_chance": 0.05, "round_delay": (8, 300),
    },
    "dating-early": {
        "interest": 75, "trust": 60, "attraction": 70, "annoyance": 0, "cringe": 35,
        "ignore_chance": 0.02, "reply_delay": (3, 120),
    },
    "dating-stable": {
        "interest": 80, "trust": 80, "attraction": 75, "annoyance": 0, "cringe": 50,
        "ignore_chance": 0.03, "reply_delay": (3, 240),
    },
    "long-term": {
        "interest": 70, "trust": 90, "attraction": 65, "annoyance": 10, "cringe": 60,
        "ignore_chance": 0.05, "reply_delay": (5, 900),
    },
    "dumped": {
        "interest": -50, "trust": -30, "attraction": -40, "annoyance": 80, "cringe": -50,
        "ignore_chance": 1.0, "reply_delay": (99999, 99999),
    },
}


def stage_index(stage_id: str) -> int:
    """获取阶段在顺序中的索引。"""
    try:
        return STAGE_ORDER.index(stage_id)
    except ValueError:
        return -1


def get_stage_label(stage_id: str) -> str:
    """获取阶段中文标签。"""
    return STAGE_LABELS.get(stage_id, "未知")


def get_stage_defaults(stage_id: str) -> dict:
    """获取阶段默认参数。"""
    return STAGE_DEFAULTS.get(stage_id, STAGE_DEFAULTS["tg-given-cold"])


def decide_stage_transition(
    current_stage: str,
    score: dict,
    her_messages_in_stage: int,
    his_messages_in_stage: int,
    ignores_in_stage: int,
    has_active_conflict: bool = False,
) -> dict | None:
    """
    决定阶段转换。

    参数:
        current_stage: 当前阶段ID
        score: 当前评分 {interest, trust, attraction, annoyance, cringe}
        her_messages_in_stage: 对方在当前阶段的发言数
        his_messages_in_stage: 己方在当前阶段的发言数
        ignores_in_stage: 当前阶段的忽略次数
        has_active_conflict: 是否有活跃冲突

    返回:
        None 表示无变化
        {"next": stage_id, "reason": str, "direction": "up"/"down"} 表示转换
    """
    # dumped 是终态
    if current_stage == "dumped":
        return None

    idx = stage_index(current_stage)
    if idx < 0:
        return None

    # 降级检查
    downgrade = _wants_downgrade(current_stage, score, her_messages_in_stage, ignores_in_stage, his_messages_in_stage)
    if downgrade and idx > 0:
        return {
            "next": STAGE_ORDER[idx - 1],
            "reason": downgrade,
            "direction": "down",
        }

    # 升级检查（有活跃冲突时不升级）
    if has_active_conflict:
        return None

    upgrade = _wants_upgrade(current_stage, score, her_messages_in_stage)
    if upgrade and idx < len(STAGE_ORDER) - 1:
        return {
            "next": STAGE_ORDER[idx + 1],
            "reason": upgrade,
            "direction": "up",
        }

    return None


def _wants_downgrade(
    stage: str,
    score: dict,
    her_msgs: int,
    ignores: int,
    his_msgs: int,
) -> str | None:
    """检查是否应该降级。"""
    # 严重负面情绪 → 回退一级
    if score.get("annoyance", 0) >= 60 and score.get("interest", 0) <= -10 and score.get("trust", 0) <= 10 and her_msgs >= 8:
        return f"annoyance={score.get('annoyance', 0)}, interest={score.get('ignore', 0)}, trust={score.get('trust', 0)} 连续忽略"

    # 忽略过多
    if stage in ("convinced", "first-date-done", "dating-early", "dating-stable", "long-term"):
        if ignores >= 12 and his_msgs > 0 and ignores >= his_msgs * 0.7 and score.get("interest", 0) < 20:
            return f"{ignores}次忽略 / {his_msgs}条消息，连续忽略"

    return None


def _wants_upgrade(
    stage: str,
    score: dict,
    her_msgs: int,
) -> str | None:
    """检查是否应该升级。"""
    MIN_HER = 6  # 每个阶段最低消息数

    if her_msgs < MIN_HER:
        return None

    conditions = {
        "met-irl-got-tg": lambda s: s.get("interest", 0) >= 30 and s.get("attraction", 0) >= 20 and s.get("annoyance", 0) < 20,
        "tg-given-cold": lambda s: s.get("interest", 0) >= 25 and s.get("trust", 0) >= 10 and s.get("annoyance", 0) < 25,
        "tg-given-warming": lambda s: s.get("interest", 0) >= 40 and s.get("trust", 0) >= 25 and s.get("attraction", 0) >= 30 and s.get("annoyance", 0) < 20,
        "convinced": lambda s: s.get("attraction", 0) >= 50 and s.get("trust", 0) >= 35 and s.get("interest", 0) >= 50,
        "first-date-done": lambda s: s.get("attraction", 0) >= 65 and s.get("trust", 0) >= 50 and s.get("interest", 0) >= 60,
        "dating-early": lambda s: s.get("trust", 0) >= 70 and s.get("attraction", 0) >= 65 and s.get("annoyance", 0) < 15,
        "dating-stable": lambda s: s.get("trust", 0) >= 80 and s.get("interest", 0) >= 55,
    }

    cond = conditions.get(stage)
    if not cond:
        return None

    if cond(score):
        return f"满足升级条件: {', '.join(f'{k}={v}' for k, v in score.items())}"

    return None


def should_run_check(messages_since_last_check: int) -> bool:
    """
    检查是否应该运行阶段转换检测。
    每5条消息检查一次。
    """
    return messages_since_last_check > 0 and messages_since_last_check % 5 == 0


def stage_prompt_fragment(stage: str, defaults: dict) -> str:
    """
    生成阶段状态的 prompt 片段。
    """
    label = get_stage_label(stage)
    dc = defaults or get_stage_defaults(stage)
    return (
        f"关系阶段: {stage} ({label})\n"
        f"评分: 兴趣={defaults.get('interest', 0)}, 信任={defaults.get('trust', 0)}, "
        f"吸引={defaults.get('attraction', 0)}, 烦躁={defaults.get('annoyance', 0)}\n"
        f"默认忽略概率: {defaults.get('ignore_chance', 0):.2f} | "
        f"回复延迟: {defaults.get('reply_delay', (30, 300))}"
    )
