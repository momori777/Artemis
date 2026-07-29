"""
Context Trimming — sakura app 层 re-export。

实际实现在 skills.shared.context_trimming，这里做透明转发，
保持 app.llm.context_trimming 的导入路径兼容性。

支持 API:
  - trim_messages_for_model(messages, crush_enabled=True/False, query=...)
  - retrieve_from_context_ccr(hash) → (ok, text)
  - estimate_tokens(text)
  - _estimate_messages_chars(messages)
  - context_stats(messages)
  - CRUSH_CONFIG (dict, 可运行时修改)
"""
from __future__ import annotations

import sys
import os

# 将 skills 目录加入 path
_SKILLS_PARENT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")
if _SKILLS_PARENT not in sys.path:
    sys.path.insert(0, _SKILLS_PARENT)

from skills.shared.context_trimming import (  # noqa: F401
    trim_messages_for_model,
    trim_context_for_llm,
    retrieve_from_context_ccr,
    estimate_tokens,
    _estimate_messages_chars,
    context_stats,
    CRUSH_CONFIG,
    MAX_MESSAGES,
    MAX_CHARS,
    RECENT_FULL_ROUNDS,
)

__all__ = [
    "trim_messages_for_model",
    "trim_context_for_llm",
    "retrieve_from_context_ccr",
    "estimate_tokens",
    "_estimate_messages_chars",
    "context_stats",
    "CRUSH_CONFIG",
    "MAX_MESSAGES",
    "MAX_CHARS",
    "RECENT_FULL_ROUNDS",
]
