"""
Mem0 ↔ Behavior Engine 深度联动

每轮对话时：
1. 从 behavior engine 读取角色状态
2. 根据状态 + 查询词调用 mem0 搜索
3. 将搜索结果注入 LLM context
4. 对话结束后自动写回 mem0 + 更新行为引擎状态
"""

import json
import sys
import io
from pathlib import Path
from datetime import datetime

# Only redirect stdout when running as CLI, not when imported as module
if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except (ValueError, AttributeError):
        pass

# ── 路径 ──────────────────────────────────────────────────────
WORKSPACE = Path(r"C:\Users\TK\.openclaw\workspace")
GIRLFRIEND_ROOT = Path(r"D:\AI_Girlfriend")
MEM0_BRIDGE = GIRLFRIEND_ROOT / "skills" / "shared"  # mem0_bridge.py 唯一位置（single source of truth）
BEHAVIOR_ENGINE = GIRLFRIEND_ROOT / "skills" / "behavior-engine"
MEMORY_DIR = GIRLFRIEND_ROOT / "memory" / "role_play"

# ── 角色 → user_id 映射 ──────────────────────────────────────
CHARACTER_MAP = {
    "natsume": "natsume",
    "四季夏目": "natsume",
    "夏目": "natsume",
    "sakura": "sakura",
    "夜乃桜": "sakura",
    "夜乃樱": "sakura",
    "enola": "enola",
    "atori": "atori",
    "atori2d": "atori",
    "atri": "atori",
}


def resolve_character(char_name: str) -> str | None:
    """将各种名字映射到标准 user_id"""
    if not char_name:
        return None
    for key, uid in CHARACTER_MAP.items():
        if key.lower() in char_name.lower() or char_name.lower() in key.lower():
            return uid
    # 反向查找
    for key, uid in CHARACTER_MAP.items():
        if char_name.lower() in uid.lower():
            return uid
    return None


def load_behavior_state(character: str) -> dict:
    """加载行为引擎状态"""
    path = MEMORY_DIR / character / "relationship.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_relevant_mem0_context(character: str, query: str, behavior_state: dict) -> str:
    """
    获取与当前行为状态相关的 mem0 记忆。

    策略：
    - 根据当前阶段(hormones.conflict/affection)决定搜索深度
    - 根据当前阶段调整 query：
        cold → 搜索 "喜欢/讨厌/记住的"
        warm → 搜索 "爱好/习惯/回忆"
        dating → 搜索 "承诺/约会/约定"
        long-term → 搜索 "习惯/日常/未来"
    """
    stage = behavior_state.get("stage", "")
    score = behavior_state.get("score", {})
    hormones = behavior_state.get("hormones", {})

    # 根据状态调整查询
    if "冷" in str(behavior_state.get("conflict", {}).get("reason", "")) or score.get("annoyance", 0) > 50:
        base_query = f"{character} 喜欢 讨厌 记忆 回忆"
        limit = 3
    elif stage in ("dating-early", "dating-stable"):
        base_query = f"{character} 约会 约定 承诺 回忆 习惯"
        limit = 5
    elif stage == "long-term":
        base_query = f"{character} 习惯 日常 未来 回忆"
        limit = 4
    elif stage == "tg-given-warming" or score.get("affection", 0) > 0.6:
        base_query = f"{character} 爱好 兴趣 习惯 回忆"
        limit = 5
    elif score.get("affection", 0) < 0.3:
        base_query = f"{character} 印象 感觉 记忆"
        limit = 3
    else:
        base_query = f"{character} {query}"
        limit = 5

    # Import mem0 bridge using importlib (avoids sys.stdout issues)
    import importlib.util
    sys.path.insert(0, str(MEM0_BRIDGE))
    spec = importlib.util.spec_from_file_location('mb', str(MEM0_BRIDGE / 'mem0_bridge.py'))  # skills/shared/mem0_bridge.py
    if spec and spec.loader:
        mb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mb)
        search_mem0_qdrant = mb.search_mem0_qdrant
    else:
        return ""

    results = search_mem0_qdrant(character, base_query, limit=limit)
    if not results:
        return ""

    # Check if all scores are 0.0 (embedding server down or cold start)
    all_zero = all(r.get("score", 0) == 0.0 for r in results)

    # 按 score 分级
    high = []
    medium = []
    low = []
    for r in results:
        if r.get("score", 0) >= 0.7:
            high.append(r["memory"])
        elif r.get("score", 0) >= 0.5:
            medium.append(r["memory"])
        elif r.get("score", 0) >= 0.3:
            low.append(r["memory"])

    # When all scores are 0.0 (embedding server not running),
    # include all results as "fallback" to avoid empty context
    if all_zero and not high and not medium and not low:
        # Include top results as low-relevance fallback
        low = [r["memory"] for r in results[:3]]

    parts = []
    if high:
        parts.append("## 强相关长期记忆 (score>=0.7，必须体现):\n" + "\n".join(f"• {m}" for m in high))
    if medium:
        parts.append("## 中等相关长期记忆 (score>=0.5，自然融入):\n" + "\n".join(f"• {m}" for m in medium))
    if low:
        prefix = "## 弱相关长期记忆 (score>=0.3，可选参考):\n" if not all_zero else "## 长期记忆 (embedding server 离线，全部作为参考):\n"
        parts.append(prefix + "\n".join(f"• {m}" for m in low))

    return "\n\n".join(parts)


