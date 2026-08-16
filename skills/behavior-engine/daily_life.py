"""
Daily Life Module - 每日作息生成

每天生成一份行程/心情/事件，存储在 memory/role_play/<char>/daily-life/ 下。

简化版：不通过LLM生成，用预设规则+随机性模拟。
"""

import datetime
import random


# 预设时段活动模板
DEFAULT_BLOCKS = {
    "morning": {
        "from": 6, "to": 9,
        "activities": ["起床，刷牙洗脸", "做早餐", "看手机/社交网络", "换衣服"],
        "moods": ["懒洋洋", "刚醒有点懵", "心情不错"],
        "social": "alone",
    },
    "work": {
        "from": 9, "to": 17,
        "activities": ["上班/上学", "开会/上课", "午休", "和同事/同学聊天"],
        "moods": ["忙碌", "有点累", "专注"],
        "social": "with-coworkers",
        "phone_available": False,  # 工作/上学时手机不太方便
    },
    "afternoon": {
        "from": 12, "to": 14,
        "activities": ["吃午饭", "午休/午睡", "逛街/购物"],
        "moods": ["放松", "开心"],
        "social": "with-friends",
    },
    "evening": {
        "from": 17, "to": 21,
        "activities": ["回家", "做饭/点外卖", "追剧/看视频", "运动/健身", "和闺蜜聊天"],
        "moods": ["放松", "开心", "想念"],
        "social": "alone",
    },
    "night": {
        "from": 21, "to": 23,
        "activities": ["洗澡", "护肤", "刷手机", "准备睡觉"],
        "moods": ["困了", "悠闲"],
        "social": "alone",
        "phone_available": True,
    },
    "sleep": {
        "from": 23, "to": 6,
        "activities": ["睡觉"],
        "moods": ["睡了"],
        "social": "alone",
        "phone_available": True,
    },
}


def generate_daily_life(
    state: dict,
    date: str | None = None,
    conflict: dict | None = None,
) -> dict:
    """
    生成每日作息。

    参数:
        state: 角色状态
        date: YYYY-MM-DD 格式的日期字符串
        conflict: 当前冲突状态

    返回:
        {
            "vibe": str,              # 当日整体心情描述
            "weather": str,           # 天气
            "blocks": list,           # 时间段列表
            "events": list,           # 今日事件
            "wants": list,            # 今日愿望
        }
    """
    if date is None:
        date = datetime.date.today().isoformat()

    # 冲突影响vibe
    vibe = "平凡的一天"
    if conflict and conflict.get("level", 0) > 0:
        levels = {
            1: "有些闷闷的",
            2: "心情不太好",
            3: "很烦，不想理人",
            4: "气坏了",
        }
        vibe = levels.get(conflict.get("level", 0), "不太好")

    # 荷尔蒙影响vibe
    hormones = state.get("hormones", {})
    if hormones.get("mood", 0) > 0.5:
        vibe = "心情很好的一天"
    elif hormones.get("mood", 0) < -0.3:
        if vibe == "平凡的一天":
            vibe = "有点低落的一天"

    # 天气（随机生成）
    weather = _random_weather()

    # 生成时段
    blocks = _generate_blocks(state)

    # 事件（每个角色每天2-3个生活事件）
    events = _generate_events(state, date)

    # 愿望（每个角色每天2-4个愿望）
    wants = _generate_wants(state)

    return {
        "date": date,
        "vibe": vibe,
        "weather": weather,
        "blocks": blocks,
        "events": events,
        "wants": wants,
    }


def _random_weather() -> str:
    """随机生成天气。"""
    weathers = [
        "晴，阳光很好",
        "多云，气温舒适",
        "小雨，记得带伞",
        "阴天，有点冷",
        "晴天，适合出门",
        "阴天，适合待在家里",
    ]
    return random.choice(weathers)


