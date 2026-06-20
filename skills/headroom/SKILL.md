---
name: headroom
description: SmartCrusher + CCR context compression — crunch large JSON arrays, tool outputs, and search results to save tokens. Use when context is bloated or approaching token limits.
license: MIT
homepage: https://github.com/chopratejas/headroom
---

# Headroom — Context Compression Layer

SmartCrusher + CCR (Compress-Cache-Retrieve) for token-saving context compression.
Portable Python module — no external dependencies beyond stdlib.

## When to Use

- Large tool output (grep results, JSON arrays, file listings) approaching context limit
- Before sending a long context to a model with token cap
- Need to preserve essential items while dropping noise

## Quick Start

```python
from skills.headroom import SmartCrusher, CCRStore

# Compress a JSON array (keep most important items)
crusher = SmartCrusher()
result = crusher.crush(large_json, query="relevant keywords")
# result.compressed  → compressed JSON string
# result.items_kept / items_total → retention ratio
# result.compression_ratio → e.g. 0.3 means 70% tokens saved
```

## SmartCrusher — 5-Dimensional Scoring

Keeps items by:
1. **First/Last items** — pagination context + latest data (30% head + 15% tail)
2. **Error items** — 100% preserved
3. **Statistical outliers** — > 2 std from mean
4. **Query-relevant** — BM25 match against user query
5. **Change points** — significant transitions in data

Config overrides:
```python
crusher = SmartCrusher(config={
    "max_items_after_crush": 15,
    "first_fraction": 0.3,
    "variance_threshold": 2.0,
})
```

## CCR Store — Compress-Cache-Retrieve

```python
store = CCRStore(max_entries=1000, ttl_seconds=3600)

# Cache original when crushing
store.put(hash_key, original_text)

# Retrieve if LLM needs more detail
full_text = store.get(hash_key)
```

## Token Estimation

```python
from skills.headroom import estimate_tokens
tokens = estimate_tokens("some text — CJK-aware counting")
```

## Integration Notes

- This module is already imported by `skills/shared/context_trimming.py` (SmartCrusher layer)
- CCR background worker in `skills/sakura/app/agent/memory_curator.py` writes to Qdrant
- For roleplay context trimming: the context_trimming module wraps SmartCrusher with 24msg/40K char cap
