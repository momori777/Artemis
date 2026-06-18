from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from pathlib import Path

# ── Headroom SmartCrusher + CCR ──────────────────────────────
HEADROOM_MODULE = Path(__file__).parent.parent.parent.parent / "headroom"
if str(HEADROOM_MODULE.parent) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(HEADROOM_MODULE.parent))
from skills.headroom import SmartCrusher, CCRStore, estimate_tokens


MAX_MODEL_CONTEXT_MESSAGES = 24
MAX_MODEL_CONTEXT_CHARS = 40_000

# 从 config.yaml 读取 headroom 配置（默认值）
_CCR_STORE: CCRStore | None = None
_CRUSHER: SmartCrusher | None = None


def _load_headroom_config() -> dict:
    """从 config.yaml 加载 headroom 配置（简易 YAML 解析）"""
    import os
    config_path = Path(os.environ.get(
        "AI_GIRLFRIEND_ROOT",
        str(Path(__file__).parent.parent.parent.parent),
    )) / "config.yaml"
    config_raw = ""
    if config_path.exists():
        config_raw = config_path.read_text(encoding="utf-8")

    cfg = {}
    ccr_cfg = {}
    in_ccr_section = False
    in_sc_section = False
    for line in config_raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("smart_crusher:"):
            in_sc_section = True
            in_ccr_section = False
            continue
        elif stripped.startswith("ccr:"):
            in_ccr_section = True
            in_sc_section = False
            continue
        elif stripped and not stripped.startswith("#") and not stripped.startswith("-"):
            if in_sc_section and ":" in stripped:
                key, val = stripped.split(":", 1)
                key = key.strip()
                val = val.strip().split("#")[0].strip()
                try:
                    cfg[key] = int(val)
                except ValueError:
                    try:
                        cfg[key] = float(val)
                    except ValueError:
                        cfg[key] = val.lower() == "true"
            elif in_ccr_section and ":" in stripped:
                key, val = stripped.split(":", 1)
                key = key.strip()
                val = val.strip().split("#")[0].strip()
                try:
                    ccr_cfg[key] = int(val)
                except ValueError:
                    try:
                        ccr_cfg[key] = float(val)
                    except ValueError:
                        ccr_cfg[key] = val.lower() == "true"
            else:
                in_sc_section = False
                in_ccr_section = False

    return {"crusher": cfg, "ccr": ccr_cfg}


def _get_crusher() -> SmartCrusher:
    global _CRUSHER
    if _CRUSHER is None:
        cfg = _load_headroom_config()["crusher"]
        _CRUSHER = SmartCrusher(cfg)
    return _CRUSHER


def _get_ccr() -> CCRStore:
    global _CCR_STORE
    if _CCR_STORE is None:
        ccr_cfg = _load_headroom_config()["ccr"]
        max_entries = ccr_cfg.get("max_entries", 500)
        ttl_seconds = ccr_cfg.get("ttl_seconds", 300)
        _CCR_STORE = CCRStore(max_entries=max_entries, ttl_seconds=ttl_seconds)
    return _CCR_STORE


def trim_messages_for_model(
    messages: list[dict[str, Any]],
    crush_enabled: bool = True,
    query: str = "",
) -> list[dict[str, Any]]:
    """
    保留最近上下文，用 SmartCrusher 压缩早期消息，用 CCR 缓存原文。

    流程：
    1. 截断到最近 MAX_MODEL_CONTEXT_MESSAGES 条
    2. 如果总字符数 > MAX_MODEL_CONTEXT_CHARS：
       a. 分离"保留区"（最近 N 条，不超过预算）和"压缩区"（更早的消息）
       b. 对"压缩区"用 SmartCrusher 压缩
       c. 将原文存入 CCR，压缩版替换原消息
    3. 返回处理后的消息列表
    """
    if not messages:
        return messages

    # 第一步：截断到最近 N 条消息
    recent = list(messages[-MAX_MODEL_CONTEXT_MESSAGES:])

    # 检查是否超过字符预算
    total_chars = _estimate_messages_chars(recent)
    if total_chars <= MAX_MODEL_CONTEXT_CHARS:
        return recent

    if not crush_enabled:
        # 压缩未启用时，粗暴截断
        while len(recent) > 1 and _estimate_messages_chars(recent) > MAX_MODEL_CONTEXT_CHARS:
            recent.pop(0)
        return recent

    # ── SmartCrusher 智能压缩 ──
    crusher = _get_crusher()
    ccr_store = _get_ccr()

    # 估算字符预算，计算每条消息的字符数
    msg_chars = []
    for msg in recent:
        chars = _estimate_message_chars(msg)
        msg_chars.append(chars)

    # 从后往前找"保留区"（不超过预算）
    # 保留最近消息直到剩余预算 < 一条消息的字符数
    budget_remaining = MAX_MODEL_CONTEXT_CHARS
    keep_start = 0
    for i in range(len(msg_chars) - 1, -1, -1):
        if budget_remaining >= msg_chars[i]:
            keep_start = i
            budget_remaining -= msg_chars[i]
        else:
            break

    # 分割：early = 需要压缩的消息, recent_safe = 最近保留的消息
    early_msgs = recent[:keep_start] if keep_start > 0 else []
    recent_safe = recent[keep_start:] if keep_start > 0 else recent

    if not early_msgs:
        return recent

    # 压缩"早期消息"
    crushed_msgs = _compress_early_messages(early_msgs, crusher, ccr_store, query)

    # 合并：压缩后的早期消息 + 保留的最近消息
    return crushed_msgs + recent_safe


