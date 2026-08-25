# Headroom — Context Compression / 上下文压缩

## 中文

SmartCrusher + CCR (Compress-Cache-Retrieve) 上下文压缩模块，节省 token。
纯 Python 标准库实现，无外部依赖。

### 适用场景

- 大型工具输出（grep 结果、JSON 数组、文件列表）接近上下文上限
- 向有 token 限制的模型发送长上下文之前
- 需要保留关键内容、丢弃噪音

### 快速使用

```python
from skills.headroom import SmartCrusher, CCRStore

# 压缩 JSON 数组（保留最重要的条目）
crusher = SmartCrusher()
result = crusher.crush(large_json, query="relevant keywords")
# result.compressed        → 压缩后的 JSON 字符串
# result.items_kept / items_total → 保留比例
# result.compression_ratio → 如 0.3 表示节省 70% token
```

### SmartCrusher — 五维评分

保留依据：
1. **首尾条目** — 分页上下文 + 最新数据（30% 头部 + 15% 尾部）
2. **错误条目** — 100% 保留
3. **统计异常值** — 偏离均值 > 2 个标准差
4. **查询相关** — BM25 匹配用户查询
5. **变化点** — 数据中的显著转折

### CCR Store — 压缩-缓存-取回

```python
store = CCRStore(max_entries=1000, ttl_seconds=3600)
store.put(hash_key, original_text)          # 压缩时缓存原文
full_text = store.get(hash_key)             # LLM 需要细节时取回
```

### Token 估算

```python
from skills.headroom import estimate_tokens
tokens = estimate_tokens("some text — CJK-aware counting")
```

### 集成说明

- 本模块已被 `skills/shared/context_trimming.py` 导入（SmartCrusher 层）
- CCR 后台 worker 在 `skills/sakura/app/agent/memory_curator.py`，写入 Qdrant
- 角色扮演上下文裁剪：context_trimming 模块用 24msg/40K 字符上限包装 SmartCrusher
- 详见 `PROXY.md` 与 `SKILL.md`

## English

SmartCrusher + CCR (Compress-Cache-Retrieve) context compression module for token savings.
Pure Python stdlib — no external dependencies.

### When to Use

- Large tool output (grep results, JSON arrays, file listings) approaching context limit
- Before sending a long context to a model with token cap
- Need to preserve essential items while dropping noise

### Quick Start

```python
from skills.headroom import SmartCrusher, CCRStore

# Compress a JSON array (keep most important items)
crusher = SmartCrusher()
result = crusher.crush(large_json, query="relevant keywords")
# result.compressed  → compressed JSON string
# result.items_kept / items_total → retention ratio
# result.compression_ratio → e.g. 0.3 means 70% tokens saved
```

### SmartCrusher — 5-Dimensional Scoring

Keeps items by:
1. **First/Last items** — pagination context + latest data (30% head + 15% tail)
2. **Error items** — 100% preserved
3. **Statistical outliers** — > 2 std from mean
4. **Query-relevant** — BM25 match against user query
5. **Change points** — significant transitions in data

### CCR Store — Compress-Cache-Retrieve

```python
store = CCRStore(max_entries=1000, ttl_seconds=3600)
store.put(hash_key, original_text)          # cache original when crushing
full_text = store.get(hash_key)             # retrieve if LLM needs more detail
```

### Token Estimation

```python
from skills.headroom import estimate_tokens
tokens = estimate_tokens("some text — CJK-aware counting")
```

### Integration Notes

- Imported by `skills/shared/context_trimming.py` (SmartCrusher layer)
- CCR background worker in `skills/sakura/app/agent/memory_curator.py` writes to Qdrant
- Roleplay context trimming: context_trimming wraps SmartCrusher with 24msg/40K char cap
- See `PROXY.md` and `SKILL.md` for details
