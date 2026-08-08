"""
Mem0 ↔ OpenClaw Memory Bridge (方案 B — 四角色多租户版)

双路记忆注入桥接器:
1. sync: 从 mem0 Qdrant 同步到 memory/role_play/<角色>/_mem0_auto.md
2. search: 直接查询 mem0 Qdrant + OpenClaw 内置 memory search
3. list: 列出所有 mem0 记忆
4. init <角色>: 为角色初始化独立的 mem0 Qdrant collection（无桌宠时用嵌入服务器独立写）

架构:
  所有角色共用同一嵌入模型 (all-MiniLM-L6-v2, 9999端口)
  数据隔离: 每个角色在 Qdrant 中通过 user_id 过滤，共享一个 collection
  桥接: 定时同步 mem0 Qdrant → memory/role_play/<角色>/_mem0_auto.md
        让 OpenClaw 内置 memory search 同时索引

用法:
  python mem0_bridge.py sync <角色名>          # 同步 mem0 → markdown
  python mem0_bridge.py search <角色名> <查询>  # 双路搜索
  python mem0_bridge.py list <角色名>           # 列出所有 mem0 记忆
  python mem0_bridge.py add <角色名> <文本>     # 手动添加一条记忆
"""

import json
import os
import sys
import io
from datetime import datetime
from pathlib import Path

# Only redirect stdout if running as main script (not imported as module)
if __name__ == "__main__":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except (ValueError, AttributeError):
        pass  # stdout already text or no buffer

# ── Headroom SmartCrusher + CCR ──────────────────────────────
HEADROOM_MODULE = Path(__file__).parent.parent / "headroom"
# Ensure the workspace dir (parent of skills/) is on sys.path so 'skills.headroom' resolves
WORKSPACE_DIR = HEADROOM_MODULE.parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))
from skills.headroom import SmartCrusher, CCRStore, estimate_tokens

# 全局 CCR 缓存（进程内 LRU，TTL=300s）
_global_ccr = CCRStore(max_entries=500, ttl_seconds=300)

# 压缩配置
CRUSH_CONFIG = {
    "min_tokens_to_crush": 150,       # 少于 150 tokens 不压缩
    "max_items_after_crush": 10,      # 压缩后最多保留 10 条
    "first_fraction": 0.3,            # 保留开头 30%
    "last_fraction": 0.1,             # 保留结尾 10%
    "variance_threshold": 2.0,
    "preserve_change_points": True,
}

# ── Paths ──────────────────────────────────────────────────
WORKSPACE = Path(os.environ.get(
    "OPENCLAW_WORKSPACE",
    os.path.expandvars(r"%USERPROFILE%\.openclaw\workspace")
))
MEM0_QDRANT = WORKSPACE / "skills" / "sakura" / "data" / "memory" / "qdrant"
MEMORY_DIR = WORKSPACE / "memory" / "role_play"

# ── 四角色配置 ────────────────────────────────────────────
CHARACTERS = {
    "sakura": {"user_id": "sakura", "lang_instruction": "夜乃桜的长期记忆使用简体中文记录。"},
    "natsume": {"user_id": "natsume", "lang_instruction": "夏目的长期记忆使用简体中文记录，保留日文称呼如「君」。"},
    "enola": {"user_id": "enola", "lang_instruction": "Enola 的长期记忆使用简体中文记录。"},
    "atori": {"user_id": "atori", "lang_instruction": "Atori 的长期记忆使用简体中文记录。"},
}

EMBEDDING_SERVER = "http://127.0.0.1:9999/v1/embeddings"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMS = 384


def _get_embedding(text: str) -> list[float]:
    """调用本地嵌入服务器获取向量"""
    import urllib.request
    data = json.dumps({"model": EMBEDDING_MODEL, "input": text}).encode()
    req = urllib.request.Request(EMBEDDING_SERVER, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
        return result["data"][0]["embedding"]
    except Exception:
        # 返回一个零向量作为 fallback（仅用于存储，不用于搜索）
        return [0.0] * EMBEDDING_DIMS


def _get_qdrant_client():
    """获取 Qdrant 客户端，自动创建集合"""
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams
    
    client = QdrantClient(path=str(MEM0_QDRANT))
    
    collection_name = "sakura_memories"
    
    # 确保 collection 存在
    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=EMBEDDING_DIMS, distance=Distance.COSINE, on_disk=True),
        )
    
    return client


