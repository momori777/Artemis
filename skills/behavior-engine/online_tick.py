"""
Online Tick Module - 在线/睡眠模拟

模拟真实人的在线不规律性：
- 不在时持续在线（通过发消息体现自然在线）
- 睡眠中85%概率忽略
- 忙碌时段不在线
- cold period 影响在线频率
"""

import random
import datetime


def decide_online(
    state: dict,
    recent_send_ms: int = 0,
    in_active_dialog: bool = False,
) -> dict:
    """
    决定在线状态。

    参数:
        state: 角色状态
        recent_send_ms: 上次发消息到现在的时间（毫秒），0表示很久没发
        in_active_dialog: 是否正在活跃对话

    返回:
        {
            "online": bool,           # 是否在线
            "next_tick_sec": int,     # 下次检查间隔（秒）
            "reason": str,            # 原因
        }
    """
    # 活跃对话中：自然在线，不需要显示在线
    if in_active_dialog:
        return {
            "online": False,
            "next_tick_sec": 90,
            "reason": "active-dialog (natural online)",
        }

    # 最近发过消息：自然在线
    if recent_send_ms < 90000:
        return {
            "online": False,
            "next_tick_sec": 90,
            "reason": "recent-send (natural online)",
        }

    # 睡眠检查
    asleep = is_asleep(state)
    night_awake = is_night_awake(state)

    if asleep and not night_awake:
        return {
            "online": False,
            "next_tick_sec": max(20 * 60, min(state.get("sleep_to", 7) * 60, 90 * 60)),
            "reason": "asleep",
        }

    # cold period: 减少在线频率
    conflict = state.get("conflict", {})
    cold_until = conflict.get("cold_until")
    if cold_until:
        try:
            cut = datetime.datetime.fromisoformat(cold_until)
            if cut > datetime.datetime.now():
                return {
                    "online": False,
                    "next_tick_sec": random.randint(120, 300),
                    "reason": "cold period",
                }
        except (ValueError, TypeError):
            pass

    # 在线概率（基于配置）
    online_prob = state.get("online_prob", 0.3)
    online = random.random() < online_prob

    if online:
        window_min = state.get("online_window_min", 2)
        return {
            "online": True,
            "next_tick_sec": random.randint(45, min(150, window_min * 60)),
            "reason": "presence-online",
        }
    else:
        return {
            "online": False,
            "next_tick_sec": random.randint(60, 600),
            "reason": "offline",
        }


def is_asleep(state: dict) -> bool:
    """检查是否在睡眠时间段。"""
    now = datetime.datetime.now()
    sleep_from = state.get("sleep_from", 23)
    sleep_to = state.get("sleep_to", 7)
    hour = now.hour

    if sleep_from < sleep_to:
        return hour >= sleep_from or hour < sleep_to
    else:
        return hour >= sleep_from or hour < sleep_to


def is_night_awake(state: dict) -> bool:
    """检查是否夜间清醒。"""
    if random.random() < state.get("night_wake_chance", 0.15):
        return True
    return False
