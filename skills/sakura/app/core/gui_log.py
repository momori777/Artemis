from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


GUI_LOG_SCOPE_PROGRAM = "program"
GUI_LOG_SCOPE_TTS = "tts"
GUI_LOG_LEVEL_INFO = "info"
GUI_LOG_LEVEL_WARNING = "warning"
GUI_LOG_LEVEL_ERROR = "error"
DEFAULT_GUI_LOG_SCOPE_LIMIT = 200

_SENSITIVE_KEY_MARKERS = ("api_key", "authorization", "token", "secret", "password")
_PRIVATE_TEXT_KEY_MARKERS = (
    "body",
    "content",
    "input",
    "messages",
    "output",
    "payload",
    "prompt",
    "query",
    "reply",
    "response",
    "system_prompt",
    "text",
    "translation",
)
_ERROR_MARKERS = (
    "error",
    "exception",
    "fail",
    "failed",
    "timeout",
    "不可用",
    "失败",
    "异常",
    "错误",
    "超时",
    "无效",
)
_WARNING_MARKERS = (
    "fallback",
    "warning",
    "回退",
    "警告",
)
_PROGRAM_INFO_MESSAGES = {
    "应用初始化完成",
    "初始主窗口服务已创建",
    "TTS Provider 已创建",
    "后台启动服务已创建",
    "后台启动服务已注入窗口",
}
_PROGRAM_MESSAGE_LABELS = {
    ("API", "准备发送聊天补全请求"): "发送请求",
    ("API", "准备发送原生工具聊天补全请求"): "发送请求（带工具）",
    ("API", "模型原始文本返回"): "收到回复：文本",
    ("API", "原生工具模型返回"): "收到回复：工具调用",
}
_PROGRAM_TTS_MESSAGE_LABELS = {
    "发送 GPT-SoVITS 请求": "送入 TTS：GPT-SoVITS",
    "发送 Genie TTS 请求": "送入 TTS：Genie",
    "GPT-SoVITS 请求成功": "合成完成：GPT-SoVITS",
    "Genie 临时音频已写入": "合成完成：Genie",
    "音频请求失败": "TTS 合成失败",
    "开始播放音频": "开始播放",
    "音频播放完成": "播放完成",
    "已启动本地 GPT-SoVITS 服务": "准备：已拉起 GPT-SoVITS 服务",
    "本地 GPT-SoVITS 服务启动并探测成功": "准备：GPT-SoVITS 服务已就绪",
    "已启动本地 Genie TTS 服务": "准备：已拉起 Genie TTS 服务",
    "本地 Genie TTS 服务启动并探测成功": "准备：Genie TTS 服务已就绪",
    "服务探测成功": "准备：TTS 服务探测成功",
    "Genie 服务探测成功": "准备：Genie TTS 服务探测成功",
    "角色权重切换完成": "准备：TTS 角色权重切换完成",
}
_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
_HTTP_LINE_RE = re.compile(
    r'"(?P<method>[A-Z]+)\s+(?P<path>[^\s"]+)[^"]*"\s+(?P<status>\d{3})(?:\s+(?P<status_text>[A-Za-z]+))?'
)
_PROGRESS_RE = re.compile(r"(?P<percent>\d{1,3})%\|")
_PROGRESS_COUNT_RE = re.compile(r"(?P<current>\d+)\s*/\s*(?P<total>\d+)")
_PROGRESS_SPEED_RE = re.compile(r"(?P<speed>\d+(?:\.\d+)?)\s*it/s")
_T2S_EOS_RE = re.compile(r"Decoding EOS \[\s*(?P<start>\d+)\s*->\s*(?P<end>\d+)\s*\]")
# 语义 token 预测进度的原地合并键：相邻进度记录互相替换，只保留最新一条
_SEMANTIC_PROGRESS_MERGE_KEY = "semantic-token-progress"
# 记录各 provider 最近一次 EOS 的 token 数，用于丢弃 tqdm 收尾时重复的最终帧，
# 避免"预测完成（EOS）"行被一条停在中途百分比的旧进度覆盖
_LAST_EOS_TOKEN_COUNTS: dict[str, int] = {}
# 各 provider 最近一次语义 token 推理速度，供 EOS 完成行展示
_LAST_SPEED_BY_PROVIDER: dict[str, str] = {}
_SERVER_PROCESS_RE = re.compile(r"\[(\d+)\]")
_UVICORN_URL_RE = re.compile(r"https?://[^\s)]+")
_MAX_DETAIL_TEXT_CHARS = 180
_MAX_DETAIL_ITEMS = 8
_MAX_DETAIL_KEYS = 16
_TEXT_PREVIEW_MAX_CHARS = 60


