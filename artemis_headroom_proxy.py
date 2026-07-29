#!/usr/bin/env python3
"""
OpenAI-compatible /v1/chat/completions proxy with forced Headroom + Mem0.

拦截 OpenClaw Gateway 发来的 LLM 请求，无论目标后端是本地 llama-server 还是云端 API，
统一注入 mem0 角色向量记忆 + SmartCrusher 压缩，然后透传到目标后端。

数据流:
  OpenClaw → /v1/chat/completions (port 19251)
    → [1] 检测当前角色 → mem0 Qdrant 搜索
    → [2] 注入 mem0 结果到 system prompt
    → [3] SmartCrusher 5维压缩对话历史
    → [4] 根据 model 字段路由:
         - local-llama/*  → llama-server:8080
         - 其他 provider  → 对应云端 baseUrl (apiKey 从 openclaw.json 读取)

关键参数 (与 shiki_daemon.py 对齐):
  headroom: RECENT_FULL_ROUNDS=4, MAX_MESSAGES=24, MAX_CHARS=40K
  mem0: limit=5, score>0.7高相关, >0.5自然融入, <0.3忽略
"""

import json
import os
import sys
import urllib.request
import urllib.error
import hashlib
import re

WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORKSPACE_ROOT)

from skills.shared.context_trimming import trim_messages_for_model, context_stats
from flask import request, jsonify, Response

# ── 从 config.yaml 读取配置（避免硬编码） ──
def _load_config():
    import yaml
    cfg_path = os.path.join(WORKSPACE_ROOT, "config.yaml")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}

_CFG = _load_config()

LLAMA_PORT = int(os.environ.get("LLAMA_PORT", str(_CFG.get("llama_port", 8080))))
LLAMA_URL = f"http://127.0.0.1:{LLAMA_PORT}/v1/chat/completions"
# 模型名从 config.yaml 读取，fallback 到环境变量
_model_path = _CFG.get("llama_model", "")
LLAMA_MODEL = os.path.basename(_model_path) if _model_path else os.environ.get("LLAMA_MODEL", "local-model")

# ── Headroom 关键参数 (与 context_trimming.py 对齐) ──────────
HEADROOM_RECENT_FULL_ROUNDS = 4   # 最近 N 轮完整保留
HEADROOM_MAX_MESSAGES = 24        # 消息数硬限制
HEADROOM_MAX_CHARS = 40_000       # 字符数硬限制

# ── Mem0 关键参数 ────────────────────────────────────────────
MEM0_SEARCH_LIMIT = 5             # 搜索返回条数
MEM0_SCORE_HIGH = 0.7             # 高相关阈值 (必须体现)
MEM0_SCORE_MEDIUM = 0.5           # 中等相关 (自然融入)
MEM0_SCORE_LOW = 0.3              # 低相关 (可选参考, 低于此忽略)

# ── 角色检测映射 ─────────────────────────────────────────────
# 从 system prompt 内容检测当前角色名
CHARACTER_DETECT_KEYWORDS = {
    "natsume": ["四季夏目", "natsume", "夏目", "shiki natsume"],
    "sakura": ["夜乃桜", "sakura", "夜乃樱", "yono sakura"],
    "enola": ["Enola", "enola"],
    "atori": ["Atori", "atori", "atri"],
}

# 角色名 → mem0 user_id 映射 (与 mem0_bridge.py CHARACTERS 对齐)
CHARACTER_MEM0_ID = {
    "natsume": "natsume",
    "sakura": "sakura",
    "enola": "enola",
    "atori": "atori",
}

# ── 本地 provider 前缀（这些走 llama-server，不经过云端） ──
LOCAL_PROVIDER_PREFIXES = ("local-llama", "local")


def _detect_character(messages: list) -> str | None:
    """从 messages 的 system prompt 中检测当前角色名。"""
    for msg in messages:
        if msg.get("role") != "system":
            continue
        content = msg.get("content", "")
        for char_id, keywords in CHARACTER_DETECT_KEYWORDS.items():
            for kw in keywords:
                if kw in content:
                    return char_id
    return None