def extract_mem0_facts_from_messages(messages: list[dict], character: str) -> list[str]:
    """从对话历史中提取可存入 mem0 的事实。"""
    facts = []
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if not content or len(content) < 5:
            continue

        # 提取人名、地点、时间、喜好、习惯等
        if role == "user":
            # 用户说过的关键信息
            for pattern in [
                r"我喜欢(.{1,30})", r"喜欢(.{1,30})", r"讨厌(.{1,30})",
                r"不喜欢(.{1,30})", r"觉得(.{1,30})", r"记得(.{1,30})",
                r"应该(.{1,30})", r"以后(.{1,30})", r"喜欢(.{1,30})",
            ]:
                import re
                matches = re.findall(pattern, content)
                for m in matches:
                    fact = f"{character} 用户: {m}"
                    if fact not in facts:
                        facts.append(fact)
        elif role == "assistant":
            # 角色说过的关键信息
            for pattern in [
                r"我喜欢(.{1,30})", r"喜欢(.{1,30})", r"讨厌(.{1,30})",
                r"记得(.{1,30})", r"应该(.{1,30})", r"以后(.{1,30})",
                r"喜欢(.{1,30})", r"心情(.{1,30})", r"状态(.{1,30})",
            ]:
                import re
                matches = re.findall(pattern, content)
                for m in matches:
                    fact = f"{character} 自身: {m}"
                    if fact not in facts:
                        facts.append(fact)

    return facts[:20]


def sync_to_behavior_state(character: str, messages: list[dict] | None, behavior_state: dict) -> dict:
    """
    根据对话内容更新行为引擎状态，并在满足条件时触发阶段转换。

    策略：
    - 每轮递增消息计数
    - 每5条消息检查一次阶段转换（should_run_check）
    - 转换结果写回 relationship.json（save_state）
    """
    # 导入行为引擎
    sys.path.insert(0, str(BEHAVIOR_ENGINE))
    from engine import update_state, save_state
    from stages import decide_stage_transition, should_run_check

    # 本轮消息（messages 可能为 None，做防御）
    if not messages:
        messages = []
    user_msgs = sum(1 for m in messages if isinstance(m, dict) and m.get("role") == "user" and len(str(m.get("content", ""))) > 3)
    assistant_msgs = sum(1 for m in messages if isinstance(m, dict) and m.get("role") == "assistant" and len(str(m.get("content", ""))) > 3)

    # 用户在本轮至少发了一条：递增他（用户）的发言计数，并触发一次状态更新
    his_delta = 1 if user_msgs > 0 else 0

    new_state = update_state(character, {
        "interest": 0, "trust": 0, "attraction": 0, "annoyance": 0, "cringe": 0,
    }, intent=("reply" if assistant_msgs > 0 else "ignore"))

    # 记录用户发言计数（本轮用户消息对应「他」的发言）
    if his_delta:
        new_state.his_messages_in_stage += 1

    # 每5条消息检查阶段转换
    if should_run_check(new_state.messages_since_last_check):
        conflict_active = new_state.conflict.get("level", 0) > 0
        trans = decide_stage_transition(
            new_state.stage,
            new_state.score.to_dict(),
            new_state.her_messages_in_stage,
            new_state.his_messages_in_stage,
            new_state.ignores_in_stage,
            conflict_active,
        )
        if trans:
            # 写回新阶段
            new_state.stage = trans["next"]
            print(f"[behavior-engine] Stage transition: -> {trans['next']} ({trans['reason']})")
    
    # 落盘
    save_state(character, new_state)

    return new_state.to_dict()