@dataclass(frozen=True)
class GuiLogRecord:
    """展示到 GUI 的精简运行日志记录。"""

    record_id: int
    timestamp: str
    scope: str
    level: str
    category: str
    message: str
    detail: str = ""
    # 合成/播放相关记录附带的文本内容预览，仅用于界面展示
    text_preview: str = ""
    # 非空时，同 scope 相邻的同 merge_key 记录会原地替换（用于推理进度刷新）
    merge_key: str = ""


class GuiLogBuffer:
    """线程安全的内存环形日志缓冲；只保留本次会话。"""

    def __init__(self, *, max_records_per_scope: int = DEFAULT_GUI_LOG_SCOPE_LIMIT) -> None:
        self.max_records_per_scope = max(1, int(max_records_per_scope))
        self._records: dict[str, list[GuiLogRecord]] = {
            GUI_LOG_SCOPE_PROGRAM: [],
            GUI_LOG_SCOPE_TTS: [],
        }
        self._next_id = 1
        self._lock = threading.Lock()

    def append(
        self,
        *,
        timestamp: str,
        scope: str,
        level: str,
        category: str,
        message: str,
        detail: str = "",
        text_preview: str = "",
        merge_key: str = "",
    ) -> GuiLogRecord:
        normalized_scope = scope if scope in self._records else GUI_LOG_SCOPE_PROGRAM
        with self._lock:
            record = GuiLogRecord(
                record_id=self._next_id,
                timestamp=timestamp,
                scope=normalized_scope,
                level=level,
                category=category,
                message=message,
                detail=detail,
                text_preview=text_preview,
                merge_key=merge_key,
            )
            self._next_id += 1
            scope_records = self._records[normalized_scope]
            # 进度类记录原地替换上一条，避免高频刷新挤掉环形缓冲里的其他日志
            if (
                merge_key
                and scope_records
                and scope_records[-1].merge_key == merge_key
            ):
                scope_records[-1] = record
            else:
                scope_records.append(record)
            if len(scope_records) > self.max_records_per_scope:
                del scope_records[: len(scope_records) - self.max_records_per_scope]
            return record

    def snapshot(
        self,
        *,
        scope: str | None = None,
        after_id: int = 0,
    ) -> list[GuiLogRecord]:
        with self._lock:
            if scope is not None:
                records = list(self._records.get(scope, []))
            else:
                records = [
                    record
                    for scope_records in self._records.values()
                    for record in scope_records
                ]
            return sorted(
                (record for record in records if record.record_id > after_id),
                key=lambda record: record.record_id,
            )

    def clear(self, *, scope: str | None = None) -> None:
        with self._lock:
            if scope is None:
                for scope_records in self._records.values():
                    scope_records.clear()
                return
            self._records.get(scope, []).clear()


_GLOBAL_GUI_LOG_BUFFER = GuiLogBuffer()


def get_gui_log_buffer() -> GuiLogBuffer:
    return _GLOBAL_GUI_LOG_BUFFER


def clear_gui_logs() -> None:
    _GLOBAL_GUI_LOG_BUFFER.clear()
    _LAST_EOS_TOKEN_COUNTS.clear()
    _LAST_SPEED_BY_PROVIDER.clear()


def record_debug_log_for_gui(
    category: str,
    message: str,
    data: Any | None = None,
    *,
    timestamp: str | None = None,
) -> GuiLogRecord | None:
    """把内部 debug_log 转为适合界面查看的精简日志。"""

    category_text = str(category).strip() or "Runtime"
    message_text = str(message).strip()
    if not message_text:
        return None

    scope = _scope_for(category_text, message_text)
    level = _level_for(message_text, data)
    if not _should_record(scope, category_text, message_text, level):
        return None

    detail = _format_detail(data)
    return _GLOBAL_GUI_LOG_BUFFER.append(
        timestamp=timestamp or _now_iso(),
        scope=scope,
        level=level,
        category=category_text,
        message=_compact_debug_message(category_text, message_text, data),
        detail=detail,
        text_preview=_tts_text_preview(category_text, data),
    )