def _search_mem0(character_id: str, query: str) -> str | None:
    """
    搜索 mem0 Qdrant 并返回格式化的记忆上下文。
    
    返回 None 表示无相关记忆。
    返回字符串表示格式化的记忆块，可拼接到 system prompt。
    """
    try:
        if WORKSPACE_ROOT not in sys.path:
            sys.path.insert(0, WORKSPACE_ROOT)
        # 部署版 mem0_bridge (workspace skills/shared/)
        from skills.shared.mem0_bridge import search_mem0_qdrant
        results = search_mem0_qdrant(character_id, query, limit=MEM0_SEARCH_LIMIT)
        if not results:
            return None

        relevant = [r for r in results if r.get("score", 0) > MEM0_SCORE_LOW]
        if not relevant:
            return None

        lines = [
            "\n\n## 长期记忆 (Mem0 Qdrant)",
            "以下是与你、与当前对话相关的长期记忆，请自然地融入对话中，不必逐条复述：",
        ]
        for r in relevant:
            score = r.get("score", 0)
            mem = r.get("memory", "")
            if score > MEM0_SCORE_HIGH:
                lines.append(f"- [高相关] {mem}")
            elif score > MEM0_SCORE_MEDIUM:
                lines.append(f"- {mem}")
            else:
                lines.append(f"- (弱相关) {mem}")
        return "\n".join(lines)
    except Exception as e:
        print(f"[headroom-proxy] mem0 search error: {e}", file=sys.stderr, flush=True)
        return None


def _resolve_upstream(model_field: str) -> tuple[str, str, dict]:
    """
    根据 request 中的 model 字段解析目标后端。
    
    model_field 格式: "provider-id/model-id" 或纯 "model-id"
    
    读取 ~/.openclaw/headroom_routes.json sidecar 文件
    获取 provider 的真实后端地址和 apiKey。
    
    Returns:
        (upstream_url, upstream_model_name, extra_headers)
        
    对于本地 provider (local-llama/*, local/*):
        → llama-server:8080, model = LLAMA_MODEL
    对于云端 provider:
        → sidecar 中的原始 baseUrl + /chat/completions
    """
    parts = model_field.split("/", 1)
    provider_prefix = parts[0].lower() if len(parts) > 1 else ""
    
    # 本地 provider → llama-server
    if provider_prefix in LOCAL_PROVIDER_PREFIXES:
        return LLAMA_URL, LLAMA_MODEL, {}
    
    # 云端 provider → 从 sidecar 路由文件 + openclaw.json 读取
    routes_path = os.path.join(os.path.expanduser("~"), ".openclaw", "headroom_routes.json")
    oc_cfg_path = os.path.join(os.path.expanduser("~"), ".openclaw", "openclaw.json")
    
    if not os.path.isfile(oc_cfg_path):
        return LLAMA_URL, LLAMA_MODEL, {}
    
    try:
        # 读 sidecar 路由映射
        routes = {}
        if os.path.isfile(routes_path):
            with open(routes_path, "r", encoding="utf-8") as f:
                routes = json.load(f)
        
        # 读 openclaw.json 获取 apiKey
        with open(oc_cfg_path, "r", encoding="utf-8") as f:
            oc_cfg = json.load(f)
        providers = oc_cfg.get("models", {}).get("providers", {})
        
        provider_id = parts[0] if len(parts) > 1 else model_field
        provider_cfg = providers.get(provider_id)
        if not provider_cfg:
            print(f"[headroom-proxy] unknown provider '{provider_id}', falling back to local", flush=True)
            return LLAMA_URL, LLAMA_MODEL, {}
        
        # 从 sidecar 文件读原始 baseUrl，fallback 到 openclaw.json 的 baseUrl
        base_url = routes.get(provider_id, "")
        if not base_url:
            base_url = provider_cfg.get("baseUrl", "")
        # 如果 baseUrl 还是指向 19251（自己），说明 sidecar 缺失，降级
        if "19251" in base_url:
            base_url = routes.get(provider_id, "")
            if not base_url:
                print(f"[headroom-proxy] no route for '{provider_id}' in sidecar, falling back to local", flush=True)
                return LLAMA_URL, LLAMA_MODEL, {}
        
        if not base_url:
            print(f"[headroom-proxy] no baseUrl for provider '{provider_id}', falling back to local", flush=True)
            return LLAMA_URL, LLAMA_MODEL, {}
        
        base_url = base_url.rstrip("/")
        upstream_url = f"{base_url}/chat/completions"
        
        # model-id 部分（去掉 provider 前缀）
        upstream_model = parts[1] if len(parts) > 1 else model_field
        
        # API key
        api_key = provider_cfg.get("apiKey", "")
        headers = {"Content-Type": "application/json"}
        if api_key and api_key != "***":
            headers["Authorization"] = f"Bearer {api_key}"
        
        return upstream_url, upstream_model, headers
    except Exception as e:
        print(f"[headroom-proxy] provider resolve error: {e}, falling back to local", flush=True)
        return LLAMA_URL, LLAMA_MODEL, {}


