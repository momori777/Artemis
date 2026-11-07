#!/usr/bin/env python3
r"""End-to-end self-check for the mem0 + RAG + headroom (SmartCrusher / CCR) memory stack.

Runs the whole read/write path against the project's own embedded Qdrant store:

    embedding server (:9999)  ->  all-MiniLM-L6-v2 384-d vectors
    mem0_bridge               ->  Qdrant collection `sakura_memories` (dense + BM25 sparse)
    headroom SmartCrusher     ->  compress RAG hits, CCR reversible cache round-trip

用法 / Usage (paths are repo-relative, run from anywhere):
    python skills/shared/mem0_selfcheck.py
    python skills/shared/mem0_selfcheck.py --character sakura --query 提醒我喝水休息
    python skills/shared/mem0_selfcheck.py --skip-write      # read-only pass
    python skills/shared/mem0_selfcheck.py --root "%USERPROFILE%\.openclaw\workspace" --character shifty
        # 检查 OpenClaw workspace 端（谢芙蒂那一侧）自己的 store；2026-11-07 两端均已跑通。

前提 / Requires (any Python 3.12+ with these packages — the bundled
`skills/sakura/runtime` venv only works on the machine that created it):
    pip install qdrant_client sentence-transformers flask
    (torch comes in as a dependency; the CPU build is enough — this stack never touches VRAM)
    then start the embedding server:  python skills/shared/embedding_server.py

退出码 / Exit codes: 0 = all green, 1 = check failed, 2 = environment not ready.
"""

import argparse
import os
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# --root <path> points the check at *another* tree's store (e.g. the OpenClaw workspace
# side where Shifty runs). Must be resolved BEFORE importing mem0_bridge, because the
# bridge pins MEM0_QDRANT from OPENCLAW_WORKSPACE at import time. Without --root the
# check stays on this checkout, as before.
def _early_root() -> Path:
    for i, arg in enumerate(sys.argv):
        if arg == "--root" and i + 1 < len(sys.argv):
            return Path(sys.argv[i + 1]).expanduser().resolve()
    return REPO_ROOT

ROOT = _early_root()
os.environ["OPENCLAW_WORKSPACE"] = str(ROOT)
sys.path.insert(0, str(ROOT))

from skills.shared.mem0_bridge import (  # noqa: E402
    CHARACTERS,
    MEM0_QDRANT,
    add_memory,
    compress_search_results,
    list_mem0,
    retrieve_from_ccr,
    search_mem0_qdrant,
    _get_embedding,
)

QDRANT_DIR = ROOT / "skills" / "sakura" / "data" / "memory" / "qdrant"
COLLECTION = "sakura_memories"
DEMO_TEXT = "樱: 主人今天工作到很晚，记得喝温水。" + "（他一直在改 Strata 的启动参数，改完又回头改 README。）" * 14


def check_env() -> int:
    """2 = something the script cannot fix by itself is missing."""
    bad = 0
    try:
        with urllib.request.urlopen("http://127.0.0.1:9999/health", timeout=5) as resp:
            print(f"[env] embedding server :9999 -> {resp.read().decode('utf-8', 'replace')}")
    except Exception as exc:
        print(f"[env] FAIL embedding server :9999 unreachable: {exc}")
        print("      start it with: python skills/shared/embedding_server.py")
        bad = 2
    try:
        import qdrant_client  # noqa: F401
        print("[env] qdrant_client OK")
    except ImportError:
        print("[env] FAIL qdrant_client missing -> pip install qdrant_client")
        bad = 2
    return bad


def check_embeddings() -> bool:
    t0 = time.time()
    vec = _get_embedding("樱提醒我喝水")
    ms = int((time.time() - t0) * 1000)
    if all(x == 0.0 for x in vec):
        print(f"[embed] FAIL zero-vector fallback used ({ms} ms) — port 9999 is not answering")
        return False
    print(f"[embed] dim={len(vec)} norm={sum(x * x for x in vec) ** 0.5:.4f} {ms} ms")
    return len(vec) == 384