def record_tts_service_output(
    provider: str,
    line: str,
    *,
    timestamp: str | None = None,
) -> GuiLogRecord | None:
    """记录本地 TTS 服务原生输出的精简摘要。"""

    raw_line = _normalize_service_line(line)
    if not raw_line:
        return None
    provider_text = str(provider).strip() or "TTS"
    message, merge_key = _compact_tts_service_message(raw_line, provider_text)
    if not message:
        return None
    return _GLOBAL_GUI_LOG_BUFFER.append(
        timestamp=timestamp or _now_iso(),
        scope=GUI_LOG_SCOPE_TTS,
        level=_level_for(raw_line, None),
        category=f"{provider_text} 服务",
        message=message,
        detail="",
        merge_key=merge_key,
    )


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _scope_for(category: str, message: str) -> str:
    _ = message
    return GUI_LOG_SCOPE_PROGRAM


def _level_for(message: str, data: Any | None) -> str:
    message_haystack = message.lower()
    if any(marker.lower() in message_haystack for marker in _ERROR_MARKERS):
        return GUI_LOG_LEVEL_ERROR
    if _data_has_error_value(data):
        return GUI_LOG_LEVEL_ERROR
    if any(marker.lower() in message_haystack for marker in _WARNING_MARKERS):
        return GUI_LOG_LEVEL_WARNING
    return GUI_LOG_LEVEL_INFO


def _safe_data_for_level(data: Any | None) -> Any:
    if isinstance(data, dict):
        return {
            str(key): value
            for key, value in data.items()
            if not _is_sensitive_key(str(key).lower())
        }
    return data


def _data_has_error_value(data: Any | None) -> bool:
    if not isinstance(data, dict):
        return False
    for key, value in data.items():
        normalized_key = str(key).lower()
        if normalized_key not in {"error", "exception", "error_body"}:
            continue
        if value in (None, "", False, 0):
            continue
        return True
    return False


def _should_record(scope: str, category: str, message: str, level: str) -> bool:
    if level == GUI_LOG_LEVEL_ERROR:
        return True
    if category.lower() == "tts":
        return message in _PROGRAM_TTS_MESSAGE_LABELS
    if level == GUI_LOG_LEVEL_WARNING:
        return True
    return message in _PROGRAM_INFO_MESSAGES or (category, message) in _PROGRAM_MESSAGE_LABELS


def _compact_debug_message(category: str, message: str, data: Any | None = None) -> str:
    if category.lower() == "tts":
        label = _PROGRAM_TTS_MESSAGE_LABELS.get(message)
        if label:
            return label
    label = _PROGRAM_MESSAGE_LABELS.get((category, message))
    if label:
        if message == "原生工具模型返回":
            tool_calls = data.get("tool_calls") if isinstance(data, dict) else None
            if isinstance(tool_calls, list):
                if tool_calls:
                    tool_names = _extract_tool_names(data)
                    return f"收到回复：工具调用：{tool_names}" if tool_names else "收到回复：工具调用"
                else:
                    # tool_calls 为空列表说明模型实际只返回了文本内容
                    return "收到回复：文本"
        return label
    return _compact_message(message)


def _extract_tool_names(data: Any | None) -> str:
    """从 tool_calls 数据中提取工具函数名，用于日志展示。

    支持内部自定义格式（call["name"]）和 OpenAI 标准格式（call["function"]["name"]）。
    """
    if not isinstance(data, dict):
        return ""
    tool_calls = data.get("tool_calls")
    if not isinstance(tool_calls, list) or not tool_calls:
        return ""
    names: list[str] = []
    for call in tool_calls:
        if not isinstance(call, dict):
            continue
        # 内部格式：{"name": "tool_name", "type": "tool_call", ...}
        # OpenAI 格式：{"function": {"name": "tool_name"}, ...}
        name = call.get("name") or (call.get("function") or {}).get("name")
        if name:
            names.append(str(name))
    if not names:
        return ""
    if len(names) > 3:
        return "、".join(names[:3]) + f" 等 {len(names)} 个"
    return "、".join(names)