def register_headroom_endpoint(app):
    """Register /v1/chat/completions with forced Headroom + Mem0."""

    @app.route("/v1/chat/completions", methods=["POST"])
    def v1_chat_completions():
        data = request.get_json(silent=True) or {}
        messages = data.get("messages", [])
        stream = data.get("stream", False)
        max_tokens = data.get("max_tokens", 4096)
        temperature = data.get("temperature", 0.7)
        model_field = data.get("model", "")

        if not messages:
            return jsonify({"error": "messages is required"}), 400

        # Extract last user message for BM25 relevance matching
        last_user_query = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_query = m.get("content", "")
                break

        # ── Step 1: Mem0 角色向量记忆注入 ──
        character_id = _detect_character(messages)
        mem0_context = None
        if character_id and last_user_query:
            try:
                mem0_context = _search_mem0(character_id, last_user_query)
                if mem0_context:
                    # 拼接到 system prompt 末尾
                    messages = list(messages)  # 不修改原始
                    if messages and messages[0].get("role") == "system":
                        new_content = messages[0]["content"] + mem0_context
                        messages[0] = {**messages[0], "content": new_content}
                    else:
                        messages.insert(0, {"role": "system", "content": mem0_context.strip()})
                    print(f"[headroom-proxy] mem0 injected for {character_id} ({len(mem0_context)} chars)", flush=True)
            except Exception as e:
                print(f"[headroom-proxy] mem0 injection error: {e}", file=sys.stderr, flush=True)

        # ── Step 2: Headroom SmartCrusher 压缩 ──
        try:
            before = context_stats(messages)
            messages = trim_messages_for_model(
                messages,
                query=last_user_query,
                recent_full_rounds=HEADROOM_RECENT_FULL_ROUNDS,
                max_messages=HEADROOM_MAX_MESSAGES,
                max_chars=HEADROOM_MAX_CHARS,
            )
            after = context_stats(messages)
            if before["messages"] != after["messages"]:
                ratio = after["estimated_tokens"] / max(1, before["estimated_tokens"])
                print(f"[headroom-proxy] compressed {before['messages']}→{after['messages']} msgs, "
                      f"{before['estimated_tokens']}→{after['estimated_tokens']} tokens "
                      f"({int((1-ratio)*100)}% saved)", flush=True)
        except Exception as e:
            print(f"[headroom-proxy] compression skipped: {e}", file=sys.stderr, flush=True)

        # ── Step 3: 解析目标后端 ──
        upstream_url, upstream_model, extra_headers = _resolve_upstream(model_field)
        
        is_local = upstream_url == LLAMA_URL
        backend_label = "local-llama" if is_local else model_field
        print(f"[headroom-proxy] forwarding to {backend_label} → {upstream_url}", flush=True)

        # ── Step 4: 转发 ──
        payload = {
            "model": upstream_model,
            "messages": messages,
            "stream": stream,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # 保留原始请求中的额外参数（如 top_p, frequency_penalty 等）
        for k in ("top_p", "frequency_penalty", "presence_penalty", "stop", "seed"):
            if k in data:
                payload[k] = data[k]

        headers = {"Content-Type": "application/json"}
        headers.update(extra_headers)

        try:
            req = urllib.request.Request(
                upstream_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
            )

            if stream:
                resp = urllib.request.urlopen(req, timeout=300)
                def generate():
                    for line_bytes in resp:
                        yield line_bytes
                return Response(generate(), content_type="text/event-stream")
            else:
                resp = urllib.request.urlopen(req, timeout=300)
                return jsonify(json.loads(resp.read()))

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            return jsonify({"error": f"upstream error: {e.code}", "detail": error_body[:500]}), 502
        except Exception as e:
            return jsonify({"error": str(e)}), 502

    print(f"[artemis_bridge] /v1/chat/completions registered (headroom: ON, mem0: ON, routing: auto)", flush=True)


# ── Standalone mode: 独立运行在独立端口，不绑定 artemis_bridge ──
if __name__ == "__main__":
    from flask import Flask
    import argparse

    parser = argparse.ArgumentParser(description="Headroom Proxy (standalone)")
    parser.add_argument("--port", type=int, default=19251, help="Port (default: 19251)")
    args = parser.parse_args()

    app = Flask(__name__)
    register_headroom_endpoint(app)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"ok": True, "service": "headroom-proxy", "port": args.port})

    @app.route("/api/status", methods=["GET"])
    def status():
        return jsonify({"ok": True, "service": "headroom-proxy", "port": args.port})

    print(f"[headroom-proxy] Starting standalone on http://localhost:{args.port}")
    app.run(host="127.0.0.1", port=args.port, threaded=True)