def search_mem0_qdrant(character: str, query: str, limit: int = 10) -> list[dict]:
    """在 Qdrant 中搜索角色的 mem0 记忆"""
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    
    client = _get_qdrant_client()
    char_cfg = CHARACTERS.get(character, CHARACTERS["sakura"])
    user_id = char_cfg["user_id"]
    
    try:
        query_vec = _get_embedding(query)
        
        results = client.query_points(
            collection_name="sakura_memories",
            query=query_vec,
            query_filter=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]),
            limit=limit * 2,
            with_payload=True,
        )
        
        out = []
        for hit in results.points:
            payload = hit.payload or {}
            mem_text = payload.get("memory", "") or payload.get("data", "")
            if not mem_text:
                continue
            out.append({
                "id": hit.id,
                "memory": mem_text,
                "score": float(hit.score),
                "metadata": {k: v for k, v in payload.items() if k not in ("memory", "data")},
            })
        
        out.sort(key=lambda x: x["score"], reverse=True)
        return out[:limit]
    finally:
        try:
            client.close()
        except Exception:
            pass


def list_mem0(character: str, limit: int = 50) -> list[dict]:
    """列出角色的所有 mem0 记忆"""
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    
    client = _get_qdrant_client()
    char_cfg = CHARACTERS.get(character, CHARACTERS["sakura"])
    user_id = char_cfg["user_id"]
    
    try:
        points, _ = client.scroll(
            collection_name="sakura_memories",
            scroll_filter=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]),
            limit=limit,
            with_payload=True,
        )
        
        out = []
        for pt in points:
            payload = pt.payload or {}
            mem_text = payload.get("memory", "") or payload.get("data", "")
            if not mem_text:
                continue
            out.append({
                "id": pt.id,
                "memory": mem_text,
                "metadata": {k: v for k, v in payload.items() if k not in ("memory", "data")},
            })
        return out
    finally:
        try:
            client.close()
        except Exception:
            pass


def add_memory(character: str, text: str) -> dict:
    """手动为角色添加一条记忆"""
    from qdrant_client.models import PointStruct
    
    client = _get_qdrant_client()
    char_cfg = CHARACTERS.get(character, CHARACTERS["sakura"])
    user_id = char_cfg["user_id"]
    
    vec = _get_embedding(text)
    point_id = hash(f"{user_id}:{text}:{datetime.now().isoformat()}") & 0x7FFFFFFFFFFFFFFF
    
    try:
        client.upsert(
            collection_name="sakura_memories",
            points=[PointStruct(
                id=point_id,
                vector=vec,
                payload={
                    "memory": text,
                    "user_id": user_id,
                    "agent_id": character,
                    "timestamp": datetime.now().isoformat(),
                },
            )]
        )
        return {"id": point_id, "memory": text, "status": "added"}
    finally:
        try:
            client.close()
        except Exception:
            pass


def sync_mem0_to_markdown(character: str) -> dict:
    """同步 mem0 Qdrant → memory/role_play/<角色>/_mem0_auto.md"""
    memories = list_mem0(character)
    
    char_dir = MEMORY_DIR / character
    char_dir.mkdir(parents=True, exist_ok=True)
    out_path = char_dir / "_mem0_auto.md"
    
    if not memories:
        content = f"""# {character} - Mem0 自动记忆

> 最后同步: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 状态: 暂无长期记忆（mem0 Qdrant 为空）

此文件由 mem0_bridge.py 自动生成，每 30 分钟同步一次。
"""
    else:
        lines = [
            f"# {character} - Mem0 自动记忆",
            "",
            f"> 最后同步: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"> 记忆数: {len(memories)}",
            f"> 来源: mem0 Qdrant (user_id={CHARACTERS[character]['user_id']})",
            "",
            "此文件由 mem0_bridge.py 自动生成，每 30 分钟同步一次。",
            "",
            "---",
            "",
        ]
        for i, mem in enumerate(memories, 1):
            lines.append(f"## 记忆 {i}")
            lines.append(f"* {mem['memory']}")
            meta = mem.get('metadata', {})
            clean_meta = {k: v for k, v in meta.items() if k not in ('user_id', 'agent_id', 'vector') and v}
            if clean_meta:
                for k, v in clean_meta.items():
                    lines.append(f"  * ({k}: {v})")
            lines.append("")
        
        content = "\n".join(lines)
    
    out_path.write_text(content, encoding="utf-8")
    return {"file": str(out_path), "count": len(memories), "character": character}


# ── SmartCrusher + CCR 压缩注入 ──────────────────────────