def _compact_message(message: str) -> str:
    return _truncate(message.replace("\r", " ").replace("\n", " "), 140)


def _normalize_service_line(line: str) -> str:
    text = _ANSI_RE.sub("", str(line))
    if "\r" in text:
        # 一段里混有多次 \r 刷新时（按行读取的退路），只保留最新一帧
        segments = [segment for segment in text.split("\r") if segment.strip()]
        text = segments[-1] if segments else ""
    text = re.sub(r"\s+", " ", text.strip())
    return text


def _compact_tts_service_message(line: str, provider: str) -> tuple[str, str]:
    """压缩服务输出行，返回 (消息, 合并键)；消息为空表示丢弃该行。"""
    http_match = _HTTP_LINE_RE.search(line)
    if http_match is not None:
        method = http_match.group("method")
        path = http_match.group("path")
        status = http_match.group("status")
        status_text = http_match.group("status_text") or ""
        return f"HTTP {method} {path} -> {status} {status_text}".strip(), ""

    if "合成音频" in line:
        return "开始合成音频", ""
    if "实际输入的目标文本" in line or "目标文本" in line:
        return _summarize_service_text_line(line), ""
    if "Decoding EOS" in line:
        # T2S 语义 token 预测命中 EOS；记录 token 数以便丢弃 tqdm 收尾重复帧
        eos_match = _T2S_EOS_RE.search(line)
        if eos_match is not None:
            start = int(eos_match.group("start"))
            end = int(eos_match.group("end"))
            _LAST_EOS_TOKEN_COUNTS[provider] = end
            speed = _LAST_SPEED_BY_PROVIDER.pop(provider, "")
            speed_part = f"，{speed} it/s" if speed else ""
            return (
                f"语义 token 预测完成：EOS（{start} → {end}{speed_part}）",
                _SEMANTIC_PROGRESS_MERGE_KEY,
            )
        return "语义 token 预测完成（EOS）", _SEMANTIC_PROGRESS_MERGE_KEY
    if "Set seed to" in line or "分桶处理模式已开启" in line:
        return "", ""  # 内部初始化操作，不展示

    progress_message = _semantic_progress_message(line, provider)
    if progress_message is not None:
        return progress_message, _SEMANTIC_PROGRESS_MERGE_KEY

    if line.startswith("INFO:"):
        content = line.removeprefix("INFO:").strip()
        return _compact_message(_translate_info_line(content)), ""
    if line.startswith(("ERROR:", "WARNING:")):
        return _compact_message(line), ""
    if any(marker in line.lower() for marker in ("error", "warning", "started", "server", "http")):
        return _compact_message(line), ""
    return "", ""


def _semantic_progress_message(line: str, provider: str) -> str | None:
    """解析 tqdm 进度行为语义 token 预测进度；返回 None 表示不是进度行，
    返回空串表示是进度行但应丢弃（EOS 后的收尾重复帧）。"""
    percent_match = _PROGRESS_RE.search(line)
    count_match = _PROGRESS_COUNT_RE.search(line)
    if percent_match is None and (count_match is None or "it/s" not in line):
        return None

    current = int(count_match.group("current")) if count_match else None
    total = int(count_match.group("total")) if count_match else None
    if current is not None and _LAST_EOS_TOKEN_COUNTS.get(provider) == current:
        # EOS 已经展示完成行，丢弃 tqdm 关闭时停在中途百分比的最终帧
        _LAST_EOS_TOKEN_COUNTS.pop(provider, None)
        return ""

    speed_match = _PROGRESS_SPEED_RE.search(line)
    extras: list[str] = []
    if current is not None and total is not None:
        extras.append(f"{current}/{total}")
    if speed_match is not None:
        speed_str = speed_match.group("speed")
        _LAST_SPEED_BY_PROVIDER[provider] = speed_str  # 缓存速度，供 EOS 完成行展示
        extras.append(f"{speed_str} it/s")
    extras_text = f"（{'，'.join(extras)}）" if extras else ""

    if percent_match is not None:
        percent = min(100, int(percent_match.group("percent")))
        return f"语义 token 预测 {percent}%{extras_text}"
    return f"语义 token 预测{extras_text}"