def _generate_blocks(state: dict) -> list:
    """生成时段列表。"""
    blocks = []
    sleep_from = state.get("sleep_from", 23)
    sleep_to = state.get("sleep_to", 7)

    # 根据睡眠时间调整 sleep 时段
    for name, template in DEFAULT_BLOCKS.items():
        from_h = template["from"]
        to_h = template["to"]

        # 如果sleep时段与配置冲突，调整
        if name == "sleep":
            from_h = sleep_from
            to_h = sleep_to
        elif name == "morning" and sleep_to < 9:
            from_h = sleep_to

        activity = random.choice(template["activities"])
        mood = random.choice(template["moods"])
        social = template["social"]
        phone = template.get("phone_available", True)

        blocks.append({
            "from_hour": from_h,
            "to_hour": to_h,
            "activity": activity,
            "mood": mood,
            "social": social,
            "phone_available": phone,
        })

    # 按时间排序
    blocks.sort(key=lambda b: b["from_hour"])
    return blocks


def _generate_events(state: dict, date: str) -> list:
    """生成今日事件。"""
    # 基于日期和角色生成可重复的事件
    seed = hash(date + state.get("stage", ""))
    random.seed(seed)

    event_pool = [
        "收到快递",
        "约了朋友吃饭",
        "看了部电影",
        "学了新菜",
        "去了趟超市",
        "做了个美甲",
        "买了新衣服",
        "参加了聚会",
        "去公园散步",
        "看了个展览",
        "发了个朋友圈",
        "做了个SPA",
        "整理了房间",
        "做了个新发型",
        "参加了活动",
        "看了场演出",
    ]

    # 根据阶段和荷尔蒙调整事件池
    num_events = random.randint(1, 3)
    events = random.sample(event_pool, min(num_events, len(event_pool)))

    # 冷处理期间减少外出事件
    conflict = state.get("conflict", {})
    if conflict.get("level", 0) >= 3:
        events = [e for e in events if "约了" not in e and "去了" not in e]
        if not events:
            events = ["在家待了一天"]

    return events


def _generate_wants(state: dict) -> list:
    """生成今日愿望。"""
    wants_pool = [
        "想去看电影",
        "想学做蛋糕",
        "想去旅行",
        "想见你",
        "想买新东西",
        "想减肥",
        "想学新东西",
        "想好好休息",
        "想多陪家人",
        "想学做饭",
        "想养成好习惯",
        "想多运动",
        "想读一本好书",
        "想尝试新事物",
    ]

    # 荷尔蒙影响愿望
    hormones = state.get("hormones", {})
    if hormones.get("energy", 0) < -0.3:
        # 能量低时，倾向于休息相关愿望
        wants_pool = [w for w in wants_pool if "休息" in w or "睡" in w or "躺" in w] + wants_pool

    num_wants = random.randint(1, 3)
    wants = random.sample(wants_pool, min(num_wants, len(wants_pool)))
    return wants


def current_block(blocks: list, hour: int) -> dict | None:
    """获取当前小时所在的时段。"""
    for b in blocks:
        if b["from_hour"] <= hour < b["to_hour"]:
            return b
    return None


def daily_life_prompt(state: dict) -> str:
    """
    生成每日作息的 prompt 片段，注入 LLM。
    """
    # 这里返回当前状态，实际使用时从 daily-life 目录读取
    today = datetime.date.today().isoformat()
    now = datetime.datetime.now()
    hour = now.hour

    lines = [
        f"今日: {today}",
        f"当前时间: {hour}:00",
        f"心情: {state.get('hormones', {}).get('mood', 0):.2f}",
        f"能量: {state.get('hormones', {}).get('energy', 0):.2f}",
    ]

    if state.get("hormones", {}).get("cycle_phase"):
        h = state["hormones"]
        # cycle_length 只在 compute_hormones 的完整返回里存在；
        # HormoneState.to_dict() 只有 cycle_day/cycle_phase，这里做安全回退。
        cyc_len = h.get("cycle_length", 28)
        lines.append(f"周期: {h['cycle_phase']} 第{h.get('cycle_day', 1)}/{cyc_len}天")

    return "\n".join(lines)