def check_store() -> tuple[bool, bool]:
    """Read the store once and report scopes (single-writer: closed before the bridge runs).

    Returns (store_ok, store_has_points)."""
    from qdrant_client import QdrantClient

    if not QDRANT_DIR.exists():
        print(f"[store] FAIL missing {QDRANT_DIR}")
        return False, False
    try:
        client = QdrantClient(path=str(QDRANT_DIR))
    except RuntimeError as exc:
        print(f"[store] FAIL {exc}")
        print("       hint: embedded Qdrant is single-writer — the pet process may be holding it")
        return False, False
    try:
        names = [c.name for c in client.get_collections().collections]
        if COLLECTION not in names:
            print(f"[store] FAIL collection '{COLLECTION}' not in {names}")
            return False, False
        info = client.get_collection(COLLECTION)
        points, _ = client.scroll(COLLECTION, limit=200, with_payload=True, with_vectors=True)
        scopes: dict[str, int] = {}
        for p in points:
            uid = str((p.payload or {}).get("user_id"))
            scopes[uid] = scopes.get(uid, 0) + 1
        print(f"[store] points={info.points_count} scopes={scopes or '(none)'}")

        configured = {cfg["user_id"] for cfg in CHARACTERS.values()}
        stored = set(scopes)
        blind = sorted(s for s in configured if s not in stored)
        if blind and stored:
            near = [s for s in stored if any(s.lower() == b.lower() for b in blind)]
            if near:
                print(f"[store] WARN 库里是不带规范的小写域: {near}（桥接靠 MatchAny 才能捡到）")
                print("       刷成规范域: python skills/shared/qdrant_rescope.py --apply")
            else:
                print(f"[store] note: 这些角色还没记忆（新角色正常）: {blind}")
        if not points:
            print("[store] WARN store empty — nothing to retrieve")
        return True, bool(points)
    finally:
        try:
            client.close()
        except Exception:
            pass


def check_read(character: str, query: str, store_has_points: bool) -> bool:
    hits = search_mem0_qdrant(character, query, limit=3)
    print(f"[read] search_mem0_qdrant('{character}', {query!r}) -> {len(hits)} hits")
    for h in hits:
        print(f"       {h['score']:+.3f} {h['memory'][:90]}")
    if hits:
        return True
    if store_has_points:
        # points exist but no candidate scope matches them (legacy spelling not covered by scope_ids)
        print("       FAIL 0 hits although the store holds points — bridge user_id scope matches nothing")
        print("       查库: python skills/shared/qdrant_store_inspect.py ；刷齐隔离域: python skills/shared/qdrant_rescope.py --apply")
        return False
    print("       note: 0 hits, store is empty (nothing to retrieve)")
    return True


def check_write(character: str) -> bool:
    marker = "mem0_selfcheck 写入自检（可安全删除）"
    res = add_memory(character, marker)
    pid = res.get("id")
    print(f"[write] add_memory -> id={pid}")
    found = [h for h in search_mem0_qdrant(character, marker, limit=3) if h["id"] == pid]
    if not found:
        print("[write] FAIL added point was not retrievable")
    else:
        print(f"[write] round-trip OK, score={found[0]['score']:+.3f}")

    # embedded mode is single-writer, so reopen after the bridge closed its client
    from qdrant_client import QdrantClient
    client = QdrantClient(path=str(QDRANT_DIR))
    try:
        client.delete(COLLECTION, points_selector=[pid])
        print(f"[write] cleanup deleted {pid}; points={client.count(COLLECTION, exact=True).count}")
    finally:
        client.close()
    return bool(found)


def check_headroom() -> bool:
    demo = [{"id": "demo", "score": 0.8, "memory": DEMO_TEXT}]
    compressed, stats = compress_search_results(demo, "喝水 README")
    print(f"[headroom] SmartCrusher: {stats['tokens_before']} -> {stats['tokens_after']} tokens "
          f"({stats['savings_pct']}% saved), items={stats['items']}")
    ok, back = retrieve_from_ccr(compressed[0]["_original_hash"])
    print(f"[headroom] CCR retrieve: ok={ok} restored_chars={len(back) if ok else 0}")
    if stats["savings_pct"] == 0:
        print("           note: short memories stay verbatim (min_tokens_to_crush); try crush on a long tool dump")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="mem0 + RAG + headroom end-to-end self-check.")
    ap.add_argument("--character", default="sakura", choices=sorted(CHARACTERS))
    ap.add_argument("--query", default="提醒我喝水休息")
    ap.add_argument("--skip-write", action="store_true", help="read-only pass (no add/delete)")
    ap.add_argument("--root", default=str(REPO_ROOT),
                    help="project/workspace tree whose store to check (default: this repo); "
                         "also read early, before the bridge import")
    args = ap.parse_args()

    print(f"tree: {ROOT}")
    print(f"store: {MEM0_QDRANT}")
    env = check_env()
    if env:
        return env

    checks = [check_embeddings()]
    store_ok, store_has_points = check_store()
    checks.append(store_ok)
    checks.append(check_read(args.character, args.query, store_has_points))
    if not args.skip_write:
        checks.append(check_write(args.character))
    checks.append(check_headroom())

    ok = all(checks)
    print("RESULT:", "ALL GREEN" if ok else "PROBLEMS FOUND (see WARN/FAIL above)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
