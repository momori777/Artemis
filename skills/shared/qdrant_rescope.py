#!/usr/bin/env python3
"""Batch-rewrite the mem0/Qdrant isolation scope (`payload.user_id`) to canonical lowercase.

用法 / Usage (paths are repo-relative, run from anywhere; dry run is the default):
    python skills/shared/qdrant_rescope.py                      # report only (repo store)
    python skills/shared/qdrant_rescope.py --apply              # rewrite in place
    python skills/shared/qdrant_rescope.py --store <dir> --apply  # another checkout's store

为什么需要 / Why:
  Qdrant 按 `payload.user_id` 做角色隔离。历史上写入端把这个域写成了**角色卡 id 原样**
  （"Sakura"），而读取侧（`DEFAULT_MEMORY_SCOPE`、`artemis_headroom_proxy.py:CHARACTER_MEM0_ID`、
  `mem0_behavior_integration.py:CHARACTER_MAP`）用的是**小写**（"sakura"）。大小写不同 = 两个
  隔离域，搜索会静默 0 命中。本脚本把旧数据的 user_id 统一刷成小写。
  写入侧现在由 `app/agent/memory.py:_normalize_scope_id` 统一小写，所以刷过之后不会再分叉。

注意 / Caveats:
  - Embedded (file) mode is **single-writer**: if the pet process holds this directory,
    opening the client fails with "already accessed by another instance". Stop it first.
  - 只做 user_id 规范化，不动向量、payload 其他字段、collection 配置。可反复跑（幂等）。
  - 刷之前先跑一次不带 `--apply` 的 dry run 看清楚要改哪些点。
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE = REPO_ROOT / "skills" / "sakura" / "data" / "memory" / "qdrant"
COLLECTION = "sakura_memories"


def scroll_all(client, collection: str):
    """Yield (point_id, payload) for every point, paging with the returned offset."""
    offset = None
    while True:
        kwargs = {"collection_name": collection, "limit": 256, "with_payload": True, "with_vectors": False}
        if offset is not None:
            kwargs["offset"] = offset
        points, offset = client.scroll(**kwargs)
        for point in points:
            yield point.id, (dict(point.payload) if point.payload else {})
        if offset is None:
            return


def main() -> int:
    ap = argparse.ArgumentParser(description="Normalise Qdrant payload.user_id to lowercase.")
    ap.add_argument("--store", default=str(DEFAULT_STORE), help="Qdrant data dir (default: skills/sakura/data/memory/qdrant)")
    ap.add_argument("--collection", default=COLLECTION, help=f"collection name (default: {COLLECTION})")
    ap.add_argument("--apply", action="store_true", help="actually write the new user_id (default: dry run)")
    ap.add_argument("--verbose", action="store_true", help="print every point id being rewritten")
    args = ap.parse_args()
    collection = args.collection

    try:
        from qdrant_client import QdrantClient
    except ImportError:
        print("FAIL: qdrant_client not installed -> pip install qdrant_client")
        return 2

    collection = args.collection

    store = Path(args.store)
    print(f"store: {store}")
    if not store.exists():
        print("FAIL: store dir missing")
        return 2

    try:
        client = QdrantClient(path=str(store))
    except RuntimeError as exc:
        print(f"FAIL: {exc}")
        print("hint: embedded mode is single-writer — stop the pet process (or other client) first")
        return 2

    rc = 0
    try:
        names = [c.name for c in client.get_collections().collections]
        if collection not in names:
            print(f"FAIL: collection {collection!r} not in {names}")
            return 2

        rows = list(scroll_all(client, collection))
        before = Counter(str((payload or {}).get("user_id")) for _pid, payload in rows)
        print(f"points: {len(rows)}  user_id: {dict(before)}")

        todo = [
            (pid, str(payload.get("user_id")), str(payload.get("user_id")).strip().lower())
            for pid, payload in rows
            if payload.get("user_id") is not None and str(payload.get("user_id")).strip().lower() != str(payload.get("user_id"))
        ]
        if not todo:
            print("nothing to rewrite — every user_id is already canonical lowercase")
            return 0

        by_change = Counter(f"{old!r} -> {new!r}" for _pid, old, new in todo)
        for label, count in by_change.items():
            print(f"rewrite {count:>3} point(s): {label}")
        if args.verbose:
            for pid, old, new in todo:
                print(f"  {pid}  {old!r} -> {new!r}")

        if not args.apply:
            print("dry run — add --apply to write")
            return 0

        # Group point ids per target value: set_payload is one call per target scope.
        targets: dict[str, list] = {}
        for pid, _old, new in todo:
            targets.setdefault(new, []).append(pid)
        for new, ids in targets.items():
            client.set_payload(collection_name=collection, points=ids, payload={"user_id": new}, wait=True)
            print(f"applied: {len(ids)} point(s) -> user_id={new!r}")

        after = Counter(str((payload or {}).get("user_id")) for _pid, payload in scroll_all(client, collection))
        print(f"after: {dict(after)}")
        if any(value != value.lower() for value in after):
            print("FAIL: some user_id values are still not lowercase")
            rc = 1
        elif sum(after.values()) != len(rows):
            print(f"FAIL: point count changed {len(rows)} -> {sum(after.values())}")
            rc = 1
        else:
            print("RESULT: OK")
    finally:
        client.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
