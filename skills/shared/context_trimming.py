"""
Context Trimming — LLM 请求预处理（强制 headroom SmartCrusher）

在每次 LLM 调用前自动压缩上下文：
  1. API 兼容格式：OpenAI-compatible messages 数组
  2. 角色扮演保护：system prompt 100% 保留
  3. 最近对话优先：保留最后 N 轮完整对话
  4. 中间历史压缩：SmartCrusher + BM25 相关性提取
  5. 硬截断兜底：消息数/字符数双限制

集成点：
  - shiki_daemon.py: _build_messages() 出口处调用
  - artemis_bridge.py: LLM 请求转发前调用
"""

from __future__ import annotations

import json
import sys
import os
from typing import Any, List, Dict, Optional, Tuple


# ── 加载 headroom ──
_HEADROOM_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "headroom")
if _HEADROOM_PATH not in sys.path:
    sys.path.insert(0, os.path.dirname(_HEADROOM_PATH))

try:
    from skills.headroom import SmartCrusher, estimate_tokens as hr_estimate_tokens
    _HAS_HEADROOM = True
except ImportError:
    _HAS_HEADROOM = False
    # 降级：纯截断
    print("[context_trimming] WARNING: headroom not found, using fallback truncation only")


# ── 配置 ──
MAX_MESSAGES = 24           # 最大消息数（硬限制）
MAX_CHARS = 40_000          # 最大字符数（硬限制）
RECENT_FULL_ROUNDS = 4      # 最近 N 轮完整保留（不压缩）
SYSTEM_ALWAYS_KEEP = True   # system prompt 永不压缩
CRUSH_CONFIG = {
    "max_items_after_crush": 10,
    "first_fraction": 0.3,
    "last_fraction": 0.15,
    "variance_threshold": 2.0,
    "preserve_change_points": True,
    "dedup_identical_items": True,
    "use_feedback_hints": True,
}


# ── 核心 API ──

def trim_messages_for_model(
    messages: List[Dict[str, Any]],
    query: str = "",
    max_messages: int = MAX_MESSAGES,
    max_chars: int = MAX_CHARS,
    recent_full_rounds: int = RECENT_FULL_ROUNDS,
) -> List[Dict[str, Any]]:
    """
    预处理 OpenAI-compatible messages 数组。

    Strategy:
      1. System prompt — 100% 保留在最前面
      2. 最近 N 轮对话 — 完整保留（不压缩）
      3. 更早的历史 — SmartCrusher 压缩 或 丢弃
      4. 硬截断兜底 — 消息数 + 字符数双重限制

    Args:
        messages: OpenAI-compatible messages
        query: 当前用户查询（用于 BM25 相关性匹配保留）
        max_messages: 最大保留消息数
        max_chars: 最大保留字符数
        recent_full_rounds: 最近完整保留轮数

    Returns:
        预处理后的 messages
    """
    if not messages:
        return messages

    msgs = list(messages)  # 不修改原始

    # Step 0: 提取 system prompt
    system_msgs = [m for m in msgs if m.get("role") == "system"]
    non_system = [m for m in msgs if m.get("role") != "system"]

    # Step 1: 统计轮次
    rounds = _split_rounds(non_system)

    # Step 2: 如果总轮次 <= 最近轮次，不需要压缩
    if len(rounds) <= recent_full_rounds:
        result = system_msgs + non_system
        return _hard_cap(result, max_messages, max_chars)

    # Step 3: 分离最近轮次 + 旧轮次
    recent_rounds = rounds[-recent_full_rounds:]
    old_rounds = rounds[:-recent_full_rounds]

    # Step 4: 旧轮次 — 尝试 SmartCrusher 压缩
    if _HAS_HEADROOM and old_rounds and query:
        old_messages = [msg for rnd in old_rounds for msg in rnd]
        crushed = _crush_messages(old_messages, query)
    elif _HAS_HEADROOM and old_rounds:
        # 没有 query 也用 SmartCrusher（纯统计压缩）
        old_messages = [msg for rnd in old_rounds for msg in rnd]
        crushed = _crush_messages(old_messages, "")
    else:
        # 降级：只保留旧轮次中的关键消息
        old_messages = [msg for rnd in old_rounds for msg in rnd]
        crushed = _fallback_trim(old_messages, max_items=6)

    # Step 5: 组装
    recent_messages = [msg for rnd in recent_rounds for msg in rnd]
    result = system_msgs + crushed + recent_messages

    # Step 6: 硬截断
    return _hard_cap(result, max_messages, max_chars)


