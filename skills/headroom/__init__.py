"""
Headroom — 上下文压缩层 (SmartCrusher + CCR)

基于 headroom.ai 论文/实现，适配 AI Girlfriend 项目的轻量级 Python 版本。

核心组件：
  - SmartCrusher: JSON 数组统计压缩 (70-90% token 节省)
  - CCR (Compress-Cache-Retrieve): 可逆压缩缓存
  - ContentRouter: 自动检测内容类型并路由

用法：
  from skills.headroom import SmartCrusher, CCRStore

  # SmartCrusher — 压缩工具输出/搜索结果的 JSON 数组
  crusher = SmartCrusher()
  result = crusher.crush(json_data, query="用户查询关键词")
  # result.compressed 是压缩后的内容
  # result.original_hash 可用于 CCR 取回

  # CCR — 压缩时自动缓存原文，按需取回
  store = CCRStore()
  store.put(original_text, result.original_hash)
  # LLM 觉得不够时可以：store.get(hash) 取回原文
"""

import hashlib
import json
import math
import re
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


# ── Data Classes ───────────────────────────────────────────────────

@dataclass
class CrushResult:
    """SmartCrusher 压缩结果"""
    compressed: str
    original_hash: str
    original_text: str
    items_kept: int
    items_total: int
    tokens_before: int
    tokens_after: int
    compression_ratio: float
    preserved_categories: List[str] = field(default_factory=list)


@dataclass
class CCRStore:
    """Compress-Cache-Retrieve 缓存存储 (LRU)"""
    max_entries: int = 1000
    ttl_seconds: int = 3600  # 默认 1 小时 TTL
    _cache: Dict[str, dict] = field(default_factory=dict)
    _access_order: List[str] = field(default_factory=list)  # LRU 排序
    _created_at: Dict[str, float] = field(default_factory=dict)  # 时间戳

    def put(self, key: str, value: str, meta: Optional[dict] = None) -> None:
        """缓存原文"""
        self._evict_if_needed()
        self._cache[key] = {
            "value": value,
            "meta": meta or {},
        }
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        self._created_at[key] = datetime.now().timestamp()

    def get(self, key: str) -> Optional[str]:
        """取回原文"""
        entry = self._cache.get(key)
        if not entry:
            return None
        # 检查 TTL
        if self._created_at.get(key, 0) + self.ttl_seconds < datetime.now().timestamp():
            self.remove(key)
            return None
        # LRU 更新
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        return entry["value"]

    def remove(self, key: str) -> None:
        """删除缓存项"""
        self._cache.pop(key, None)
        self._access_order = [k for k in self._access_order if k != key]
        self._created_at.pop(key, None)

    def _evict_if_needed(self) -> None:
        """LRU 淘汰"""
        while len(self._cache) >= self.max_entries and self._access_order:
            oldest = self._access_order.pop(0)
            self._cache.pop(oldest, None)
            self._created_at.pop(oldest, None)

    def search(self, key: str, query: str) -> Optional[str]:
        """BM25 风格搜索缓存内原文（简化版：关键词匹配）"""
        text = self.get(key)
        if not text:
            return None
        query_terms = set(query.lower().split())
        text_words = set(text.lower().split())
        if query_terms & text_words:  # 有交集就返回
            return text
        return None

    def stats(self) -> dict:
        """返回缓存统计"""
        return {
            "size": len(self._cache),
            "max": self.max_entries,
            "ttl_seconds": self.ttl_seconds,
        }

    def clear(self) -> None:
        self._cache.clear()
        self._access_order.clear()
        self._created_at.clear()


# ── Token Estimation ──────────────────────────────────────────────