def compress_search_results(search_results: list[dict], query: str) -> tuple[dict]:
    """
    压缩搜索结果的 memory 字段（文本），用 SmartCrusher 提取高信息量部分。
    """
    if not search_results:
        return search_results, {"status": "empty"}
    
    crusher = SmartCrusher(CRUSH_CONFIG)
    total_before = 0
    total_after = 0
    compressed_items = []
    
    for result in search_results:
        mem_text = result.get("memory", "")
        if not mem_text:
            compressed_items.append(result)
            continue
        
        total_before += estimate_tokens(mem_text)
        
        crush_result = crusher._compress_plain(mem_text, query)
        total_after += estimate_tokens(crush_result.compressed)
        
        _global_ccr.put(crush_result.original_hash, mem_text, {
            "source": "mem0_qdrant",
            "character": "unknown",
            "timestamp": datetime.now().isoformat(),
        })
        
        entry = dict(result)
        entry["memory"] = crush_result.compressed
        entry["_crushed"] = True
        entry["_original_hash"] = crush_result.original_hash
        compressed_items.append(entry)
    
    stats = {
        "status": "compressed",
        "items": len(compressed_items),
        "tokens_before": total_before,
        "tokens_after": total_after,
        "savings_pct": round((1 - total_after / max(1, total_before)) * 100, 1),
        "ccr_cache_size": _global_ccr.stats()["size"],
    }
    
    return compressed_items, stats


def retrieve_from_ccr(original_hash: str) -> tuple[bool, str]:
    """从 CCR 缓存取回原文。"""
    text = _global_ccr.get(original_hash)
    if text:
        return True, text
    return False, "原文不在缓存中 (已过期或超出容量)"


# ── CLI ────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Mem0 ↔ OpenClaw Memory Bridge (四角色版)")
    sub = parser.add_subparsers(dest="command")
    
    sync_parser = sub.add_parser("sync", help="同步 mem0 Qdrant → memory/role_play/<角色>/_mem0_auto.md")
    sync_parser.add_argument("character", help="角色名 (sakura/natsume/enola/atori)")
    
    search_parser = sub.add_parser("search", help="搜索角色的 mem0 记忆")
    search_parser.add_argument("character", help="角色名")
    search_parser.add_argument("query", help="搜索内容")
    search_parser.add_argument("--limit", type=int, default=10)
    
    list_parser = sub.add_parser("list", help="列出角色的所有 mem0 记忆")
    list_parser.add_argument("character", help="角色名")
    list_parser.add_argument("--limit", type=int, default=50)
    
    add_parser = sub.add_parser("add", help="手动添加一条记忆")
    add_parser.add_argument("character", help="角色名")
    add_parser.add_argument("text", help="记忆内容")
    
    init_parser = sub.add_parser("init", help="初始化角色的 Qdrant 存储（创建 collection）")
    init_parser.add_argument("character", help="角色名")
    
    crush_parser = sub.add_parser("crush", help="测试 SmartCrusher 压缩搜索结果")
    crush_parser.add_argument("character", help="角色名")
    crush_parser.add_argument("query", help="搜索查询")
    crush_parser.add_argument("--limit", type=int, default=10)
    
    retrieve_parser = sub.add_parser("retrieve", help="从 CCR 缓存取回原文")
    retrieve_parser.add_argument("hash", help="原文 hash")
    
    args = parser.parse_args()
    
    if args.command == "sync":
        result = sync_mem0_to_markdown(args.character)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "search":
        results = search_mem0_qdrant(args.character, args.query, args.limit)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif args.command == "list":
        results = list_mem0(args.character, args.limit)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif args.command == "add":
        result = add_memory(args.character, args.text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "init":
        _get_qdrant_client()
        print(json.dumps({"status": "ok", "character": args.character, "message": "Collection 已就绪"}, ensure_ascii=False))
    elif args.command == "crush":
        raw_results = search_mem0_qdrant(args.character, args.query, args.limit)
        compressed, stats = compress_search_results(raw_results, args.query)
        print(json.dumps({
            "raw_count": len(raw_results),
            "compressed_count": len(compressed),
            "stats": stats,
            "compressed_results": compressed,
        }, ensure_ascii=False, indent=2))
    elif args.command == "retrieve":
        ok, text = retrieve_from_ccr(args.hash)
        print(json.dumps({
            "success": ok,
            "hash": args.hash,
            "text": text if ok else None,
            "error": None if ok else text,
        }, ensure_ascii=False, indent=2))
    else:
        parser.print_help()