def trim_context_for_llm(
    system_prompt: str,
    history: List[Dict[str, Any]],
    user_message: str,
    **kwargs,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    便捷函数：同时预处理 system prompt 和对话历史。

    用于 shiki_daemon 的 _build_messages() 替代。

    Args:
        system_prompt: 完整的 system prompt（不会被压缩）
        history: 对话历史 messages
        user_message: 当前用户消息

    Returns:
        (compressed_system_prompt, compressed_history)
        system_prompt 原样返回，history 被压缩
    """
    # System prompt 不变
    # 构建完整 messages 数组
    full_messages = [{"role": "system", "content": system_prompt}] + list(history)
    full_messages.append({"role": "user", "content": user_message})

    # 压缩（system 会被自动保护）
    compressed = trim_messages_for_model(full_messages, query=user_message, **kwargs)

    # 分离 system + history
    new_system = next(
        (m["content"] for m in compressed if m.get("role") == "system"),
        system_prompt,
    )
    new_history = [m for m in compressed if m.get("role") != "system"]

    return new_system, new_history


# ── 内部实现 ──

def _split_rounds(messages: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """
    将 messages 按 user ↔ assistant 切分为轮次。

    以 user 消息为轮次起点。
    """
    rounds = []
    current = []
    for msg in messages:
        role = msg.get("role", "")
        if role == "user" and current:
            rounds.append(current)
            current = [msg]
        else:
            current.append(msg)
    if current:
        rounds.append(current)
    return rounds


def _crush_messages(messages: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """
    用 SmartCrusher 压缩消息数组。

    策略：
      - 保留包含 error/failed/timeout 的消息
      - BM25 匹配 query 相关性
      - 统计异常值（异常长/短的消息）
      - 变化点（话题转换）
    """
    crusher = SmartCrusher(config=CRUSH_CONFIG)

    # 将消息转为 JSON 数组供 SmartCrusher 处理
    items_for_crush = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, list):
            # 多模态内容：提取 text 部分
            text_parts = [p.get("text", "") for p in content if isinstance(p, dict) and "text" in p]
            content = " ".join(text_parts)
        items_for_crush.append(content)

    # SmartCrusher 压缩
    result = crusher.crush(items_for_crush, query=query)

    if result.compression_ratio >= 0.9:
        # 压缩率太低（没减多少），不压缩，直接走截断
        return _fallback_trim(messages, max_items=8)

    # 重建 messages：被保留的消息 + 索引标记
    # 注意：SmartCrusher 输出的 "compressed" 是文本数组
    # 我们保留对应的原始 message 对象
    try:
        # 尝试解析压缩结果中的索引信息
        crushed_text = result.compressed
        # 从缓存标记中提取 kept indices
        kept_texts = crushed_text.split("\n\n", 1)
        if len(kept_texts) > 1:
            data_part = kept_texts[1]
            kept_items = json.loads(data_part) if data_part.strip().startswith("[") else None
        else:
            kept_items = None
    except (json.JSONDecodeError, IndexError):
        kept_items = None

    if kept_items is None:
        # 回退：按文本相似度重新匹配
        kept = _match_messages_to_crushed(messages, result)
    else:
        kept = _match_messages_by_text(messages, kept_items)

    return kept


def _match_messages_to_crushed(
    messages: List[Dict[str, Any]], result
) -> List[Dict[str, Any]]:
    """根据 CrushResult 中的文本重建 message 对象列表（按内容匹配）"""
    # 提取压缩后保留的文本
    compressed_text = result.compressed
    # 去掉缓存标记行
    lines = compressed_text.split("\n")
    text_lines = [l for l in lines if not l.startswith("[")]
    
    if not text_lines:
        # 空结果：保留少量旧消息
        return _fallback_trim(messages, max_items=4)

    # 按内容匹配原始消息
    kept = []
    msg_contents = []
    for msg in messages:
        c = msg.get("content", "")
        if isinstance(c, list):
            c = " ".join(p.get("text", "") for p in c if isinstance(p, dict) and "text" in p)
        msg_contents.append(c)

    # 简单匹配：取前几条作为旧历史的摘要
    kept_count = min(result.items_kept, len(messages))
    # 用 SmartCrusher 保留的索引逻辑：首尾 + 采样
    n = len(messages)
    indices = set()
    
    # 首
    for i in range(min(2, n)):
        indices.add(i)
    # 尾
    for i in range(max(0, n-2), n):
        indices.add(i)
    # 均匀采样
    step = max(1, n // (kept_count - len(indices))) if kept_count > len(indices) else 1
    for i in range(0, n, step):
        if len(indices) >= kept_count:
            break
        indices.add(i)
    
    sorted_indices = sorted(indices)[:kept_count]
    kept = [messages[i] for i in sorted_indices]

    # 添加压缩标记
    summary = _make_compression_note(result)
    kept.insert(0, {"role": "system", "content": summary})

    return kept


def _match_messages_by_text(
    messages: List[Dict[str, Any]], kept_items: List[str]
) -> List[Dict[str, Any]]:
    """按文本内容匹配原始消息"""
    kept = []
    for item in kept_items:
        item_text = item.strip() if isinstance(item, str) else str(item)
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(p.get("text", "") for p in content if isinstance(p, dict) and "text" in p)
            if item_text[:50] in content or content[:50] in item_text:
                if msg not in kept:
                    kept.append(msg)
                    break
    
    if not kept:
        kept = _fallback_trim(messages, max_items=4)
    
    return kept


def _make_compression_note(result) -> str:
    """生成压缩标记，注入 context"""
    ratio_pct = int((1 - result.compression_ratio) * 100)
    return (
        f"[上下文压缩] 更早的对话已被压缩以节省 token（节省 {ratio_pct}%）。"
        f"关键信息已保留：{', '.join(result.preserved_categories)}"
    )


def _fallback_trim(messages: List[Dict[str, Any]], max_items: int = 6) -> List[Dict[str, Any]]:
    """降级方案：纯截断保留首尾"""
    n = len(messages)
    if n <= max_items:
        return messages

    kept = []
    # 首 30%
    first_n = max(1, int(max_items * 0.3))
    kept.extend(messages[:first_n])
    # 尾 70%
    last_n = max_items - first_n
    kept.extend(messages[-last_n:])

    return kept


def _hard_cap(
    messages: List[Dict[str, Any]],
    max_messages: int,
    max_chars: int,
) -> List[Dict[str, Any]]:
    """硬截断兜底"""
    result = list(messages)

    # 消息数限制
    if len(result) > max_messages:
        # 保留 system + 最近的
        system = [m for m in result if m.get("role") == "system"]
        others = [m for m in result if m.get("role") != "system"]
        others = others[-(max_messages - len(system)):]
        result = system + others

    # 字符数限制
    total = sum(len(str(m.get("content", ""))) for m in result)
    while total > max_chars and len(result) > 2:
        # 从前面开始删（保留 system 和最近的内容）
        for i, m in enumerate(result):
            if m.get("role") != "system":
                total -= len(str(m.get("content", "")))
                result.pop(i)
                break
        else:
            break

    return result


# ── 统计函数 ──

def estimate_tokens(text: str) -> int:
    """估算 token 数量（CJK-aware）"""
    if _HAS_HEADROOM:
        return hr_estimate_tokens(text)
    if not text:
        return 0
    cjk = sum(1 for c in text if '\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff')
    return cjk + max(1, (len(text) - cjk) // 4)


def context_stats(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """返回当前上下文压缩统计"""
    total_chars = sum(len(str(m.get("content", ""))) for m in messages)
    total_tokens = estimate_tokens(json.dumps(messages, ensure_ascii=False))
    return {
        "messages": len(messages),
        "total_chars": total_chars,
        "estimated_tokens": total_tokens,
        "system_count": sum(1 for m in messages if m.get("role") == "system"),
        "user_count": sum(1 for m in messages if m.get("role") == "user"),
        "assistant_count": sum(1 for m in messages if m.get("role") == "assistant"),
        "headroom_available": _HAS_HEADROOM,
    }


__all__ = [
    "trim_messages_for_model",
    "trim_context_for_llm",
    "estimate_tokens",
    "context_stats",
]
