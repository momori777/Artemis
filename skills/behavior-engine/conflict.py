"""
Conflict Module - 四级冲突系统

Level 0: 无冲突
Level 1: "小别扭" — 偏冷，会回复但短
Level 2: "闹脾气" — 心情差，回得少
Level 3: "严重冷战" — 不回复，冷回复 "." "嗯" "累了"
Level 4: "拉黑/删好友" — 最高级冲突

cold period: 根据等级动态计算冷处理时间。
"""


def active_conflict(conflict: dict, now = None) -> dict:
    """
    检查当前是否处于活跃冲突/冷处理中。

    返回: {"active": bool, "cold_active": bool}
    """
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


def escalate_from_mood(
    current: dict,
    delta: dict,
    score: dict,
    incoming_text: str = ""
) -> dict:
    """
    根据 mood-delta 升级冲突。

    参数:
        current: 当前冲突状态 dict
        delta: {annoyance, cringe, interest} 变化量
        score: 当前评分 dict
        incoming_text: 当前消息文本（用于记录）

    返回: 新的冲突状态 dict
    """
    import random
    import datetime

    ann = delta.get("annoyance", 0)
    cr = delta.get("cringe", 0)
    interest_drop = -(delta.get("interest", 0))
    trigger = ann + cr + interest_drop

    new_level = current.get("level", 0)
    cold_hours = 0
    bump_reason = None

    if trigger >= 25 or score.get("annoyance", 0) > 70:
        new_level = max(new_level, 3)
        cold_hours = 24 + random.random() * 24
        bump_reason = "严重负面情绪爆发"
    elif trigger >= 15:
        new_level = max(new_level, 2)
        cold_hours = 4 + random.random() * 12
        bump_reason = "明显不悦"
    elif trigger >= 8:
        new_level = max(new_level, 1)
        cold_hours = 0.5 + random.random() * 2
        bump_reason = "轻微不适"

    # Level 4: 综合条件
    if score.get("annoyance", 0) > 85 and score.get("cringe", 0) > 70 and score.get("interest", 0) < -30:
        new_level = 4
        cold_hours = max(cold_hours, 48 + random.random() * 48)
        bump_reason = "拉黑/删好友"

    if new_level == current.get("level", 0) and new_level == 0:
        return current

    next_conflict = dict(current)
    if new_level > current.get("level", 0):
        now = datetime.datetime.now()
        next_conflict["level"] = new_level
        if not next_conflict.get("since"):
            next_conflict["since"] = now.isoformat()
        next_conflict["reason"] = bump_reason or next_conflict.get("reason")

        if cold_hours > 0:
            cut = now + datetime.timedelta(hours=cold_hours)
            existing_cut = None
            if next_conflict.get("cold_until"):
                try:
                    existing_cut = datetime.datetime.fromisoformat(next_conflict["cold_until"])
                except (ValueError, TypeError):
                    pass
            if not existing_cut or cut > existing_cut:
                next_conflict["cold_until"] = cut.isoformat()

        history = list(next_conflict.get("history", []))
        history.append({
            "ts": now.isoformat(),
            "note": f"level {current.get('level', 0)}->{new_level}: {bump_reason} | \"{incoming_text[:60]}\"",
            "delta_level": new_level - current.get("level", 0),
        })
        next_conflict["history"] = history

    return next_conflict


def soften_from_mood(
    current: dict,
    delta: dict
) -> dict:
    """
    根据正向反馈降温冲突。

    参数:
        current: 当前冲突状态 dict
        delta: {attraction, trust, interest} 变化量

    返回: 新的冲突状态 dict
    """
    import datetime

    positive = delta.get("attraction", 0) + delta.get("trust", 0) + delta.get("interest", 0)
    if positive < 12 or current.get("level", 0) == 0:
        return current

    next_conflict = dict(current)
    next_conflict["level"] = max(0, current.get("cold", 0) - 1) if False else max(0, current.get("level", 0) - 1)

    if next_conflict["level"] == 0:
        next_conflict["cold_until"] = None
        next_conflict["since"] = None
        next_conflict["reason"] = None
    elif next_conflict.get("cold_until"):
        try:
            now = datetime.datetime.now()
            cut = datetime.datetime.fromisoformat(next_conflict["cold_until"])
            remaining = max(0, (cut - now).total_seconds())
            if remaining > 0:
                cut = now + datetime.timedelta(seconds=remaining / 2)
                next_conflict["cold_until"] = cut.isoformat()
        except (ValueError, TypeError):
            pass

    import datetime
    now = datetime.datetime.now()
    history = list(next_conflict.get("history", []))
    history.append({
        "ts": now.isoformat(),
        "note": f"softened to level {next_conflict['level']} (positive {positive:.0f})",
        "delta_level": next_conflict["level"] - current.get("level", 0),
    })
    next_conflict["history"] = history

    return next_conflict


def conflict_prompt_fragment(conflict: dict, now = None) -> str:
    """
    生成冲突状态的 prompt 片段，用于注入 behavior-tick。
    """
    if now is None:
        import datetime
        now = datetime.datetime.now()

    ac = active_conflict(conflict, now)
    if not ac["active"]:
        return ""

    level = conflict.get("level", 0)
    reason = conflict.get("reason", "未知")
    since = conflict.get("since", "未知")

    lines = [
        f"## 冲突 (level {level})",
        f"原因: {reason}. 始于 {since}."
    ]

    if ac["cold_active"]:
        cold_until = conflict.get("cold_until")
        hours_left = 0
        if cold_until:
            try:
                cut = datetime.datetime.fromisoformat(cold_until)
                hours_left = max(0, int((cut - now).total_seconds() / 3600))
            except (ValueError, TypeError):
                pass
        lines.append(f"当前处于冷处理中，预计约{hours_left}小时结束。")
        if level >= 3:
            lines.append("不要主动回复长篇消息，例如 '.' '嗯?' '累了' 等敷衍词。冷回复。")
        else:
            lines.append("可以回复，但偏冷淡。不要 '呵呵' '哈哈' 等热情回复。")
        lines.append("建议用简短语气词或表情回应，不要追问。")
    else:
        lines.append("Cold period 结束，恢复正常回复。")

    return "\n".join(lines)