def estimate_tokens(text: str) -> int:
    """估算 token 数（粗略：1 token ≈ 4 chars for Chinese/UTF-8）"""
    if not text:
        return 0
    # 中文/日文等 CJK 字符 1 char ≈ 1 token，英文 1 token ≈ 4 chars
    cjk_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff')
    non_cjk = len(text) - cjk_count
    return cjk_count + max(1, non_cjk // 4)


# ── SmartCrusher — JSON 数组统计压缩 ──────────────────────────────

class SmartCrusher:
    """
    JSON 数组统计压缩器。
    
    五维评分保留机制：
    1. 首/尾项 — 分页上下文和最新数据
    2. 错误项 — 100% 保留
    3. 异常值 — 统计离群值 (> 2 std)
    4. 相关项 — BM25 匹配用户查询
    5. 变化点 — 数据中的显著过渡
    
    保留比例：30% 开头 + 15% 结尾 + 55% 按重要性
    """

    def __init__(self, config: Optional[dict] = None):
        cfg = config or {}
        self.min_tokens_to_crush = cfg.get("min_tokens_to_crush", 200)
        self.max_items_after_crush = cfg.get("max_items_after_crush", 15)
        self.first_fraction = cfg.get("first_fraction", 0.3)
        self.last_fraction = cfg.get("last_fraction", 0.15)
        self.variance_threshold = cfg.get("variance_threshold", 2.0)
        self.preserve_change_points = cfg.get("preserve_change_points", True)
        self.uniqueness_threshold = cfg.get("uniqueness_threshold", 0.1)
        self.similarity_threshold = cfg.get("similarity_threshold", 0.8)
        self.dedup_identical = cfg.get("dedup_identical_items", True)
        self.use_feedback_hints = cfg.get("use_feedback_hints", True)

    def crush(self, data: Any, query: str = "") -> CrushResult:
        """
        压缩 JSON 数据（可以是 dict、list 或 JSON 字符串）。
        
        Returns CrushResult with compressed output and metadata.
        """
        # 解析输入
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
            except json.JSONDecodeError:
                return self._compress_plain(data, query)
        else:
            parsed = data

        # 提取数组
        target_array = self._extract_array(parsed)
        if not target_array:
            return self._compress_plain(str(data), query)

        # 如果太小不压缩
        text = json.dumps(parsed, ensure_ascii=False)
        if estimate_tokens(text) < self.min_tokens_to_crush:
            return CrushResult(
                compressed=text,
                original_hash=hashlib.md5(text.encode()).hexdigest()[:12],
                original_text=text,
                items_kept=len(target_array),
                items_total=len(target_array),
                tokens_before=estimate_tokens(text),
                tokens_after=estimate_tokens(text),
                compression_ratio=1.0,
            )

        # 压缩
        compressed, metrics = self._crush_array(target_array, query)
        
        # 重建 JSON
        compressed_text = json.dumps(compressed, ensure_ascii=False, indent=2)
        original_text = json.dumps(parsed, ensure_ascii=False, indent=2)
        
        tokens_before = estimate_tokens(original_text)
        tokens_after = estimate_tokens(compressed_text)

        # 生成缓存标记
        original_hash = hashlib.md5(original_text.encode()).hexdigest()[:12]
        cache_marker = (
            f"[{len(target_array)} items compressed to {len(compressed)}. "
            f"Retrieve original: {original_hash}]"
        )
        compressed_text = cache_marker + "\n\n" + compressed_text

        preserved = metrics.get("preserved_categories", [])
        if not preserved:
            preserved = ["sampling"]

        return CrushResult(
            compressed=compressed_text,
            original_hash=original_hash,
            original_text=original_text,
            items_kept=len(compressed),
            items_total=len(target_array),
            tokens_before=tokens_before,
            tokens_after=tokens_after + estimate_tokens(cache_marker),
            compression_ratio=tokens_after / max(1, tokens_before),
            preserved_categories=preserved,
        )

    def _extract_array(self, data: Any) -> Optional[list]:
        """从 dict 或 list 中提取目标数组"""
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # 尝试找第一个值为 list 的 value
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    return value
        return None

    def _crush_array(self, items: list, query: str) -> Tuple[list, dict]:
        """
        核心压缩逻辑。
        Returns: (compressed_items, metrics)
        """
        n = len(items)
        if n <= 2:
            return items, {"preserved_categories": ["all"], "reason": "too small"}

        metrics = {"preserved_categories": [], "reason": "compression"}
        kept_indices = set()

        # ── 1. 首尾项 ──
        first_n = max(1, int(n * self.first_fraction))
        last_n = max(1, int(n * self.last_fraction))
        kept_indices.update(range(0, first_n))
        kept_indices.update(range(n - last_n, n))
        metrics["preserved_categories"].append("first_tail")

        # ── 2. 错误项 (100% 保留) ──
        error_indices = self._find_error_items(items)
        kept_indices.update(error_indices)
        if error_indices:
            metrics["preserved_categories"].append("errors")

        # ── 3. 异常值 (统计离群值) ──
        anomaly_indices = self._find_anomalies(items)
        kept_indices.update(anomaly_indices)
        if anomaly_indices:
            metrics["preserved_categories"].append("anomalies")

        # ── 4. 相关项 (BM25 匹配查询) ──
        if query:
            relevant_indices = self._find_relevant_items(items, query)
            kept_indices.update(relevant_indices)
            if relevant_indices:
                metrics["preserved_categories"].append("relevant")

        # ── 5. 变化点 ──
        if self.preserve_change_points:
            change_indices = self._find_change_points(items)
            kept_indices.update(change_indices)
            if change_indices:
                metrics["preserved_categories"].append("change_points")

        # ── 6. 去重 ──
        if self.dedup_identical:
            seen = set()
            deduped_indices = set()
            for i in kept_indices:
                sig = self._item_signature(items[i])
                if sig not in seen:
                    seen.add(sig)
                    deduped_indices.add(i)
            kept_indices = deduped_indices
            if len(seen) < len(kept_indices) + 1:
                metrics["preserved_categories"].append("deduped")

        # ── 7. 采样补充 (如果保留数量 < max) ──
        remaining = [i for i in range(n) if i not in kept_indices]
        budget = max(self.max_items_after_crush, len(kept_indices))
        if remaining and len(kept_indices) < budget:
            # 均匀采样补充
            sample_step = max(1, len(remaining) // (budget - len(kept_indices)))
            for i in remaining[::sample_step]:
                kept_indices.add(i)
                if len(kept_indices) >= budget:
                    break
            metrics["preserved_categories"].append("sampling")

        # 构建压缩结果
        sorted_indices = sorted(kept_indices)
        compressed = [items[i] for i in sorted_indices]
        metrics["indices_kept"] = sorted_indices
        metrics["preserved_categories"] = list(set(metrics["preserved_categories"]))

        return compressed, metrics

    def _find_error_items(self, items: list) -> set:
        """找错误项：包含 error/failed/exception/fatal 等关键字"""
        error_keywords = {"error", "failed", "exception", "fatal", "timeout", "refused"}
        indices = set()
        for i, item in enumerate(items):
            text = self._item_text(item).lower()
            if any(kw in text for kw in error_keywords):
                indices.add(i)
        return indices

    def _find_anomalies(self, items: list) -> set:
        """找统计异常值：数值字段的离群值"""
        indices = set()
        numeric_values = []
        for i, item in enumerate(items):
            nums = self._extract_numbers(item)
            if nums:
                numeric_values.append((i, nums))

        if len(numeric_values) < 3:
            return indices

        # 对每个数值字段计算均值和标准差
        max_fields = min(3, len(numeric_values[0][1]))
        for f in range(max_fields):
            field_vals = [vals[f] for _, vals in numeric_values]
            if not field_vals:
                continue
            mean = sum(field_vals) / len(field_vals)
            variance = sum((v - mean) ** 2 for v in field_vals) / len(field_vals)
            std = math.sqrt(variance) if variance > 0 else 0.001

            if std > 0:
                for idx, vals in numeric_values:
                    if abs(vals[f] - mean) > self.variance_threshold * std:
                        indices.add(idx)
                        break  # 每个 item 只计一次

        return indices

    def _find_relevant_items(self, items: list, query: str) -> set:
        """BM25 风格的相关性匹配"""
        indices = set()
        query_terms = self._tokenize(query)
        if not query_terms:
            return indices

        # 计算每个 item 的 BM25 分数
        scores = []
        doc_len = len(items)
        for i, item in enumerate(items):
            item_text = self._item_text(item)
            item_terms = set(self._tokenize(item_text))
            # 简单 BM25: TF * IDF
            score = 0
            for term in query_terms:
                tf = item_text.lower().count(term.lower())
                if tf > 0:
                    doc_freq = sum(1 for it in items if term.lower() in self._item_text(it).lower())
                    idf = math.log((doc_len - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
                    score += (tf * idf) / (tf + 0.5)  # 简化的 BM25
            scores.append((score, i))

        # 取 top K
        k = max(1, len(items) // 10)
        scores.sort(reverse=True, key=lambda x: x[0])
        for score, idx in scores[:k]:
            if score > 0:
                indices.add(idx)

        return indices

    def _find_change_points(self, items: list) -> set:
        """找数据中的显著变化点"""
        indices = set()
        if len(items) < 5:
            return indices

        # 检查连续项的显著差异
        numeric_seq = []
        for item in items:
            nums = self._extract_numbers(item)
            if nums:
                numeric_seq.append(nums[0])
            else:
                numeric_seq.append(None)

        valid = [(i, v) for i, v in enumerate(numeric_seq) if v is not None]
        if len(valid) < 5:
            return indices

        values = [v for _, v in valid]
        for i in range(1, len(values)):
            if values[i - 1] != 0 and abs(values[i] - values[i - 1]) / abs(values[i - 1]) > 0.5:
                indices.add(valid[i][0])

        return indices

    def _compress_plain(self, text: str, query: str) -> CrushResult:
        """非 JSON 数据的压缩：按行切分后用 SmartCrusher 的索引保留逻辑"""
        tokens = estimate_tokens(text)
        original_hash = hashlib.md5(text.encode()).hexdigest()[:12]
        
        if tokens < self.min_tokens_to_crush:
            return CrushResult(
                compressed=text,
                original_hash=original_hash,
                original_text=text,
                items_kept=1,
                items_total=1,
                tokens_before=tokens,
                tokens_after=tokens,
                compression_ratio=1.0,
            )
        
        # 按行切分，用索引保留逻辑
        lines = [l for l in text.split('\n') if l.strip()]
        n = len(lines)
        if n <= 2:
            return CrushResult(
                compressed=text,
                original_hash=original_hash,
                original_text=text,
                items_kept=n,
                items_total=n,
                tokens_before=tokens,
                tokens_after=tokens,
                compression_ratio=1.0,
            )
        
        # 复用 SmartCrusher 的索引逻辑
        _, metrics = self._crush_array(lines, query)
        
        compressed_lines = [lines[i] for i in sorted(metrics.get('indices_kept', set()))]
        compressed = '\n'.join(compressed_lines)
        tokens_after = estimate_tokens(compressed)
        preserved = metrics.get('preserved_categories', [])
        if not preserved:
            preserved = ['sampling']
        
        return CrushResult(
            compressed=compressed,
            original_hash=original_hash,
            original_text=text,
            items_kept=len(compressed_lines),
            items_total=n,
            tokens_before=tokens,
            tokens_after=tokens_after,
            compression_ratio=tokens_after / max(1, tokens),
            preserved_categories=preserved,
        )

    # ── Helpers ──

    def _item_text(self, item: Any) -> str:
        """将 item 转为文本"""
        if isinstance(item, str):
            return item
        if isinstance(item, (dict, list)):
            return json.dumps(item, ensure_ascii=False)
        return str(item)

    def _item_signature(self, item: Any) -> str:
        """item 的签名（用于去重）"""
        if isinstance(item, dict):
            # 忽略 id/timestamp 等变化字段，只签内容
            clean = {k: v for k, v in item.items() if k not in ('id', 'timestamp', 'date', 'time', '_id')}
            return json.dumps(clean, sort_keys=True, ensure_ascii=False)
        return str(item)

    def _extract_numbers(self, item: Any) -> List[float]:
        """从 item 中提取数字"""
        nums = []
        if isinstance(item, (int, float)):
            nums.append(float(item))
        elif isinstance(item, dict):
            for k, v in item.items():
                if isinstance(v, (int, float)):
                    nums.append(float(v))
        elif isinstance(item, list):
            for v in item:
                if isinstance(v, (int, float)):
                    nums.append(float(v))
        return nums

    def _tokenize(self, text: str) -> List[str]:
        """简易分词"""
        # 中文/英文混合分词
        text = text.lower().strip()
        # 英文单词
        words = re.findall(r'[a-zA-Z]+|\S', text)
        return [w for w in words if len(w) > 1]


# ── ContentRouter — 自动内容类型检测 ─────────────────────────────

class ContentRouter:
    """自动检测内容类型并路由到对应压缩器"""

    def __init__(self, crusher: Optional[SmartCrusher] = None):
        self.crusher = crusher or SmartCrusher()

    def classify(self, content: str) -> str:
        """检测内容类型"""
        content = content.strip()
        if not content:
            return "empty"

        # JSON 数组检测
        if content.lstrip().startswith('[') or content.lstrip().startswith('{'):
            try:
                parsed = json.loads(content)
                if isinstance(parsed, list):
                    return "json_array"
                if isinstance(parsed, dict):
                    # 检查是否有数组 value
                    for v in parsed.values():
                        if isinstance(v, list) and v:
                            return "json_array"
            except json.JSONDecodeError:
                pass

        # 日志检测
        log_patterns = [
            r'^\d{4}-\d{2}-\d{2}',  # 日期前缀
            r'\d{2}:\d{2}:\d{2}',   # 时间戳
            r'(INFO|WARN|ERROR|DEBUG|FATAL|TRACE)',  # 日志级别
            r'(\[.*?\]|\(.*?\))',    # 日志标签
        ]
        if any(re.search(p, content, re.MULTILINE) for p in log_patterns):
            return "log"

        # Diff 检测
        if content.startswith('diff ') or '---' in content and '+++' in content:
            return "diff"

        # Code 检测（简易）
        code_patterns = [r'\b(def|class|import|function|const|let|var|fn|pub)\b']
        if len(re.findall(code_patterns[0], content)) > 3:
            return "code"

        return "text"

    def compress(self, content: str, query: str = "") -> CrushResult:
        """路由压缩"""
        content_type = self.classify(content)
        if content_type == "empty":
            return CrushResult(
                compressed="", original_hash="", original_text="",
                items_kept=0, items_total=0, tokens_before=0, tokens_after=0,
                compression_ratio=1.0,
            )
        
        # JSON 数组走 SmartCrusher
        if content_type in ("json_array", "text"):
            return self.crusher.crush(content, query)
        
        # 其他类型走 plain compress
        return self.crusher._compress_plain(content, query)


# ── Public API ────────────────────────────────────────────────────

def compress_json(data: Any, query: str = "", config: Optional[dict] = None) -> CrushResult:
    """快捷函数：压缩 JSON 数据"""
    crusher = SmartCrusher(config)
    return crusher.crush(data, query)


def compress_text(text: str, query: str = "", config: Optional[dict] = None) -> CrushResult:
    """快捷函数：压缩文本"""
    router = ContentRouter(SmartCrusher(config))
    return router.compress(text, query)


def estimate_tokens(text: str) -> int:
    """估算 token 数"""
    return _estimate_tokens_internal(text)


def _estimate_tokens_internal(text: str) -> int:
    if not text:
        return 0
    cjk_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff')
    non_cjk = len(text) - cjk_count
    return cjk_count + max(1, non_cjk // 4)


__all__ = [
    "SmartCrusher",
    "CCRStore",
    "ContentRouter",
    "CrushResult",
    "compress_json",
    "compress_text",
    "estimate_tokens",
]