def _compress_early_messages(
    early_msgs: list[dict[str, Any]],
    crusher: SmartCrusher,
    ccr_store: CCRStore,
    query: str,
) -> list[dict[str, Any]]:
    """
    压缩早期消息：将多条消息合并为一条压缩消息。

    策略：
    1. 将早期消息按角色分组（user / assistant），每条消息提取摘要
    2. 对摘要列表用 SmartCrusher 压缩（JSON 数组格式，SmartCrusher 擅长）
    3. 将原文存入 CCR 缓存
    """
    if not early_msgs:
        return early_msgs

    # 按角色构建结构化数据
    msg_list = []
    for i, msg in enumerate(early_msgs):
        role = msg.get("role", "user")
        content = str(msg.get("content", ""))
        if not content.strip():
            continue
        msg_list.append({
            "idx": i,
            "role": role,
            "content": content,
        })

    if not msg_list:
        return early_msgs

    # 将 msg_list 序列化为 JSON 用于 SmartCrusher 压缩
    json_text = json.dumps(msg_list, ensure_ascii=False, indent=2)
    total_tokens = estimate_tokens(json_text)

    if total_tokens < crusher.min_tokens_to_crush:
        return list(early_msgs)

    # SmartCrusher 对 JSON 数组做统计压缩
    # 对于早期消息，我们希望保留首尾（最近/最早的）+ 按 BM25 相关性保留
    crush_config = {
        "min_tokens_to_crush": crusher.min_tokens_to_crush,
        "max_items_after_crush": max(5, len(msg_list) // 3),  # 压缩到 1/3
        "first_fraction": 0.5,  # 保留更多开头（最早消息）
        "last_fraction": 0.3,   # 保留更多结尾（最近消息）
        "variance_threshold": 2.0,
        "preserve_change_points": True,
        "dedup_identical_items": True,
    }
    aggressive_crusher = SmartCrusher(crush_config)
    crush_result = aggressive_crusher.crush(json_text, query)

    # 将原文 JSON 存入 CCR
    ccr_store.put(crush_result.original_hash, crush_result.original_text, {
        "source": "context_trimming",
        "message_count": len(msg_list),
        "timestamp": datetime.now().isoformat(),
    })

    # 构建压缩后的消息
    cache_marker = (
        f"[{len(msg_list)} 条早期消息压缩为 {crush_result.items_kept} 条。"
        f"节省 {100 * (1 - crush_result.compression_ratio):.0f}% tokens。"
        f"取回原文: {crush_result.original_hash}]"
    )
    compressed_content = f"{cache_marker}\n\n{crush_result.compressed}"

    # 保留第一条消息的 role
    compressed_role = msg_list[0]["role"] if msg_list else "system"

    return [
        {
            "role": compressed_role,
            "content": compressed_content,
            "_compressed": True,
            "_original_hash": crush_result.original_hash,
            "_message_count": len(msg_list),
            "_items_kept": crush_result.items_kept,
        }
    ]


def retrieve_from_context_ccr(original_hash: str) -> tuple[bool, str]:
    """
    从 CCR 缓存取回被上下文压缩的消息原文。

    Args:
        original_hash: SmartCrusher 生成的缓存 hash

    Returns:
        (是否成功, 原文/错误信息)
    """
    ccr_store = _get_ccr()
    text = ccr_store.get(original_hash)
    if text:
        return True, text
    return False, "原文不在缓存中 (已过期或超出容量)"


def _estimate_messages_chars(messages: list[dict[str, Any]]) -> int:
    return sum(_estimate_message_chars(msg) for msg in messages)


def _estimate_message_chars(message: dict[str, Any]) -> int:
    """估算单条消息的字符数"""
    content = message.get("content", "")
    if isinstance(content, list):
        # 处理多模态内容（如 [type: text, text: "..."], [type: image, ...]）
        total = 0
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                total += len(str(item.get("text", "")))
            else:
                total += 50  # 每个非文本 item 估算 50 chars
        return total
    return len(str(content))