def build_full_context(character: str, query: str, behavior_state: dict, recent_messages: list[dict] = None) -> str:
    """
    构建完整的注入上下文。

    包含：
    1. 行为引擎状态（阶段/评分/冲突/荷尔蒙）
    2. Mem0 相关记忆（按相关度分级）
    3. 每日作息（如果适用）
    """
    lines = []

    # ── 1. 行为引擎状态 ──
    score = behavior_state.get("score", {})
    stage = behavior_state.get("stage", "unknown")
    conflict = behavior_state.get("conflict", {})
    hormones = behavior_state.get("hormones", {})

    lines.append(f"## 当前状态")
    lines.append(f"关系阶段: {stage}")
    lines.append(f"评分: 兴趣={score.get('interest', 0)}, 信任={score.get('trust', 0)}, "
                 f"吸引={score.get('attraction', 0)}, 烦躁={score.get('annoyance', 0)}, 尴尬={score.get('cringe', 0)}")

    energy = hormones.get("energy", 0)
    mood = hormones.get("mood", 0)
    affection = hormones.get("affection", 0)
    irritability = hormones.get("irritability", 0)

    # 状态描述
    state_desc = []
    if energy > 0.4:
        state_desc.append("精力充沛")
    elif energy < -0.3:
        state_desc.append("很困")
    if mood > 0.4:
        state_desc.append("心情好")
    elif mood < -0.2:
        state_desc.append("心情低落")
    if irritability > 0.6:
        state_desc.append("容易烦躁")
    if affection > 0.7:
        state_desc.append("很亲昵")
    if state_desc:
        lines.append(f"状态: " + "，".join(state_desc))
    else:
        lines.append("状态: 正常")

    if conflict.get("level", 0) > 0:
        lines.append(f"⚠️ 冲突等级 {conflict['level']}: {conflict.get('reason', '未知')}")
        cold_until = conflict.get("cold_until")
        if cold_until:
            try:
                from datetime import datetime as dt
                cut = dt.fromisoformat(cold_until)
                now = dt.now()
                hours_left = max(0, int((cut - now).total_seconds() / 3600))
                lines.append(f"冷处理中，剩余约 {hours_left} 小时")
            except (ValueError, TypeError):
                pass

    lines.append("")

    # ── 2. Mem0 记忆 ──
    mem0_context = get_relevant_mem0_context(character, query, behavior_state)
    if mem0_context:
        lines.append(mem0_context)
        lines.append("")

    # ── 3. 每日作息 ──
    now = datetime.now()
    hour = now.hour
    lines.append(f"当前时间: {hour}:00")

    if hormones.get("cycle_phase"):
        cp = hormones.get("cycle_phase", "")
        cd = hormones.get("cycle_day", 1)
        cl = hormones.get("cycle_length", 28)
        if cd and cl:
            lines.append(f"生理周期: {cp} 第{cd}/{cl}天")

    return "\n".join(lines)


def run_integration(character: str, query: str, messages: list[dict] = None) -> str:
    """
    主入口：每轮对话调用。

    Args:
        character: 角色名（natsume/sakura/enola/atori）
        query: 用户消息
        messages: 对话历史（用于提取事实和更新状态）

    Returns:
        注入上下文字符串，应附加到 system prompt 或 user message 前面

    副作用：
        - 调用 sync_to_behavior_state，递增消息计数并检查阶段转换（写回 relationship.json）
    """
    # 1. 加载行为状态
    behavior_state = load_behavior_state(character)
    if not behavior_state:
        return ""

    # 2. 构建完整上下文
    context = build_full_context(character, query, behavior_state, messages)

    # 3. 写回状态 + 触发阶段转换（确保阶段系统真正推进，而非只读）
    try:
        sync_to_behavior_state(character, messages, behavior_state)
    except Exception as e:
        print(f"[behavior-engine] sync_to_behavior_state failed: {e}")

    return context


# ── CLI ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mem0 ↔ Behavior Engine 联动")
    parser.add_argument("character", help="角色名")
    parser.add_argument("query", help="用户消息")
    parser.add_argument("--show-all", action="store_true", help="显示所有记忆（不分级）")

    args = parser.parse_args()

    context = run_integration(args.character, args.query)
    if context:
        print(context)
    else:
        print("[mem0-behavior-engine] No relevant memories found or empty behavior state.")
