#!/usr/bin/env python3
"""Read-only inspector for the project's embedded Qdrant store (needs no embedding server).

用法 / Usage (paths are repo-relative, run from anywhere):
    python skills/shared/qdrant_store_inspect.py
    python skills/shared/qdrant_store_inspect.py --character natsume

前提 / Requires: `pip install qdrant_client` (>=1.20 works; note that 1.20 removed
`client.search()` — the bridge and this script both use `client.query_points()`).

注意 / Caveats:
  - Qdrant 本地(文件)模式是**单写者**：桌宠进程持有该目录时这里会报
    "already accessed by another instance"。等它释放或改用 Qdrant server 模式。
  - Embedded (file) mode is single-writer; close the other client first.
  - 写入方（桌宠 mem0）的 user_id = 角色卡 id（不改大小写），所以是 "Sakura" 而不是
    "sakura"。--character 的探测会复用 mem0_bridge.scope_ids() 的候选集合。
  - Only reads. Nothing is written to the store.
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE = REPO_ROOT / "skills" / "sakura" / "data" / "memory" / "qdrant"
COLLECTION = "sakura_memories"


def main() -> int:
    ap = argparse.ArgumentParser(description="Inspect the embedded Qdrant memory store (read-only).")
    ap.add_argument("--store", default=str(DEFAULT_STORE), help="Qdrant data dir (default: skills/sakura/data/memory/qdrant)")
    ap.add_argument("--character", default=None, help="also probe this bridge user_id, plus its capitalised form")
    ap.add_argument("--show", type=int, default=3, help="how many memory texts to print")
    args = ap.parse_args()

    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import FieldCondition, Filter, MatchValue
    except ImportError:
        print("FAIL: qdrant_client not installed -> pip install qdrant_client")
        return 2

    store = Path(args.store)
    print(f"store: {store}")
    if not store.exists():
        print(f"FAIL: store dir missing")
        return 2

    try:
        client = QdrantClient(path=str(store))
    except RuntimeError as exc:
        print(f"FAIL: {exc}")
        print("hint: embedded mode is single-writer — stop the other client (pet process / another script) first")
        return 2

    rc = 0
    try:
        collections = [c.name for c in client.get_collections().collections]
        print(f"collections: {collections or '(none)'}")
        if COLLECTION not in collections:
            print(f"FAIL: collection '{COLLECTION}' missing -> python -m skills.shared.mem0_bridge init <char>")
            return 1

        for col in collections:
            info = client.get_collection(col)
            vec = info.config.params.vectors
            if isinstance(vec, dict):
                vec = next(iter(vec.values()), None)
            print(f"[{col}] points={info.points_count} status={info.status.value} "
                  f"dim={getattr(vec, 'size', '?')} dist={getattr(vec, 'distance', '?')} "
                  f"sparse={list(info.config.params.sparse_vectors or {})}")

            points, _ = client.scroll(col, limit=200, with_payload=True, with_vectors=True)
            users: dict[str, int] = {}
            keys: set[str] = set()
            for p in points:
                payload = p.payload or {}
                uid = str(payload.get("user_id"))
                users[uid] = users.get(uid, 0) + 1
                keys.update(payload.keys())
            print(f"    user_id scopes: {users or '(none)'}")
            print(f"    payload keys  : {sorted(keys)}")
            for p in points[: max(0, args.show)]:
                payload = p.payload or {}
                text = payload.get("data") or payload.get("memory") or ""
                print(f"    - [{payload.get('created_at') or payload.get('timestamp')}] {str(text)[:100]}")

            if not points:
                continue

            # vector search proof: query with a stored vector, expect score ~1.0 on itself
            vec0 = points[0].vector
            vec0 = vec0 if isinstance(vec0, list) else list((vec0 or {}).values())[0]
            hits = client.query_points(col, query=list(vec0), limit=3, with_payload=False)
            top = hits.points[0] if hits.points else None
            print(f"    ANN self-query: hits={len(hits.points)} top_score={top.score:.4f} (expect ~1.0)")
            if not hits.points or top.score < 0.99:
                print("    FAIL: vector search did not rank the source point first")
                rc = 1

        if args.character:
            probe = _probe_users(client, args.character, Filter, FieldCondition, MatchValue)
            for uid, n in probe.items():
                print(f"filter user_id='{uid}' -> {n} hits")
            total = sum(probe.values())
            points_exist = (client.count(COLLECTION, exact=True).count or 0) > 0
            if points_exist and total == 0:
                print("    FAIL: none of the candidate scopes match anything — bridge will return 0 hits")
                print("          真正可用的域见上面 `user_id scopes:` 行（写入方用的是角色卡 id，大小写不改）")
                rc = 1
    except Exception as exc:  # pragma: no cover - diagnostic surface
        print(f"FAIL: {type(exc).__name__}: {exc}")
        rc = 1
    finally:
        try:
            client.close()
        except Exception:
            pass

    print("RESULT:", "OK" if rc == 0 else "PROBLEMS FOUND")
    return rc


def _probe_users(client, character, Filter, FieldCondition, MatchValue) -> dict[str, int]:
    """用桥接会用的那批 user_id 候选逐个计数（优先复用 scope_ids，退到大小写变体）。"""
    candidates: list[str] = []
    try:
        import sys
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        candidates = list(scope_ids := __import__("skills.shared.mem0_bridge", fromlist=["scope_ids"]).scope_ids(character))
    except Exception:
        pass
    for fallback in (character, character.capitalize(), character.lower()):
        if fallback not in candidates:
            candidates.append(fallback)

    out: dict[str, int] = {}
    for uid in candidates:
        if uid in out:
            continue
        res = client.scroll(
            COLLECTION,
            scroll_filter=Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=uid))]),
            limit=200,
            with_payload=False,
        )[0]
        out[uid] = len(res)
    return out


if __name__ == "__main__":
    sys.exit(main())
