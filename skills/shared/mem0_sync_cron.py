#!/usr/bin/env python3
"""
mem0 → memory/role_play 自动同步（由 OpenClaw cron job 调用）

同步所有 harem 角色的 mem0 Qdrant 记忆到 markdown 文件，
供 OpenClaw memory_search 索引。

路径：使用 $OPENCLAW_WORKSPACE 相对路径（项目根目录）。
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ── 路径：$OPENCLAW_WORKSPACE（运行时 workspace）──────────
WORKSPACE = Path(os.environ.get(
    "OPENCLAW_WORKSPACE",
    os.path.expandvars(r"%USERPROFILE%\.openclaw\workspace")
))

# 把 workspace 的 skills/shared 加入 path 以导入 mem0_bridge
sys.path.insert(0, str(WORKSPACE / "skills" / "shared"))

from mem0_bridge import (
    CHARACTERS,
    list_mem0,
    MEMORY_DIR,
)


def sync_all():
    results = {}
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for character in CHARACTERS:
        try:
            memories = list_mem0(character, limit=100)
            char_dir = MEMORY_DIR / character
            char_dir.mkdir(parents=True, exist_ok=True)
            out_path = char_dir / "_mem0_auto.md"

            if not memories:
                content = f"""# {character} - Mem0 自动记忆

> 最后同步: {timestamp}
> 状态: 暂无长期记忆

此文件由 mem0_sync_cron.py 自动生成。
"""
            else:
                lines = [
                    f"# {character} - Mem0 自动记忆",
                    "",
                    f"> 最后同步: {timestamp}",
                    f"> 记忆数: {len(memories)}",
                    f"> 来源: Mem0 Qdrant (user_id={CHARACTERS[character]['user_id']})",
                    "",
                    "此文件由 mem0_sync_cron.py 自动生成。",
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
            results[character] = {"file": str(out_path), "count": len(memories), "status": "ok"}

        except Exception as exc:
            results[character] = {"status": "error", "error": str(exc)}

    return timestamp, results


if __name__ == "__main__":
    ts, results = sync_all()
    summary = {
        "timestamp": ts,
        "characters": results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    errors = [c for c, r in results.items() if r.get("status") == "error"]
    if errors:
        print(f"\n⚠️ 同步出错: {errors}", file=sys.stderr)
        sys.exit(1)
    else:
        total = sum(r["count"] for r in results.values())
        print(f"\n✅ 同步完成: {total} 条记忆")