def _summarize_service_text_line(line: str) -> str:
    text = line
    for separator in (":", "："):
        if separator in text:
            text = text.split(separator, 1)[1]
            break
    text = text.strip(" []'\"")
    if not text:
        return "收到合成文本"
    return f"收到合成文本（{len(text)} 字）"


def _translate_info_line(line: str) -> str:
    """将 uvicorn/服务常见英文 INFO 行翻译为中文，无匹配时原样返回。"""
    lower = line.lower()
    if "started server process" in lower:
        m = _SERVER_PROCESS_RE.search(line)
        pid = m.group(1) if m else ""
        return f"已启动服务进程 [{pid}]" if pid else "已启动服务进程"
    if "waiting for application startup" in lower:
        return "等待应用启动…"
    if "application startup complete" in lower:
        return "应用启动完成"
    if "uvicorn running on" in lower:
        m = _UVICORN_URL_RE.search(line)
        url = m.group(0) if m else ""
        return f"服务已就绪：{url}" if url else "服务已就绪"
    if "waiting for application shutdown" in lower:
        return "等待应用关闭…"
    if "application shutdown complete" in lower:
        return "应用关闭完成"
    if "finished server process" in lower:
        return "服务进程已结束"
    if "shutting down" in lower:
        return "服务正在关闭"
    return line


def _tts_text_preview(category: str, data: Any | None) -> str:
    """TTS 合成/播放记录提取文本内容预览，供界面灰字直接展示。

    仅 GUI 内存日志使用；文件日志与 detail 字段仍按既有规则脱敏。
    """
    if category.lower() != "tts" or not isinstance(data, dict):
        return ""
    text = data.get("text")
    if not isinstance(text, str):
        return ""
    text = " ".join(text.split())
    if len(text) > _TEXT_PREVIEW_MAX_CHARS:
        return f"{text[:_TEXT_PREVIEW_MAX_CHARS]}…"
    return text


def _format_detail(data: Any | None) -> str:
    if data is None:
        return ""
    safe = _sanitize_detail(data, private_context=False)
    return json.dumps(safe, ensure_ascii=False, default=str)


def _sanitize_detail(value: Any, *, private_context: bool) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        items = list(value.items())
        for key, item_value in items[:_MAX_DETAIL_KEYS]:
            key_text = str(key)
            normalized_key = key_text.lower()
            if _is_sensitive_key(normalized_key):
                sanitized[key_text] = "<redacted>"
                continue
            next_private_context = private_context or _is_private_text_key(normalized_key)
            sanitized[key_text] = _sanitize_detail(
                item_value,
                private_context=next_private_context,
            )
        if len(items) > _MAX_DETAIL_KEYS:
            sanitized["omitted_keys"] = len(items) - _MAX_DETAIL_KEYS
        return sanitized
    if isinstance(value, list):
        if private_context:
            return {"type": "list", "items": len(value)}
        items = [
            _sanitize_detail(item, private_context=private_context)
            for item in value[:_MAX_DETAIL_ITEMS]
        ]
        if len(value) > _MAX_DETAIL_ITEMS:
            items.append({"omitted_items": len(value) - _MAX_DETAIL_ITEMS})
        return items
    if isinstance(value, tuple):
        return _sanitize_detail(list(value), private_context=private_context)
    if isinstance(value, bytes):
        return {"type": "bytes", "bytes": len(value)}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, str):
        if value.startswith("data:image/"):
            return {"type": "image_data_url", "chars": len(value)}
        if private_context:
            return {"type": "text", "chars": len(value)}
        return _truncate(value, _MAX_DETAIL_TEXT_CHARS)
    return value


def _is_sensitive_key(normalized_key: str) -> bool:
    return any(marker in normalized_key for marker in _SENSITIVE_KEY_MARKERS)


def _is_private_text_key(normalized_key: str) -> bool:
    return any(marker in normalized_key for marker in _PRIVATE_TEXT_KEY_MARKERS)


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}...<truncated {len(text) - max_chars} chars>"
