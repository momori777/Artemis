#!/usr/bin/env python3
"""
Shiki Daemon — AI Girlfriend Service Manager
=============================================
System tray app that manages all Shiki services.
- Double-click shiki.cmd → tray icon appears, services auto-start
- Right-click tray → Start All / Stop All / Web Dashboard / Quit
- Close window → graceful shutdown of all services
- Built-in HTTP dashboard on localhost:19260

Usage:
    python shiki_daemon.py
    python shiki_daemon.py --no-auto-start  (no auto-start)
"""

import sys, os, json, time, threading, subprocess, functools
import socket, signal, webbrowser, hashlib
import http.server
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
os.chdir(WORKSPACE)

# Config
import yaml
with open(os.path.join(WORKSPACE, "config.yaml"), "r", encoding="utf-8-sig") as f:
    CFG = yaml.safe_load(f)

LLAMA_EXE = CFG["llama_exe"]
LLAMA_MODEL = CFG["llama_model"]
LLAMA_PORT = int(CFG.get("llama_port", 8080))
LLAMA_LOG = os.path.join(CFG.get("llama_log_dir", WORKSPACE), "llama-err.log")
# 模型名从 config.yaml 读取：优先 llama_model_name，否则取 llama_model 路径 basename
import os as _os
LLAMA_MODEL_NAME = CFG.get("llama_model_name", "") or _os.path.basename(CFG.get("llama_model", "local-model"))
# OpenAI 兼容 API 的本地模型 id（默认 local/<模型名>，可通过 config.yaml 自定义）
LOCAL_MODEL_ID = CFG.get("llama_model_id", "local/" + LLAMA_MODEL_NAME)
LIVE2D_DIR = os.path.join(WORKSPACE, "live2d")
EMBED_SCRIPT = os.path.join(WORKSPACE, "skills", "shared", "embedding_server.py")
BRIDGE_SCRIPT = os.path.join(WORKSPACE, "artemis_bridge.py")
HEADROOM_SCRIPT = os.path.join(WORKSPACE, "artemis_headroom_proxy.py")
WEBCHAT_DIR = os.path.join(WORKSPACE, "web-chat")
DASHBOARD_PORT = 19260
WEBCHAT_PORT = 19270

# ── API 超时和重试配置 ──
REQUEST_TIMEOUT = int(CFG.get("api_timeout", 180))  # 默认 180s
REQUEST_MAX_RETRIES = int(CFG.get("api_max_retries", 2))  # 默认重试 2 次
LLAMA_BASE_URL = f"http://127.0.0.1:{LLAMA_PORT}/v1"

# ── 并发控制：限制同时请求数 ──
import threading
_llama_semaphore = threading.Semaphore(int(CFG.get("llama_max_concurrent", 3)))  # 默认最多 3 个并发

# ── Mem0 per-character write counters ───────────────────────
_mem0_write_counters = {}  # {character_id: count}
_mem0_write_lock = threading.Lock()

# ── World Book per-entry storage (new format) ────────────────
# In-memory store of per-entry worldbook entries.
# Each entry: { id, key, content, priority(0-4), enabled, source, updatedAt }
_wb_entries = []  # list of entry dicts
_wb_entries_lock = threading.Lock()

# ── Llama reasoning state tracking ─────────────────────────
# 每次 set-rea 时从实际进程读取 rea 状态，避免与脚本重启不同步
_llama_rea_state = "off"  # fallback only; actual state is checked on demand

def _get_actual_rea_state():
    """检查当前运行 llama-server 的 -rea 实际值"""
    try:
        _proc = __import__("subprocess").run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='llama-server.exe'\" | Select-Object -ExpandProperty CommandLine"],
            capture_output=True, text=True, timeout=5
        )
        if _proc.returncode == 0 and _proc.stdout.strip():
            _cmdline = _proc.stdout.strip()
            if "-rea on" in _cmdline or "-rea 1" in _cmdline:
                return "on"
            elif "-rea off" in _cmdline or "-rea 0" in _cmdline:
                return "off"
    except Exception:
        pass
    # 如果进程不在运行或无法检测，返回当前缓存值
    return _llama_rea_state

# ── DeepSeek V4 thinking-mode markers ───────────────────────
# Thinking-mode markers injected at end of first user message.
# Qwen/DeepSeek use reasoning_content field (not <think> tags), so avoid mentioning <think>.
# From: https://github.com/victorchen96/deepseek_v4_rolepaly_instruct (adapted)
_THINKING_MARKERS = {
    "immersive": (
        "\n\n【角色沉浸要求】在你的推理过程中，请遵守以下规则：\n"
        "1. 请以角色第一人称进行内心独白，用括号包裹内心活动，例如\"（心想：……）\"或\"(内心OS：……)\"\n"
        "2. 用第一人称描写角色的内心感受，例如\"我心想\"\"我觉得\"\"我暗自\"等\n"
        "3. 思考内容应沉浸在角色中，通过内心独白分析剧情和规划回复"
    ),
    "analytic": (
        "\n\n【思维模式要求】在你的推理过程中，请遵守以下规则：\n"
        "1. 禁止使用圆括号包裹内心独白，例如\"（心想：……）\"或\"(内心OS：……)\"，所有分析内容直接陈述即可\n"
        "2. 禁止以角色第一人称描写内心活动，例如\"我心想\"\"我觉得\"\"我暗自\"等，请用分析性语言替代\n"
        "3. 思考内容应聚焦于剧情走向分析和回复内容规划，不要在思考中进行角色扮演式的内心戏表演"
    ),
    "godview": (
        "\n\n【上帝视角要求】在你的推理过程中，请遵守以下规则：\n"
        "1. 以第三人称上帝视角进行思考，例如\"根据场景分析，角色A当前……\"或\"从剧情发展来看……\"\n"
        "2. 客观分析角色动机、环境背景、未来剧情走向，不代入任何角色第一人称\n"
        "3. 可以将思考分为【剧情背景】【角色动机】【回复策略】三段式结构\n"
        "4. 语气保持冷静克制，类似导演评论或编剧笔记风格"
    ),
}


def _get_thinking_marker(mode):
    """Return the thinking-mode marker string for DeepSeek V4."""
    return _THINKING_MARKERS.get(mode)


def _inject_thinking_marker(messages, marker):
    """Inject thinking-mode marker at the end of the first user message.
    This matches the training injection position for DeepSeek V4."""
    if not marker:
        return messages
    result = list(messages)
    for i, msg in enumerate(result):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            # Append marker if not already present
            if marker not in content:
                result[i] = {**msg, "content": content + marker}
            break  # only first user message
    return result


def _mem0_search_context(character_id, query, limit=5):
    """Search mem0 Qdrant and return formatted context string for system prompt."""
    try:
        # Import from skills/mem0-bridge (standalone), fallback skills/shared
        if WORKSPACE not in sys.path:
            sys.path.insert(0, WORKSPACE)
        try:
            from skills.mem0_bridge.mem0_bridge import search_mem0_qdrant, CHARACTERS
        except ImportError:
            from skills.shared.mem0_bridge import search_mem0_qdrant, CHARACTERS
        if character_id not in CHARACTERS:
            return None
        results = search_mem0_qdrant(character_id, query, limit=limit)
        if not results:
            return None
        # Filter low-score results
        relevant = [r for r in results if r.get("score", 0) > 0.3]
        if not relevant:
            return None
        lines = [
            "\n\n## 长期记忆（Mem0）\n",
            "以下是与你、与当前对话相关的长期记忆，请自然地融入对话中，不必逐条复述：\n",
        ]
        for r in relevant:
            score = r.get("score", 0)
            mem = r["memory"]
            if score > 0.7:
                lines.append(f"- [高相关] {mem}")
            elif score > 0.5:
                lines.append(f"- {mem}")
            else:
                lines.append(f"- (弱相关) {mem}")
        return "\n".join(lines)
    except Exception as e:
        print(f"[mem0] search error: {e}", file=sys.stderr, flush=True)
        return None


def _set_llama_rea(rea_mode):
    """Restart llama-server with a different -rea setting."""
    global _llama_rea_state
    # 先检查实际运行状态，避免缓存不同步
    actual = _get_actual_rea_state()
    if actual == rea_mode:
        _llama_rea_state = actual  # sync cache
        return
    import subprocess, time
    print(f"[DAEMON] Switching llama -rea {_llama_rea_state} -> {rea_mode}...", flush=True)
    # Use llama_lifecycle's stop + start
    lifecycle = os.path.join(WORKSPACE, "skills", "shared", "llama_lifecycle.py")
    subprocess.run([PYTHON, lifecycle, "stop", str(LLAMA_PORT)], timeout=60)
    for _ in range(30):
        if not is_port_open(LLAMA_PORT):
            break
        time.sleep(0.5)
    subprocess.run([PYTHON, lifecycle, "start", str(LLAMA_PORT),
                    LLAMA_EXE, LLAMA_MODEL,
                    os.path.dirname(LLAMA_LOG),
                    rea_mode], timeout=300)
    for _ in range(180):
        if is_port_open(LLAMA_PORT):
            _llama_rea_state = rea_mode
            print(f"[DAEMON] llama ready with -rea {rea_mode}", flush=True)
            return
        time.sleep(0.5)
    print(f"[DAEMON] WARNING: llama did not come back with -rea {rea_mode}", flush=True)


def _mem0_write_context(character_id, messages):
    """Extract important facts from recent conversation and write to mem0.
    Uses a lightweight keyword-based extraction (no extra LLM call)."""
    try:
        if WORKSPACE not in sys.path:
            sys.path.insert(0, WORKSPACE)
        try:
            from skills.mem0_bridge.mem0_bridge import add_memory, CHARACTERS
        except ImportError:
            from skills.shared.mem0_bridge import add_memory, CHARACTERS
        if character_id not in CHARACTERS:
            return
        # Extract last few exchanges
        recent = messages[-6:]  # last 3 pairs
        facts = _extract_facts_from_messages(recent)
        for fact in facts:
            add_memory(character_id, fact)
            print(f"[mem0] wrote for {character_id}: {fact[:60]}...", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[mem0] write error: {e}", file=sys.stderr, flush=True)


def _extract_facts_from_messages(messages):
    """Simple keyword-based fact extraction from conversation messages.
    Looks for patterns like '我叫...', '我喜欢...', '我的...是...', etc."""
    facts = []
    import re
    patterns = [
        (r'我(?:的名字)?(?:叫|是)([^，。,.]{1,30})', '用户名字'),
        (r'我(?:喜欢|爱|讨厌|想)([^，。,.]{1,60})', '用户偏好'),
        (r'我(?:的|在|是|有)([^，。,.]{2,60})', '用户信息'),
        (r'(?:记住|别忘了)[：:]?(.{3,80})', '待记忆'),
        (r'(?:今天|昨天|上周|刚刚)(.{3,80})', '事件'),
    ]
    seen_hashes = set()
    for msg in messages:
        if msg.get("role") != "user":
            continue
        text = msg.get("content", "")
        for pattern, category in patterns:
            for match in re.finditer(pattern, text):
                fact = match.group(1).strip()
                if len(fact) < 3 or len(fact) > 80:
                    continue
                # Dedup
                h = hashlib.md5(fact.encode()).hexdigest()
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
                full_fact = f"{category}: {fact}"
                facts.append(full_fact)
    return facts


def _maybe_write_mem0(character_id, messages, write_interval):
    """Check counter and trigger mem0 write if interval reached."""
    with _mem0_write_lock:
        current = _mem0_write_counters.get(character_id, 0) + 1
        _mem0_write_counters[character_id] = current
        should_write = (current % write_interval == 0)
    if should_write:
        t = threading.Thread(target=_mem0_write_context, args=(character_id, messages), daemon=True)
        t.start()
        print(f"[mem0] triggered write for {character_id} (round {current})", file=sys.stderr, flush=True)


SERVICES = [
    {"name": "llama-server",    "port": LLAMA_PORT,  "enabled": True},
    {"name": "Embedding",       "port": 9999,         "enabled": True},
    {"name": "Headroom Proxy",  "port": 19251,        "enabled": True},
    {"name": "Live2D Bridge",   "port": 19200,        "enabled": True},
    {"name": "Artemis Bridge",  "port": 19250,        "enabled": True},
    {"name": "OpenClaw Gateway","port": 18789,        "enabled": True},
    {"name": "Task Board",      "port": 19280,        "enabled": True,  "note": "AgentRQ-style task queue UI"},
    {"name": "Llama Debugger",  "port": 8765,         "enabled": True,  "note": "llama-server parameter tuning"},
    {"name": "Claude Code MCP", "port": None,          "enabled": False, "note": "Run claude-code.ps1 manually"},
    {"name": "WebChat",         "port": 19270,        "enabled": True},
]

AUTO_START = "--no-auto-start" not in sys.argv
NO_LLAMA = "--no-llama" in sys.argv

# ---- Helpers ----

def find_python():
    for py in ["python", "python3", "py"]:
        try:
            r = subprocess.run([py, "--version"], capture_output=True, timeout=3)
            if r.returncode == 0: return py
        except Exception:
            pass
    return "python"

PYTHON = find_python()

def is_port_open(port):
    try:
        sock = socket.create_connection(("127.0.0.1", port), timeout=1)
        sock.close()
        return True
    except Exception:
        return False

def kill_process(name):
    try:
        subprocess.run(["taskkill", "/F", "/IM", name], capture_output=True, timeout=5)
    except: pass

def start_llama():
    if NO_LLAMA:
        return "skipped (--no-llama)"
    if is_port_open(LLAMA_PORT):
        return "already running"
    kill_process("llama-server.exe")
    time.sleep(1)

    # 统一参数解析：从 config.yaml + model_profiles 读取（按模型文件名匹配预设）
    try:
        from skills.shared.llama_config import resolve_llama_params, build_llama_args
        _params = resolve_llama_params(CFG)
        args = build_llama_args(_params)
        if _params.get("_profile_name"):
            print(f"[LLAMA] profile: {_params['_profile_name']}", flush=True)
        if any(a == "--spec-type" for a in args):
            print("[LLAMA] MTP model detected: --spec-type draft-mtp enabled", flush=True)
    except Exception as _e:
        # 降级：老逻辑（llama 区块 + MTP 自动检测）
        print(f"[LLAMA] llama_config resolve failed ({_e}), using legacy args", flush=True)
        llm_cfg = CFG.get("llama", {})
        ctx = llm_cfg.get("context", 150000)
        batch = llm_cfg.get("batch_size", 2048)
        ubatch = llm_cfg.get("ubatch_size", 1024)
        threads = llm_cfg.get("threads", 24)
        ctk = llm_cfg.get("ctk", "q8_0")
        ctv = llm_cfg.get("ctv", "q8_0")
        ngl = llm_cfg.get("ngl", 41)
        cache_ram = llm_cfg.get("cache_ram", 3000)
        args = [
            LLAMA_EXE, "-m", LLAMA_MODEL,
            "-c", str(ctx), "--flash-attn", "on",
            "-ctk", ctk, "-ctv", ctv,
            "--no-mmap", "--cpu-moe",
            "--batch-size", str(batch), "--ubatch-size", str(ubatch),
            "--threads", str(threads),
            "-rea", "off", "--jinja", "--reasoning-preserve",
            "--cache-ram", str(cache_ram),
            "-ngl", str(ngl),
            "--parallel", "1", "--kv-unified",
            "--port", str(LLAMA_PORT), "--timeout", "600",
        ]
        _model_name_lower = (CFG.get("llama_model_name", "") or os.path.basename(LLAMA_MODEL)).lower()
        spec_draft_n_max = llm_cfg.get("spec_draft_n_max", 1)
        if "mtp" in _model_name_lower:
            print(f"[LLAMA] MTP model detected: adding --spec-type draft-mtp --spec-draft-n-max {spec_draft_n_max}", flush=True)
            args += ["--spec-type", "draft-mtp", "--spec-draft-n-max", str(spec_draft_n_max)]

    os.makedirs(os.path.dirname(LLAMA_LOG), exist_ok=True)
    with open(LLAMA_LOG, "w") as log:
        subprocess.Popen(args, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)

    # Wait for ready
    for _ in range(150):
        if is_port_open(LLAMA_PORT):
            return "ready"
        time.sleep(2)
    return "timeout"

def start_embedding():
    if is_port_open(9999):
        return "already running"
    if not os.path.isfile(EMBED_SCRIPT):
        return "script not found"
    subprocess.Popen([PYTHON, EMBED_SCRIPT], creationflags=subprocess.CREATE_NO_WINDOW)
    for _ in range(20):
        if is_port_open(9999): return "ready"
        time.sleep(2)
    return "timeout"

def start_live2d():
    if is_port_open(19200):
        return "already running"
    mjs = os.path.join(LIVE2D_DIR, "live2d-bridge.mjs")
    if not os.path.isfile(mjs):
        return "script not found"
    subprocess.Popen(["node", "live2d-bridge.mjs"], cwd=LIVE2D_DIR, creationflags=subprocess.CREATE_NO_WINDOW)
    for _ in range(5):
        if is_port_open(19200): return "ready"
        time.sleep(2)
    return "timeout"

def _get_openclaw_json_path():
    """返回用户 openclaw.json 路径（跨平台）。"""
    home = os.path.expanduser("~")
    return os.path.join(home, ".openclaw", "openclaw.json")


HEADROOM_ROUTES_PATH = os.path.join(os.path.expanduser("~"), ".openclaw", "headroom_routes.json")


def _load_headroom_routes():
    """读取 sidecar 路由映射文件。"""
    try:
        with open(HEADROOM_ROUTES_PATH, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_headroom_routes(routes: dict):
    """写入 sidecar 路由映射文件。"""
    try:
        os.makedirs(os.path.dirname(HEADROOM_ROUTES_PATH), exist_ok=True)
        with open(HEADROOM_ROUTES_PATH, "w", encoding="utf-8") as f:
            json.dump(routes, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[headroom] failed to save routes: {e}", flush=True)


def ensure_openclaw_headroom_provider():
    """
    检测 headroom proxy (19251) 是否在线，若在线则在 openclaw.json 中
    新增 local-llama provider（baseUrl=19251），并将所有现有 provider 的
    模型复制到 local-llama 下，使它们也走 headroom+mem0 管线。

    原则：只加不改。
      - 现有 provider（zai 等）原封不动
      - 新增 local-llama provider，baseUrl 指向 19251
      - local-llama 下挂载：llama-local（本地）+ 所有云端模型的副本
      - headroom proxy 根据 model id 路由：llama-local → 8080，其他 → sidecar

    幂等：已配置则跳过。
    如果 19251 未开或 openclaw.json 不存在，静默跳过。
    """
    if not is_port_open(19251):
        return False

    cfg_path = _get_openclaw_json_path()
    if not os.path.isfile(cfg_path):
        return False

    try:
        with open(cfg_path, "r", encoding="utf-8-sig") as f:
            oc_cfg = json.load(f)
    except Exception:
        return False

    providers = oc_cfg.setdefault("models", {}).setdefault("providers", {})
    if not providers:
        return False

    HEADROOM_BASE = "http://127.0.0.1:19251/v1"
    routes = _load_headroom_routes()
    changed = False

    # 收集所有非 local-llama provider 的模型 + baseUrl
    cloud_models = []
    for prov_id, prov_cfg in providers.items():
        if prov_id in ("local-llama", "local"):
            continue
        orig_url = prov_cfg.get("baseUrl", "")
        if not orig_url or "19251" in orig_url:
            continue
        # 保存 provider 的原始 baseUrl 到 sidecar
        routes[prov_id] = orig_url
        # 复制该 provider 的模型
        for m in prov_cfg.get("models", []):
            model_id = m.get("id", "")
            if not model_id:
                continue
            # 跳过已存在的
            if any(em["id"] == model_id for em in cloud_models):
                continue
            model_copy = dict(m)
            model_copy["name"] = f"{m.get('name', model_id)} via Headroom"
            cloud_models.append(model_copy)

    # 本地模型始终放第一个
    local_model = {
        "id": "llama-local",
        "name": "Local Llama (Headroom+Mem0)",
        "contextWindow": int(CFG.get("llama", {}).get("context", 150000)),
        "maxTokens": 12000,
        "reasoning": False,
        "compat": {
            "supportsReasoningEffort": False,
            "supportsTools": False,
            "supportsTemperature": True,
            "requiresStringContent": True,
        },
    }
    routes["llama-local"] = f"http://127.0.0.1:{LLAMA_PORT}/v1"

    all_models = [local_model] + cloud_models

    # 检查 local-llama provider 是否已存在且配置一致
    existing = providers.get("local-llama")
    if existing and "19251" in existing.get("baseUrl", ""):
        existing_ids = {m.get("id") for m in existing.get("models", [])}
        needed_ids = {m["id"] for m in all_models}
        if existing_ids == needed_ids:
            # 已配置且模型列表一致，只需确保 sidecar 是最新的
            _save_headroom_routes(routes)
            return False  # 无需修改

    # 创建或更新 local-llama provider
    providers["local-llama"] = {
        "baseUrl": HEADROOM_BASE,
        "api": "openai-completions",
        "apiKey": "***",
        "auth": "api-key",
        "timeoutSeconds": 300,
        "models": all_models,
    }
    changed = True
    print(f"[headroom] local-llama provider: {len(all_models)} models via {HEADROOM_BASE}", flush=True)

    if not changed:
        return False

    try:
        _save_headroom_routes(routes)
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(oc_cfg, f, indent=2, ensure_ascii=False)
        print(f"[headroom] patched {cfg_path} (local-llama added, existing providers untouched)", flush=True)
        return True
    except Exception as e:
        print(f"[headroom] failed to patch openclaw.json: {e}", flush=True)
        return False


def start_headroom():
    if is_port_open(19251):
        # 已在运行，仍确保 openclaw 配置同步
        ensure_openclaw_headroom_provider()
        return "already running"
    if not os.path.isfile(HEADROOM_SCRIPT):
        return "script not found"

    proc = subprocess.Popen(
        [PYTHON, HEADROOM_SCRIPT, "--port", "19251"],
        cwd=WORKSPACE,
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(15):
        if is_port_open(19251):
            # headroom proxy 就绪 → 自动配置 openclaw 走 19251
            ensure_openclaw_headroom_provider()
            return "ready"
        if proc.poll() is not None:
            return f"exited with code {proc.returncode}"
    return "timeout"

def start_bridge():
    if is_port_open(19250):
        return "already running"
    if not os.path.isfile(BRIDGE_SCRIPT):
        return "script not found"

    proc = subprocess.Popen(
        [PYTHON, BRIDGE_SCRIPT, "--port", "19250"],
        cwd=WORKSPACE,
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Flask takes a few seconds to bind
    for _ in range(15):
        if is_port_open(19250): return "ready"
        if proc.poll() is not None:
            return f"exited with code {proc.returncode}"
        time.sleep(2)
    return "timeout"

def start_llama_debugger():
    if is_port_open(8765):
        return "already running"
    server_path = os.path.join(WORKSPACE, "skills", "llama_debugger", "server.py")
    if not os.path.isfile(server_path):
        return "script not found"
    subprocess.Popen(
        [PYTHON, server_path, "8765"],
        cwd=os.path.join(WORKSPACE, "skills", "llama_debugger"),
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(5):
        if is_port_open(8765):
            return "ready"
        time.sleep(1)
    return "timeout"

def start_task_board():
    TASK_PORT = 19280
    if is_port_open(TASK_PORT):
        return "already running"
    api_script = os.path.join(WORKSPACE, ".claude", "task_board_api.py")
    if not os.path.exists(api_script):
        return "task_board_api.py not found"
    try:
        subprocess.Popen([PYTHON, api_script], cwd=WORKSPACE,
                         creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        for _ in range(3):
            if is_port_open(TASK_PORT): return "ready"
            time.sleep(1)
        return "timeout"
    except Exception as e:
        return f"error: {e}"

def start_webchat():
    if is_port_open(WEBCHAT_PORT):
        return "already running"
    if not os.path.isdir(WEBCHAT_DIR):
        return "web-chat directory not found"
    import http.server
    # Pass directory to the handler instead of os.chdir() — chdir changes the
    # process-wide cwd and races with other threads.
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=WEBCHAT_DIR)
    threading.Thread(target=lambda: http.server.HTTPServer(
        ("127.0.0.1", WEBCHAT_PORT),
        handler
    ).serve_forever(), daemon=True).start()
    for _ in range(3):
        if is_port_open(WEBCHAT_PORT): return "ready"
        time.sleep(1)
    return "timeout"

def start_gateway():
    if is_port_open(18789):
        return "already running"

    # 确保 headroom proxy 端口配置已注入 openclaw.json（如果 19251 在线）
    ensure_openclaw_headroom_provider()

    import shutil

    # 读取配置
    wspace = os.path.expandvars(CFG.get("workspace", os.path.expandvars(r"%USERPROFILE%\.openclaw\workspace")))
    openclaw_dir = os.path.dirname(wspace)  # .openclaw 目录
    gateway_cmd_cfg = CFG.get("gateway_cmd", "")
    gateway_cmd = os.path.expandvars(gateway_cmd_cfg) if gateway_cmd_cfg else ""
    if not gateway_cmd or not os.path.isfile(gateway_cmd):
        gateway_cmd = os.path.join(openclaw_dir, "gateway.cmd")

    if os.path.isfile(gateway_cmd):
        print(f"[daemon]   Starting gateway via cmd: {gateway_cmd}")
        subprocess.Popen(
            ["cmd.exe", "/c", gateway_cmd],
            cwd=openclaw_dir,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    else:
        # 降级：直接 node 启动，从 workspace 推算 dist 路径
        node_exe = CFG.get("node_exe", "") or shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
        openclaw_git = os.path.join(openclaw_dir, "openclaw-git", "dist", "index.js")
        npm_dist = os.path.expandvars(r"%APPDATA%\npm\node_modules\openclaw\dist\index.js")
        gateway_js = openclaw_git if os.path.isfile(openclaw_git) else npm_dist
        
        # 验证所有路径
        if not os.path.isfile(node_exe):
            return f"node.exe not found: {node_exe}"
        if not os.path.isfile(gateway_js):
            return f"gateway dist not found: {gateway_js}"
        if not os.path.isdir(openclaw_dir):
            return f"openclaw_dir not a directory: {openclaw_dir}"
        
        print(f"[daemon]   Starting gateway directly: {node_exe} {gateway_js} gateway --port 18789")
        
        # 输出重定向到日志文件而不是 DEVNULL
        gateway_log = os.path.join(WORKSPACE, "gateway.log")
        with open(gateway_log, "a", encoding="utf-8") as log_f:
            subprocess.Popen(
                [node_exe, gateway_js, "gateway", "--port", "18789"],
                cwd=openclaw_dir,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=log_f,
                stderr=log_f,
            )

    # Gateway 启动慢（编译/迁移），等最多 120 秒
    for _ in range(60):
        if is_port_open(18789):
            return "ready"
        time.sleep(2)
    return "timeout"

def stop_all():
    """Stop all managed services"""
    try:
        subprocess.run([PYTHON, os.path.join(WORKSPACE, "shutdown_all.py")], capture_output=True, text=True, timeout=30)
        return "All services stopped"
    except Exception as e:
        return f"Error: {e}"

SERVICE_STARTERS = {
    "llama-server": start_llama,
    "Embedding": start_embedding,
    "Headroom Proxy": start_headroom,
    "Live2D Bridge": start_live2d,
    "Artemis Bridge": start_bridge,
    "OpenClaw Gateway": start_gateway,
    "Task Board": start_task_board,
    "Llama Debugger": start_llama_debugger,
    "WebChat": start_webchat,
}

SERVICE_KILLERS = {
    "llama-server": 8080,
    "Embedding": 9999,
    "Headroom Proxy": 19251,
    "Live2D Bridge": 19200,
    "Artemis Bridge": 19250,
    "OpenClaw Gateway": 18789,
    "Task Board": 19280,
    "Llama Debugger": 8765,
    "WebChat": None,  # WebChat runs in daemon thread, can't kill separately
}


def _kill_by_port(port, wait_sec=3):
    """Kill the process owning a local port via netstat + taskkill by PID.
    Never uses taskkill /IM so it can't take down unrelated processes
    (e.g. other python/node instances, or the daemon itself)."""
    if not is_port_open(port):
        return "not running"
    pid = None
    try:
        result = subprocess.run(["netstat", "-ano"], capture_output=True, timeout=5,
                                encoding="utf-8", errors="replace")
        for line in result.stdout.splitlines():
            parts = line.split()
            # Only LISTENING rows (state col) on the local addr (col 2);
            # skip TIME_WAIT/ESTABLISHED rows whose local port is a client port.
            if (len(parts) >= 5 and parts[0].upper() == "TCP"
                    and parts[3].upper() == "LISTENING"
                    and parts[1].endswith(f":{port}")
                    and parts[-1].isdigit() and int(parts[-1]) > 0):
                pid = int(parts[-1])
                break
    except Exception:
        pass
    if pid:
        try:
            subprocess.run(["taskkill", "/f", "/pid", str(pid)], capture_output=True, timeout=5)
        except Exception:
            pass
    else:
        # Fallback: PowerShell per-port kill (still PID-scoped, no /IM)
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | "
                 "ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"],
                capture_output=True, text=True, timeout=8)
        except Exception:
            pass
    for _ in range(wait_sec * 2):
        time.sleep(0.5)
        if not is_port_open(port):
            return f"stopped (port {port})"
    return f"STILL RUNNING (port {port})"

# ---- Daemon core ----

class ShikiDaemon:
    def __init__(self):
        self.running = True

    def start_all_services(self):
        """Start all enabled services in order"""
        results = {}
        for svc in SERVICES:
            if not svc["enabled"]: continue
            name = svc["name"]
            if NO_LLAMA and name == "llama-server":
                results[name] = "skipped (--no-llama)"
                continue
            print(f"[daemon] Starting {name}...")
            fn = SERVICE_STARTERS.get(name)
            if fn:
                res = fn()
                results[name] = res
                print(f"[daemon]   {name}: {res}")
            else:
                results[name] = "no handler"
                print(f"[daemon]   {name}: no handler")
        return results

    def get_status(self):
        """Return current status of all services"""
        status = []
        for svc in SERVICES:
            online = is_port_open(svc["port"])
            status.append({
                "name": svc["name"],
                "port": svc["port"],
                "online": online,
                "enabled": svc["enabled"],
            })
        return status

    def stop(self):
        self.running = False


# ================================================================
# Dashboard HTTP Server
# ================================================================
daemon_instance = None

DASHBOARD_PATH = os.path.join(WORKSPACE, "shiki_dashboard.html")

def _read_dashboard():
    if os.path.isfile(DASHBOARD_PATH):
        with open(DASHBOARD_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Dashboard file not found</h1>"


# ================================================================
# Character profile scanning (skills/harem/)
# ================================================================
HAREM_DIR = os.path.join(WORKSPACE, "skills", "harem")

CHARACTER_FALLBACKS = {
    "natsume": [
        "嗯，知道了。",
        "这样说啊...我会记住的。",
        "笨蛋，这么晚了还不睡。",
        "哼，算你有心。",
        "...我在听。",
        "知道了，别一直说。",
        "偶尔也让我主动一下嘛。",
        "你啊，总是这样。",
        "好，陪你一会儿。",
        "别太勉强自己。",
    ],
    "sakura": [
        "...嗯。",
        "大丈夫、私がいる。",
        "無理しないで。",
        "ちゃんと見て。",
        "君は...本当にバカだな。",
        "...少し嬉しい。",
        "休んで。今すぐ。",
        "少し寂しい...なんてな。",
        "うん、わかった。",
        "そばにいる。",
    ],
    "enola": [
        "我在呢，有什么事想说吗？",
        "今天辛苦了，好好休息吧。",
        "嗯，我能理解你的感受。",
        "没关系，慢慢来。",
        "我一直都在这里。",
        "需要我陪你聊聊天吗？",
        "能和你在一起，我很开心。",
        "不要一个人扛着，有我在。",
    ],
    "atori": [
        "哇，好有趣！",
        "诶诶，这是什么意思？",
        "主人主人，快告诉我更多！",
        "嘻嘻，我明白了！",
        "嗯嗯，继续说呀~",
        "那个...能再说一次吗？",
        "我也想试试看！",
        "主人今天心情怎么样？",
    ],
}

CHARACTER_TAGS = {
    "natsume": ["高岭之花", "小娇妻感", "毒舌", "独占欲"],
    "sakura": ["冷娇", "守护者", "最强战力", "责任感"],
    "enola": ["温柔", "治愈", "忠诚", "陪伴"],
    "atori": ["元气", "机器人", "好奇心", "直率"],
}

CHARACTER_SOURCE = {
    "natsume": "星光咖啡蝶与死神之馆",
    "sakura": "Dimension Lovers!!",
    "enola": "原创角色",
    "atori": "ATRI -My Dear Moments-",
}

CHARACTER_ACCENT = {
    "natsume": "#d4787a",
    "sakura": "#7e9ec8",
    "enola": "#c4a882",
    "atori": "#6eb5c0",
}

CHARACTER_TTS = {
    "natsume": {"lang": "ja", "mood": "casual"},
    "sakura": {"lang": "ja", "mood": "tsundere"},
    "enola": {"lang": "ja", "mood": "romantic"},
    "atori": {"lang": "ja", "mood": "casual"},
}

# ================================================================
# Fallback paint prompts — used when LLM is offline (ComfyUI needs VRAM)
# ================================================================
FALLBACK_PROMPTS = {
    "natsume": {
        "prompt": "masterpiece, best quality, highly detailed, (shiki natsume:1.2), 1girl, solo, long black hair, yellow eyes, cold expression, black dress, elegant, cinematic lighting, beautiful detailed background, soft lighting, japanese aesthetic, (atmosphere:0.8)",
        "negative": "worst quality, bad quality, low quality, blurry, lowres, bad anatomy, extra fingers, missing fingers, extra limbs, deformed, disfigured, watermark, text, signature, jpeg artifacts, ugly, censored",
    },
    "sakura": {
        "prompt": "masterpiece, best quality, highly detailed, (yono sakura:1.2), 1girl, solo, long silver hair, pink-tipped hair, wavy hair, light blue eyes, white and black school uniform, blue skirt, yellow necktie, moonlight, night sky, starry sky, cinematic lighting, detailed face, (atmosphere:0.8)",
        "negative": "worst quality, bad quality, low quality, blurry, lowres, bad anatomy, extra fingers, missing fingers, extra limbs, deformed, disfigured, watermark, text, signature, jpeg artifacts, ugly, censored",
    },
    "atori": {
        "prompt": "masterpiece, best quality, highly detailed, (atri:1.2), 1girl, solo, silver hair, long hair, ruby red eyes, bright smile, mechanical ear accessories, white dress, flowing skirt, barefoot, seaside sunset, golden hour, warm light, detailed face, (atmosphere:0.8)",
        "negative": "worst quality, bad quality, low quality, blurry, lowres, bad anatomy, extra fingers, missing fingers, extra limbs, deformed, disfigured, watermark, text, signature, jpeg artifacts, ugly, censored",
    },
    "enola": {
        "prompt": "masterpiece, best quality, highly detailed, 1girl, solo, brown hair, gentle smile, casual clothes, soft lighting, warm atmosphere, cozy room, beautiful detailed background, detailed face, (atmosphere:0.8)",
        "negative": "worst quality, bad quality, low quality, blurry, lowres, bad anatomy, extra fingers, missing fingers, extra limbs, deformed, disfigured, watermark, text, signature, jpeg artifacts, ugly, censored",
    },
}

def _make_fallback_prompt(character_id, char_name, messages):
    """Generate a prompt without LLM when llama is offline.
    Returns a dict suitable for json response: with 'prompt' and 'negative' keys.
    Tries character-specific preset; falls back to conversation context."""
    fb = FALLBACK_PROMPTS.get(character_id)
    if fb:
        return {"prompt": fb["prompt"], "negative": fb["negative"]}
    # Generic fallback
    return {
        "prompt": f"masterpiece, best quality, highly detailed, 1girl, solo, {char_name}, beautiful detailed background, cinematic lighting, soft lighting, (atmosphere:0.8)",
        "negative": "worst quality, bad quality, low quality, blurry, lowres, bad anatomy, extra fingers, missing fingers, extra limbs, deformed, disfigured, watermark, text, signature, jpeg artifacts, ugly, censored",
    }

def _parse_identity_md(path):
    """Parse IDENTITY.md to extract name, emoji, creature, vibe."""
    result = {}
    if not os.path.isfile(path):
        return result
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                # Support both "- Key: value" (OpenClaw format) and "* **Key:** value"
                if stripped.startswith("- "):
                    stripped = stripped[2:]
                elif stripped.startswith("* **") and ":" in stripped:
                    idx = stripped.index(":")
                    stripped = stripped[2:idx] + stripped[idx:]
                    stripped = stripped.replace("**", "").strip()
                else:
                    continue
                if ":" not in stripped:
                    continue
                key, _, value = stripped.partition(":")
                key = key.strip().lower()
                value = value.strip()
                if not value:
                    continue
                # Skip placeholders
                if value.lower() in ("随意", "pick something you like", "ai? robot? familiar? ghost in the machine? something weirder?"):
                    continue
                if key in ("name", "emoji", "creature", "creator", "vibe"):
                    # Normalize creator -> creature
                    if key == "creator":
                        result["creature"] = value
                    else:
                        result[key] = value
    except Exception:
        pass
    return result

def _load_harem_characters():
    """Scan skills/harem/ and return character profiles."""
    characters = []
    if not os.path.isdir(HAREM_DIR):
        return characters
    for entry in sorted(os.listdir(HAREM_DIR)):
        char_dir = os.path.join(HAREM_DIR, entry)
        if not os.path.isdir(char_dir):
            continue
        char_id = entry.lower()
        identity_path = os.path.join(char_dir, "IDENTITY.md")
        parsed = _parse_identity_md(identity_path)
        name = parsed.get("name", entry.capitalize())
        # Clean name: remove parenthetical English
        import re
        name_cn = re.sub(r"\s*[（(][^)）]*[)）]", "", name).strip() or entry.capitalize()
        name_en = re.search(r"[（(]([^)）]+)[)）]", name)
        name_en = name_en.group(1) if name_en else entry.capitalize()
        # Icon: use first letter of romanized id (e.g. n/s/e/a)
        icon = entry[0].lower()
        characters.append({
            "id": char_id,
            "name": name_cn,
            "nameEn": name_en,
            "icon": icon,
            "emoji": parsed.get("emoji", ""),
            "creature": parsed.get("creature", ""),
            "vibe": parsed.get("vibe", ""),
            "persona": parsed.get("creature", "") or parsed.get("vibe", ""),
            "personaNote": parsed.get("vibe", ""),
            "tags": CHARACTER_TAGS.get(char_id, ["Imported"]),
            "source": CHARACTER_SOURCE.get(char_id, "原创角色"),
            "accent": CHARACTER_ACCENT.get(char_id, "#c4a882"),
            "ttsLang": CHARACTER_TTS.get(char_id, {}).get("lang", "ja"),
            "ttsMood": CHARACTER_TTS.get(char_id, {}).get("mood", "casual"),
            "fallbackReplies": CHARACTER_FALLBACKS.get(char_id, ["I'm here."]),
        })
    return characters


def _build_system_prompt(character_id):
    """Build system prompt from character SOUL.md + IDENTITY.md + USER.md.
    AGENTS.md is intentionally excluded — it's for the Gateway agent, not the chat model."""
    parts = []

    # 0. World Book (global lore, injected before character)
    #    New entries-based format: each entry has key, content, priority(0-4), enabled
    wb_entries = []
    with _wb_entries_lock:
        wb_entries = list(_wb_entries)

    # Filter: only enabled entries with priority >= 1
    enabled_entries = [e for e in wb_entries if e.get("enabled") and e.get("priority", 0) >= 1]
    # Sort by priority descending (high priority first)
    enabled_entries.sort(key=lambda e: e.get("priority", 0), reverse=True)

    if enabled_entries:
        lines = ["# WORLD BOOK / LORE"]
        for entry in enabled_entries:
            key = entry.get("key", "")
            content = entry.get("content", "")
            priority = entry.get("priority", 2)
            if key and content:
                # Priority label: [E]ssential / [H]igh / [M]edium / [L]ow
                if priority == 4:
                    label = "[E]"
                elif priority == 3:
                    label = "[H]"
                elif priority == 2:
                    label = "[M]"
                else:
                    label = "[L]"
                lines.append(f"\n## {label} {key}")
                lines.append(content.strip())
        parts.append("\n\n".join(lines))

    # Fallback: legacy _worldbook.md file if no entries
    if not enabled_entries:
        wb_path = os.path.join(WORKSPACE, "skills", "harem", "_worldbook.md")
        if os.path.isfile(wb_path):
            try:
                with open(wb_path, "r", encoding="utf-8") as f:
                    wb_content = f.read().strip()
                if wb_content:
                    parts.append("# WORLD BOOK / LORE\n\n" + wb_content)
            except Exception:
                pass

    # 1. SOUL.md — prefer character-specific from harem, fallback to root
    if character_id:
        char_soul = os.path.join(WORKSPACE, "skills", "harem", character_id, "SOUL.md")
        if os.path.isfile(char_soul):
            try:
                with open(char_soul, "r", encoding="utf-8") as f:
                    soul_content = f.read().strip()
                if soul_content:
                    parts.append(soul_content)
            except Exception:
                pass
    # Fallback: root SOUL.md (if no character-specific one found)
    if not parts:
        soul_path = os.path.join(WORKSPACE, "SOUL.md")
        if os.path.isfile(soul_path):
            try:
                with open(soul_path, "r", encoding="utf-8") as f:
                    soul_content = f.read().strip()
                if soul_content:
                    parts.append(soul_content)
            except Exception:
                pass

    # 2. IDENTITY.md from harem/<character_id>
    if character_id:
        identity_path = os.path.join(WORKSPACE, "skills", "harem", character_id, "IDENTITY.md")
        if os.path.isfile(identity_path):
            try:
                with open(identity_path, "r", encoding="utf-8") as f:
                    identity_content = f.read().strip()
                if identity_content:
                    parts.append(identity_content)
            except Exception:
                pass

    # 3. USER.md (user context)
    user_path = os.path.join(WORKSPACE, "USER.md")
    if os.path.isfile(user_path):
        try:
            with open(user_path, "r", encoding="utf-8") as f:
                user_content = f.read().strip()
            if user_content:
                parts.append(user_content)
        except Exception:
            pass

    if not parts:
        return None
    return "\n\n---\n\n".join(parts)


def _inject_system_prompt(messages, character_id, custom_system_prompt=None, mem0_context=None):
    """Ensure a system message is first in the messages list.
    If the first message is already a system message, replace it.
    Otherwise, insert a new system message at the beginning.
    
    Priority: custom_system_prompt > harem file > root SOUL.md
    If mem0_context is provided, append it to the system prompt.
    """
    if custom_system_prompt:
        prompt = custom_system_prompt.strip()
    else:
        prompt = _build_system_prompt(character_id)
    
    if not prompt and not mem0_context:
        return messages
    
    # Append mem0 context to system prompt
    if mem0_context:
        prompt = (prompt or "") + mem0_context
    
    if not prompt:
        return messages
    
    result = list(messages)  # shallow copy
    if result and result[0].get("role") == "system":
        result[0] = {"role": "system", "content": prompt}
    else:
        result.insert(0, {"role": "system", "content": prompt})
    return result


def _normalize_system_messages(messages):
    """Ensure exactly one system message, at index 0.

    Many chat templates (e.g. Qwen/Hermes with `raise_exception('System message
    must be at the beginning.')`) fail during llama.cpp --jinja tool-parser
    generation when a system-role message appears anywhere but position 0.
    In 对话树 (conversation-tree) mode the reconstructed message list can carry a
    system message mid-list, which triggers HTTP 400. Merge every system message
    into a single leading system message so the template always validates.
    """
    if not messages:
        return messages
    system_parts = []
    rest = []
    for msg in messages:
        if msg.get("role") == "system":
            content = msg.get("content", "")
            if isinstance(content, str):
                text = content.strip()
            else:
                # content may be a list of parts; join text parts
                try:
                    text = "\n".join(
                        p.get("text", "") for p in content
                        if isinstance(p, dict)
                    ).strip()
                except Exception:
                    text = str(content).strip()
            if text:
                system_parts.append(text)
        else:
            rest.append(msg)
    if not system_parts:
        return messages
    merged = {"role": "system", "content": "\n\n".join(system_parts)}
    return [merged] + rest


def _resolve_provider_for_model(model_id):
    """Given a model id like 'deepseek/deepseek-v4-flash', return the provider config from openclaw.json."""
    cfg_path = os.path.join(os.path.expanduser("~"), ".openclaw", "openclaw.json")
    if not os.path.isfile(cfg_path):
        return None
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        providers = cfg.get("models", {}).get("providers", {})
        parts = model_id.split("/", 1)
        provider_name = parts[0]
        return providers.get(provider_name)
    except Exception:
        return None


def _switch_llama_model(short_id, rea_mode="off"):
    """
    切换 llama 模型。
    short_id: 'qwen3.6-27b' 或 'qwen3.6-35b'
    rea_mode: 切换后使用 'on' 或 'off' reasoning（默认 off，保留当前状态需调用方传入）
    从 config.yaml 的 llama_model_map 查找 GGUF 路径。
    """
    global LLAMA_MODEL, LLAMA_MODEL_NAME, LOCAL_MODEL_ID
    global CFG

    # 从 config.yaml 读取模型映射
    model_map = CFG.get("llama_model_map", {})
    gguf_path = model_map.get(short_id)
    if not gguf_path:
        return {"ok": False, "error": f"Model '{short_id}' not found in config.yaml llama_model_map"}

    if not os.path.isfile(gguf_path):
        return {"ok": False, "error": f"GGUF not found: {gguf_path}"}

    if LLAMA_MODEL == gguf_path:
        return {"ok": True, "message": f"Already using {short_id}", "model": short_id}

    print(f"[DAEMON] Switching model to {short_id}: {gguf_path}", flush=True)

    # 1. 停止当前 llama
    if is_port_open(LLAMA_PORT):
        try:
            from skills.shared.llama_lifecycle import stop_llama
            stop_llama(port=LLAMA_PORT)
        except Exception as e:
            print(f"[DAEMON] stop_llama failed: {e}, using taskkill", flush=True)
            subprocess.run(["taskkill", "/f", "/im", "llama-server.exe"], capture_output=True)
        time.sleep(2)

    # 2. 更新全局变量（暂存旧值，失败时恢复）
    _old_model = LLAMA_MODEL
    _old_name = LLAMA_MODEL_NAME
    _old_local = LOCAL_MODEL_ID
    LLAMA_MODEL = gguf_path
    LLAMA_MODEL_NAME = short_id
    LOCAL_MODEL_ID = "local/" + short_id

    # 3. 更新 config.yaml
    try:
        import yaml as _yaml
        cfg_path = os.path.join(WORKSPACE, "config.yaml")
        with open(cfg_path, "r", encoding="utf-8-sig") as f:
            raw_cfg = _yaml.safe_load(f) or {}
        raw_cfg["llama_model"] = gguf_path
        raw_cfg["llama_model_name"] = short_id
        with open(cfg_path, "w", encoding="utf-8") as f:
            _yaml.dump(raw_cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        # 更新内存中的 CFG
        CFG["llama_model"] = gguf_path
        CFG["llama_model_name"] = short_id
        print(f"[DAEMON] config.yaml updated", flush=True)
    except Exception as e:
        print(f"[DAEMON] config.yaml update failed: {e}", flush=True)

    # 4. 启动新模型
    from skills.shared.llama_lifecycle import start_llama as _start_llama
    log_dir = CFG.get("llama_log_dir", os.path.join(WORKSPACE, "llama-server"))
    ok = _start_llama(
        port=LLAMA_PORT,
        exe_path=LLAMA_EXE,
        model_path=LLAMA_MODEL,
        log_dir=log_dir,
        rea_mode=rea_mode,
    )
    if ok:
        print(f"[DAEMON] Model switched to {short_id} successfully", flush=True)
        return {"ok": True, "message": f"Switched to {short_id}", "model": short_id}
    else:
        # 恢复全局变量 + config.yaml
        import yaml as _yaml2
        _cfg_path2 = os.path.join(WORKSPACE, "config.yaml")
        try:
            with open(_cfg_path2, "r", encoding="utf-8-sig") as _f:
                _rc = _yaml2.safe_load(_f) or {}
            _rc["llama_model"] = _old_model
            _rc["llama_model_name"] = _old_name
            with open(_cfg_path2, "w", encoding="utf-8") as _f:
                _yaml2.dump(_rc, _f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        except Exception as _e2:
            print(f"[DAEMON] config rollback failed: {_e2}", flush=True)
        LLAMA_MODEL = _old_model
        LLAMA_MODEL_NAME = _old_name
        LOCAL_MODEL_ID = _old_local
        print(f"[DAEMON] Failed to start {short_id}, restored old settings", flush=True)
        return {"ok": False, "error": f"Failed to start {short_id}"}


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/characters":
            chars = _load_harem_characters()
            self.send_json(chars)
            return

        if path == "/api/gateway-config":
            # Expose Gateway URL and token for webchat (localhost only)
            import json as _json
            cfg_path = os.path.join(os.path.dirname(os.path.expanduser("~")), ".openclaw", "openclaw.json")
            if not os.path.isfile(cfg_path):
                cfg_path = os.path.join(os.path.expanduser("~"), ".openclaw", "openclaw.json")
            gw_config = {"baseUrl": "http://localhost:18789", "token": "", "models": []}
            if os.path.isfile(cfg_path):
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg = _json.load(f)
                    gw_config["token"] = cfg.get("gateway", {}).get("auth", {}).get("token", "")
                    # Extract model aliases
                    aliases = cfg.get("agents", {}).get("defaults", {}).get("models", {})
                    providers = cfg.get("models", {}).get("providers", {})
                    model_list = []
                    for key, meta in aliases.items():
                        name = meta.get("alias", key) if isinstance(meta, dict) else str(meta)
                        model_list.append({"id": key, "name": name})
                    # Also add provider models (DeepSeek, etc.)
                    for pid, pdata in providers.items():
                        for m in pdata.get("models", []):
                            mid = pid + "/" + m["id"]
                            if not any(mm["id"] == mid for mm in model_list):
                                model_list.append({"id": mid, "name": m.get("name", mid)})
                    gw_config["models"] = model_list
                except Exception:
                    pass
            self.send_json(gw_config)
            return

        if path == "/api/status":
            self.send_json(daemon_instance.get_status())
            return

        if path == "/api/set-rea":
            qs = parse_qs(urlparse(self.path).query)
            mode = qs.get("mode", ["auto"])[0]
            if mode not in ("on", "off"):
                self.send_json({"error": "mode must be on or off"}, 400)
                return
            self.send_json({"ok": True, "message": f"Restarting llama with -rea {mode}"})
            threading.Thread(target=_set_llama_rea, args=(mode,), daemon=True).start()
            return

        if path == "/api/start":
            results = daemon_instance.start_all_services()
            self.send_json({"ok": True, "results": results})
            return

        if path == "/api/stop":
            msg = stop_all()
            self.send_json({"ok": True, "message": msg})
            return

        if path == "/api/mem0-viz":
            self._handle_mem0_viz()
            return

        if path == "/api/mem0-search":
            self._handle_mem0_search()
            return

        if path == "/api/worldbook":
            # New entries-based format
            with _wb_entries_lock:
                entries_snapshot = list(_wb_entries)
            if entries_snapshot:
                self.send_json({"entries": entries_snapshot, "count": len(entries_snapshot)})
                return
            # Fallback to legacy single-file format
            wb_path = os.path.join(WORKSPACE, "skills", "harem", "_worldbook.md")
            if os.path.isfile(wb_path):
                try:
                    with open(wb_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.send_json({"worldbook": content, "name": "_worldbook.md", "exists": True})
                except Exception:
                    self.send_json({"worldbook": None, "exists": False})
            else:
                self.send_json({"entries": [], "count": 0})
            return

        if path == "/api/restart-service":
            qs = parse_qs(urlparse(self.path).query)
            name = qs.get("name", [""])[0]
            fn = SERVICE_STARTERS.get(name)
            if fn:
                result = fn()
                self.send_json({"ok": True, "result": result})
            else:
                self.send_json({"ok": False, "error": "Unknown service"})
            return

        if path == "/" or path == "/dashboard":
            self.send_dashboard()
            return

        if path == "/api/media" or path.startswith("/api/media/"):
            self._handle_media_proxy()
            return

        self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path

        # 统一解析请求体（所有分支共用；worldbook 分支不再重复读取）
        cl = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(cl).decode("utf-8") if cl else "{}"
        try:
            self._post_data = json.loads(body)
        except Exception:
            self._post_data = {}
        data = self._post_data

        if path == "/api/worldbook":
            try:
                # New format: { entries: [...] }
                entries = data.get("entries")
                if isinstance(entries, list):
                    with _wb_entries_lock:
                        _wb_entries.clear()
                        _wb_entries.extend(entries)
                    self.send_json({"ok": True, "count": len(entries)})
                    return

                # Legacy format: { worldbook: { content, name } }
                wb = data.get("worldbook")
                wb_path = os.path.join(WORKSPACE, "skills", "harem", "_worldbook.md")
                if wb and isinstance(wb, dict) and wb.get("content"):
                    with open(wb_path, "w", encoding="utf-8") as f:
                        f.write(wb["content"])
                    self.send_json({"ok": True, "name": wb.get("name", "_worldbook.md")})
                else:
                    if os.path.isfile(wb_path):
                        os.remove(wb_path)
                    self.send_json({"ok": True, "cleared": True})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
            return

        if path == "/api/set-rea":
            qs = parse_qs(urlparse(self.path).query)
            mode = qs.get("mode", ["auto"])[0]
            if mode not in ("on", "off"):
                self.send_json({"error": "mode must be on or off"}, 400)
                return
            self.send_json({"ok": True, "message": f"Restarting llama with -rea {mode}"})
            threading.Thread(target=_set_llama_rea, args=(mode,), daemon=True).start()
            return

        if path == "/api/exec-script":
            qs = parse_qs(urlparse(self.path).query)
            script = qs.get("script", [""])[0]
            args = qs.get("args", [])
            # Security: resolve inside WORKSPACE only; reject path traversal
            script_path = os.path.abspath(os.path.join(WORKSPACE, script))
            ws_root = os.path.abspath(WORKSPACE)
            if not (script_path == ws_root or script_path.startswith(ws_root + os.sep)):
                self.send_json({"error": f"Script outside workspace: {script}"}, 403)
                return
            if not script_path.lower().endswith(".ps1"):
                self.send_json({"error": f"Only .ps1 scripts allowed: {script}"}, 403)
                return
            if not os.path.isfile(script_path):
                self.send_json({"error": f"Script not found: {script}"}, 404)
                return
            if script == "restart_llama_rea.ps1":
                # Pass paths from config, not hardcoded in script
                args = args + [LLAMA_EXE, LLAMA_MODEL, os.path.dirname(LLAMA_LOG)]
            self.send_json({"ok": True, "message": f"Running {script} {' '.join(args)}"})
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path] + args
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return

        if path == "/api/switch-model":
            model_id = data.get("model_id", "")
            if not model_id:
                self.send_json({"ok": False, "error": "Missing model_id"})
                return
            short_id = model_id.split("/")[-1] if "/" in model_id else model_id
            # 保留当前 reasoning 状态
            current_rea = _get_actual_rea_state()
            result = _switch_llama_model(short_id, rea_mode=current_rea)
            self.send_json(result)
            return

        if path == "/api/headroom-test":
            self._handle_headroom_test()
            return

        if path == "/api/chat":
            self._handle_chat_proxy()
            return

        if path == "/api/gen-prompt":
            self._handle_gen_prompt()
            return

        if path == "/api/debug-llama":
            self._handle_debug_llama()
            return

        if path == "/api/session-history":
            self._handle_session_history()
            return

        if path == "/api/start":
            results = daemon_instance.start_all_services()
            self.send_json({"ok": True, "results": results})

        elif path == "/api/stop":
            msg = stop_all()
            self.send_json({"ok": True, "message": msg})

        elif path == "/api/start-service":
            name = data.get("name")
            fn = SERVICE_STARTERS.get(name)
            if fn:
                result = fn()
                self.send_json({"ok": True, "result": result})
            else:
                self.send_json({"ok": False, "error": "Unknown service"})

        elif path == "/api/stop-service":
            name = data.get("name")
            port = SERVICE_KILLERS.get(name)
            if port is None:
                self.send_json({"ok": False, "error": f"Service '{name}' cannot be stopped individually (runs in daemon)"})
            elif isinstance(port, int):
                try:
                    result = _kill_by_port(port)
                    self.send_json({"ok": True, "result": result})
                except Exception as e:
                    self.send_json({"ok": False, "error": str(e)})
            else:
                self.send_json({"ok": False, "error": f"No kill handler for '{name}'"})

        elif path == "/api/toggle":
            name = data.get("name")
            for svc in SERVICES:
                if svc["name"] == name:
                    svc["enabled"] = not svc.get("enabled", True)
                    self.send_json({"ok": True, "enabled": svc["enabled"]})
                    return
            self.send_json({"ok": False, "error": "not found"})

        else:
            self.send_error(404)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def send_dashboard(self):
        # Dashboard is now embedded in web-chat, redirect
        self.send_response(302)
        self.send_header("Location", f"http://127.0.0.1:{WEBCHAT_PORT}")
        self.end_headers()

# ================================================================
# Tray App (Windows)
# ================================================================
# ================================================================
# Tray App (Windows)
# ================================================================

    def _handle_session_history(self):
        """Read OpenClaw session history for a character/session."""
        qs = parse_qs(urlparse(self.path).query)
        session_key = qs.get("sessionKey", [""])[0] or "main"
        limit = int(qs.get("limit", ["10"])[0])
        
        # Find the sessions.json path for this agent
        import glob
        # os.path.dirname(os.path.expanduser("~")) drops the username
        # (C:\Users\TK -> C:\Users); use expanduser directly so the path
        # stays dynamic/portable across machines.
        agents_dir = os.path.join(os.path.expanduser("~"), ".openclaw", "agents")
        session_files = []
        for agent_dir in glob.glob(os.path.join(agents_dir, "*", "sessions")):
            sf = os.path.join(agent_dir, "sessions.json")
            if os.path.isfile(sf):
                session_files.append(sf)
        
        if not session_files:
            self.send_json({"error": "No sessions.json found", "history": []})
            return
        
        try:
            # Read all session files, find matching session
            all_messages = []
            for sf in session_files:
                try:
                    with open(sf, "r", encoding="utf-8") as f:
                        sessions_data = json.load(f)
                    if not isinstance(sessions_data, dict):
                        continue
                    # Look for the session
                    target_key = session_key
                    if target_key == "main":
                        target_key = "agent:main:main"
                    elif not target_key.startswith("agent:"):
                        target_key = f"agent:main:{target_key}"
                    
                    if target_key in sessions_data:
                        session = sessions_data[target_key]
                        msgs = session.get("messages", [])
                        for m in msgs[-limit:]:
                            all_messages.append({
                                "role": m.get("role", ""),
                                "content": m.get("content", ""),
                                "time": m.get("timestamp", m.get("time", ""))
                            })
                except Exception as e:
                    print(f"[session-history] error reading {sf}: {e}", file=sys.stderr)
            
            # Sort by time if available
            if all_messages:
                all_messages.sort(key=lambda x: x.get("time", ""))
            
            self.send_json({"ok": True, "history": all_messages[-limit:], "source": "session-history"})
        except Exception as e:
            self.send_json({"error": str(e), "history": []})
            return

    def _handle_mem0_search(self):
        """Search mem0 memories and return raw results for frontend display.
        Supports empty characterId (iterate all characters) and returns characterId per result."""
        qs = parse_qs(urlparse(self.path).query)
        character_id = qs.get("characterId", [""])[0] or ""
        query = qs.get("query", [""])[0] or ""
        limit = int(qs.get("limit", ["20"])[0])
        
        try:
            if WORKSPACE not in sys.path:
                sys.path.insert(0, WORKSPACE)
            try:
                from skills.mem0_bridge.mem0_bridge import search_mem0_qdrant, CHARACTERS
            except ImportError:
                from skills.shared.mem0_bridge import search_mem0_qdrant, CHARACTERS

            if character_id:
                char_ids = [character_id]
            else:
                # Empty characterId: iterate all known characters
                char_ids = list(CHARACTERS.keys())
            
            all_results = []
            for cid in char_ids:
                try:
                    results = search_mem0_qdrant(cid, query if query else "所有记忆", limit=limit)
                    for r in results:
                        all_results.append({
                            "content": r.get("memory", ""),
                            "score": r.get("score", 0),
                            "timestamp": r.get("metadata", {}).get("created_at", ""),
                            "characterId": cid,
                        })
                except Exception:
                    pass  # skip characters with no results
            
            all_results.sort(key=lambda x: x["score"], reverse=True)
            if not character_id:
                all_results = all_results[:limit]
            
            self.send_json({"ok": True, "results": all_results, "source": "mem0"})
        except Exception as e:
            print(f"[mem0-search] error: {e}", file=sys.stderr)
            self.send_json({"error": str(e), "results": []})
            return

    def _handle_mem0_viz(self):
        """GET /api/mem0-viz — return all mem0 memories with PCA-2D
        projection of their embedding vectors for the frontend scatter plot.
        Pure local: numpy PCA over 384-dim vectors -> x/y."""
        try:
            if WORKSPACE not in sys.path:
                sys.path.insert(0, WORKSPACE)
            try:
                from skills.mem0_bridge.mem0_bridge import _get_qdrant_client, CHARACTERS
            except ImportError:
                from skills.shared.mem0_bridge import _get_qdrant_client, CHARACTERS
            client = _get_qdrant_client()
            try:
                pts, _ = client.scroll(
                    collection_name="sakura_memories",
                    limit=2000, with_payload=True, with_vectors=True,
                )
            finally:
                try:
                    client.close()
                except Exception:
                    pass

            import numpy as np
            items = []
            vecs = []
            for p in pts:
                payload = p.payload or {}
                text = payload.get("memory", "") or payload.get("data", "")
                if not text:
                    continue
                vec = p.vector
                if vec is None or not hasattr(vec, "__len__"):
                    continue
                try:
                    v = np.asarray(list(vec), dtype=float)
                except Exception:
                    continue
                if v.shape[0] < 2:
                    continue
                vecs.append(v)
                items.append({
                    "text": text,
                    "character": payload.get("agent_id", payload.get("user_id", "?")),
                    "time": payload.get("timestamp", payload.get("created_at", "")),
                })

            if not vecs:
                self.send_json({"ok": True, "points": [], "count": 0})
                return

            # PCA to 2D (mean-center + top-2 singular vectors)
            M = np.vstack(vecs)
            M = M - M.mean(axis=0, keepdims=True)
            try:
                _, _, Vt = np.linalg.svd(M, full_matrices=False)
                proj = M @ Vt[:2].T
            except Exception:
                # Fallback: random projection (deterministic seed)
                rng = np.random.RandomState(42)
                R = rng.randn(M.shape[1], 2)
                R /= np.linalg.norm(R, axis=0, keepdims=True)
                proj = M @ R

            # Normalize to ~[-1, 1] box
            x = proj[:, 0]; y = proj[:, 1]
            xr = x.max() - x.min() if x.max() != x.min() else 1.0
            yr = y.max() - y.min() if y.max() != y.min() else 1.0
            for i, it in enumerate(items):
                it["x"] = round(float((x[i] - x.min()) / xr * 2 - 1), 4)
                it["y"] = round(float((y[i] - y.min()) / yr * 2 - 1), 4)

            self.send_json({"ok": True, "points": items, "count": len(items)})
        except Exception as e:
            print(f"[mem0-viz] error: {e}", file=sys.stderr)
            self.send_json({"ok": False, "error": str(e), "points": []})

    def _handle_headroom_test(self):
        """POST /api/headroom-test — 测试压缩效果，返回压缩前后对比"""
        try:
            req_data = getattr(self, "_post_data", None)
            if not isinstance(req_data, dict):
                cl = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(cl).decode("utf-8") if cl else "{}"
                req_data = json.loads(body)

            messages = req_data.get("messages", [])
            query = req_data.get("query", "")
            hr_cfg = req_data.get("headroom_config", {})

            from skills.shared.context_trimming import trim_messages_for_model, context_stats

            # 动态应用配置
            trim_kwargs = {}
            if hr_cfg:
                trim_kwargs["recent_full_rounds"] = int(hr_cfg.get("recent_full_rounds", 4))
                trim_kwargs["max_messages"] = int(hr_cfg.get("max_messages", 24))
                trim_kwargs["max_chars"] = int(hr_cfg.get("max_chars", 40000))
                from skills.shared import context_trimming as ct
                for k in ("max_items_after_crush", "first_fraction", "last_fraction",
                          "variance_threshold", "preserve_change_points",
                          "dedup_identical_items", "use_feedback_hints"):
                    if k in hr_cfg:
                        ct.CRUSH_CONFIG[k] = hr_cfg[k]

            before = context_stats(messages)
            compressed = trim_messages_for_model(messages, query=query, **trim_kwargs)
            after = context_stats(compressed)

            ratio = after["estimated_tokens"] / max(1, before["estimated_tokens"])

            self.send_json({
                "ok": True,
                "compressed_messages": compressed,
                "stats": {
                    "orig_messages": before["messages"],
                    "new_messages": after["messages"],
                    "orig_chars": before["total_chars"],
                    "new_chars": after["total_chars"],
                    "orig_tokens": before["estimated_tokens"],
                    "new_tokens": after["estimated_tokens"],
                    "compression_ratio": round(ratio, 3),
                },
            })
        except Exception as e:
            self.send_json({"error": f"Headroom test failed: {e}"}, 500)

    def _handle_chat_proxy(self):
        # body 已在 do_POST 开头解析，直接复用 self._post_data
        req_data = getattr(self, "_post_data", None)
        if not isinstance(req_data, dict):
            try:
                body_len = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(body_len) if body_len else b"{}"
                req_data = json.loads(body)
            except Exception:
                self.send_json({"error": "Invalid JSON"}, 400)
                return

        # Run the upstream request in a background thread so this handler
        # can stream the response without blocking the whole server loop.
        from threading import Thread, Event

        model_id = req_data.get("model", LOCAL_MODEL_ID)

        # Reasoning toggle — restart llama in background, return error for now.
        # NOTE: "auto" (default) is a flexible mode that already handles both
        # reasoning and non-reasoning prompts, so a manually-started llama with
        # -rea auto must NOT be force-restarted just because the frontend asks
        # for reasoning on/off. Only restart when we KNOW the running llama was
        # pinned to the opposite mode.
        if model_id.startswith("local/"):
            reasoning_on = req_data.get("reasoning", "off") == "on"
            desired = "on" if reasoning_on else "off"
            if _llama_rea_state != "auto" and _llama_rea_state != desired:
                self.send_json({"error": f"Restarting llama with -rea {desired}, please retry in ~30s"}, 503)
                threading.Thread(target=_set_llama_rea, args=(desired,), daemon=True).start()
                return

        messages = req_data.get("messages", [])
        stream = req_data.get("stream", False)
        max_tokens = req_data.get("max_tokens", 4096)
        character_id = req_data.get("characterId", "natsume")
        custom_system_prompt = req_data.get("systemPrompt", None)  # imported characters pass their own prompt
        mem0_enhanced = req_data.get("mem0Enhanced", False)
        mem0_write_enabled = req_data.get("mem0WriteEnabled", False)
        mem0_write_interval = max(1, req_data.get("mem0WriteInterval", 10))
        thinking_mode = req_data.get("thinkingMode", "default")
        reasoning_on = req_data.get("reasoning", "off") == "on"

        # Inject thinking-mode marker only when reasoning is enabled.
        # Works on any model that supports reasoning_content / thinking tags.
        thinking_marker = None
        if reasoning_on and thinking_mode in ("immersive", "analytic", "godview"):
            thinking_marker = _get_thinking_marker(thinking_mode)
            if thinking_marker:
                messages = _inject_thinking_marker(messages, thinking_marker)

        # Mem0: search relevant memories before building messages
        mem0_context = None
        if mem0_enhanced:
            try:
                last_user_msg = ""
                for m in reversed(messages):
                    if m.get("role") == "user":
                        last_user_msg = m.get("content", "")
                        break
                if last_user_msg:
                    mem0_context = _mem0_search_context(character_id, last_user_msg)
            except Exception as e:
                print(f"[mem0] search error for {character_id}: {e}", file=sys.stderr)

        # Inject system prompt from custom/harem/SOUL.md
        messages = _inject_system_prompt(messages, character_id, custom_system_prompt, mem0_context)

        # ── Headroom SmartCrusher: 强制上下文压缩 ──
        try:
            from skills.shared.context_trimming import trim_messages_for_model, context_stats
            
            # 读取前端传来的 headroom 配置（如果有）
            hr_cfg = req_data.get("headroom_config", {})
            
            last_user_query = ""
            for m in reversed(messages):
                if m.get("role") == "user":
                    last_user_query = m.get("content", "")
                    break
            before = context_stats(messages)
            
            # 动态参数：前端配置优先，fallback 到 context_trimming.py 默认值
            trim_kwargs = {}
            if hr_cfg:
                trim_kwargs["recent_full_rounds"] = int(hr_cfg.get("recent_full_rounds", 4))
                trim_kwargs["max_messages"] = int(hr_cfg.get("max_messages", 24))
                trim_kwargs["max_chars"] = int(hr_cfg.get("max_chars", 40000))
                # 更新 SmartCrusher 全局配置
                from skills.shared import context_trimming
                context_trimming.CRUSH_CONFIG["max_items_after_crush"] = int(hr_cfg.get("max_items_after_crush", 10))
                context_trimming.CRUSH_CONFIG["first_fraction"] = float(hr_cfg.get("first_fraction", 0.3))
                context_trimming.CRUSH_CONFIG["last_fraction"] = float(hr_cfg.get("last_fraction", 0.15))
                context_trimming.CRUSH_CONFIG["variance_threshold"] = float(hr_cfg.get("variance_threshold", 2.0))
                context_trimming.CRUSH_CONFIG["preserve_change_points"] = bool(hr_cfg.get("preserve_change_points", True))
                context_trimming.CRUSH_CONFIG["dedup_identical_items"] = bool(hr_cfg.get("dedup_identical_items", True))
                context_trimming.CRUSH_CONFIG["use_feedback_hints"] = bool(hr_cfg.get("use_feedback_hints", True))
            
            messages = trim_messages_for_model(messages, query=last_user_query, **trim_kwargs)
            after = context_stats(messages)
            if before["messages"] != after["messages"]:
                print(f"[headroom] compressed {before['messages']}→{after['messages']} msgs, "
                      f"{before['estimated_tokens']}→{after['estimated_tokens']} tokens "
                      f"({int((1-after['estimated_tokens']/max(1,before['estimated_tokens']))*100)}% saved)",
                      file=sys.stderr)
        except Exception as e:
            print(f"[headroom] context trimming skipped: {e}", file=sys.stderr)
        # ── End headroom ──

        # Local llama: skip provider lookup, use config-based endpoint
        use_local = model_id.startswith("local/")
        if use_local:
            api_key = ""
            auth_header = ""  # no auth needed (--api-key breaks llama-server)
            base_url = LLAMA_BASE_URL
            backend_model = LLAMA_MODEL_NAME
            print(f"[chat] routing to local llama: {base_url}", file=sys.stderr)
        else:
            provider_cfg = _resolve_provider_for_model(model_id)
            if not provider_cfg:
                self.send_json({"error": f"Model not found: {model_id}. Check openclaw.json providers."}, 400)
                return
            api_key = provider_cfg.get("apiKey", "")
            auth_header = "Bearer " + api_key
            base_url = provider_cfg.get("baseUrl", "").rstrip("/")
            backend_model = model_id.split("/")[-1]
            print(f"[chat] routing to cloud provider: {base_url} model={backend_model}", file=sys.stderr)

        endpoint = base_url + "/chat/completions"
        # Normalize system messages to a single leading message. Required for
        # templates that raise when a system message is not at the beginning
        # (e.g. 对话树 mode sending mid-list system messages -> HTTP 400 on --jinja).
        messages = _normalize_system_messages(messages)
        payload = {"model": backend_model, "messages": messages, "stream": stream, "max_tokens": max_tokens}

        # ── 并发控制：使用信号量限制同时请求数 ──
        semaphore = _llama_semaphore if use_local else None
        if semaphore:
            acquired = semaphore.acquire(blocking=True, timeout=30)
            if not acquired:
                self.send_json({"error": "Server busy, too many concurrent requests. Please retry."}, 503)
                return
        
        try:
            import urllib.request, urllib.error
            data = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if auth_header:
                headers["Authorization"] = auth_header
            req = urllib.request.Request(endpoint, data=data, headers=headers)
            
            # ── 重试逻辑：最多重试 REQUEST_MAX_RETRIES 次 ──
            last_error = None
            for attempt in range(REQUEST_MAX_RETRIES + 1):
                try:
                    resp = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
                    if stream:
                        self.send_response(200)
                        self.send_header("Content-Type", "text/event-stream")
                        self.send_header("Cache-Control", "no-cache")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()
                        try:
                            for line_bytes in resp:
                                line = line_bytes.decode("utf-8", errors="replace")
                                self.wfile.write((line.rstrip("\n") + "\n").encode("utf-8"))
                                self.wfile.flush()
                            self.wfile.write(b"data: [DONE]\n\n")
                            self.wfile.flush()
                        except Exception as stream_err:
                            print(f"[chat] stream error: {stream_err}", file=sys.stderr)
                            try:
                                self.wfile.write(f"data: {{\"error\":\"{stream_err}\"}}\n\n".encode("utf-8"))
                                self.wfile.flush()
                            except Exception:
                                pass
                        finally:
                            resp.close()
                    else:
                        response_data = resp.read()
                        resp.close()
                        self.send_json(json.loads(response_data))

                    # Mem0: trigger write after response (non-blocking)
                    if mem0_write_enabled:
                        self._maybe_write_mem0(character_id, messages, mem0_write_interval)
                    break  # 成功，跳出重试循环
                    
                except urllib.error.HTTPError as http_err:
                    last_error = http_err
                    error_detail = f"HTTP {http_err.code}"
                    try:
                        error_body = http_err.read().decode("utf-8")
                        error_detail += f": {error_body[:200]}"
                    except Exception:
                        pass
                    if attempt < REQUEST_MAX_RETRIES and http_err.code >= 500:
                        print(f"[chat] attempt {attempt+1}/{REQUEST_MAX_RETRIES+1} failed: {error_detail}, retrying...", file=sys.stderr)
                        time.sleep(1 * (attempt + 1))  # 指数退避
                        continue
                    else:
                        raise Exception(f"Provider error: {error_detail}")
                        
                except (urllib.error.URLError, socket.timeout, ConnectionError) as net_err:
                    last_error = net_err
                    if attempt < REQUEST_MAX_RETRIES:
                        print(f"[chat] attempt {attempt+1}/{REQUEST_MAX_RETRIES+1} network error: {net_err}, retrying...", file=sys.stderr)
                        time.sleep(2 * (attempt + 1))
                        continue
                    else:
                        raise Exception(f"Network error after {REQUEST_MAX_RETRIES+1} attempts: {net_err}")
                        
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"[chat] final error: {error_msg}", file=sys.stderr)
            self.send_json({"error": error_msg, "model": model_id, "endpoint": endpoint}, 502)
        finally:
            if semaphore:
                semaphore.release()

    def _handle_gen_prompt(self):
        """Use LLM to generate a ComfyUI image prompt from conversation context."""
        req_data = getattr(self, "_post_data", None)
        if not isinstance(req_data, dict):
            try:
                body_len = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(body_len) if body_len else b"{}"
                req_data = json.loads(body)
            except Exception:
                self.send_json({"error": "Invalid JSON"}, 400)
                return

        character_id = req_data.get("characterId", "natsume")
        messages = req_data.get("messages", [])

        # Get character name for the prompt instruction
        char_name = character_id
        # Try to get display name from harem (supports both Chinese + English folder names)
        identity_path = os.path.join(WORKSPACE, "skills", "harem", character_id, "IDENTITY.md")
        if os.path.isfile(identity_path):
            try:
                with open(identity_path, "r", encoding="utf-8") as f:
                    for line in f:
                        stripped = line.strip()
                        # Match both "- Name: XXX" and "* **Name:** XXX" formats
                        if stripped.startswith("- Name:"):
                            char_name = stripped.split(":", 1)[1].strip()
                            break
                        if stripped.startswith("* **Name:**"):
                            char_name = stripped.split(":", 1)[1].strip() if ":" in stripped else stripped.replace("* **Name:**", "").strip()
                            break
                # Remove parenthetical English
                import re
                char_name = re.sub(r"\s*[（(][^)）]*[)）]", "", char_name).strip()
            except Exception:
                pass
        # Fallback: try fuzzy match in harem dir (for Chinese folder names)
        if char_name == character_id:
            harem_root = os.path.join(WORKSPACE, "skills", "harem")
            if os.path.isdir(harem_root):
                for d in os.listdir(harem_root):
                    idd = os.path.join(harem_root, d, "IDENTITY.md")
                    if d == character_id or (os.path.isfile(idd) and d in character_id):
                        try:
                            with open(idd, "r", encoding="utf-8") as f:
                                for line in f:
                                    stripped = line.strip()
                                    if stripped.startswith("- Name:"):
                                        char_name = stripped.split(":", 1)[1].strip()
                                        break
                                    if stripped.startswith("* **Name:**"):
                                        char_name = stripped.split(":", 1)[1].strip() if ":" in stripped else stripped.replace("* **Name:**", "").strip()
                                        break
                            import re
                            char_name = re.sub(r"\s*[（(][^)）]*[)）]", "", char_name).strip()
                            break
                        except Exception:
                            pass

        # Build character appearance context from SOUL.md if available
        char_context = ""
        soul_path = os.path.join(WORKSPACE, "skills", "harem", character_id, "SOUL.md")
        if os.path.isfile(soul_path):
            try:
                with open(soul_path, "r", encoding="utf-8") as f:
                    soul_text = f.read()
                # Extract appearance section
                import re
                app_match = re.search(r'【总体】(.*?)(?:【|$)', soul_text, re.DOTALL)
                if not app_match:
                    app_match = re.search(r'1\.5.*?外貌.*?【总体】(.*?)(?:【|$)', soul_text, re.DOTALL)
                if app_match:
                    char_context = app_match.group(1).strip()[:300]
                else:
                    # Use first 400 chars
                    char_context = soul_text.strip()[:400]
            except Exception:
                pass

        if char_context:
            char_context = f"\nCharacter description:\n{char_name}: {char_context}\n"

        # Build the instruction for LLM
        instruction = f"""You are an AI prompt engineer for image generation. Based on the conversation context below, generate a ComfyUI/Stable Diffusion prompt for the character "{char_name}".

IMPORTANT: Do NOT think or reason. Output your answer directly.

Rules:
- Output ONLY a JSON object with "prompt" and "negative" fields, nothing else.
- The prompt should be in English, detailed, include character appearance, clothing, setting, mood, lighting.
- Use tags like: masterpiece, best quality, 1girl, highly detailed, etc.
- Describe the current scene/mood based on the conversation. If no specific scene is mentioned, create a beautiful portrait.
- The negative prompt should cover common issues: bad quality, worst quality, blurry, distorted, lowres, bad anatomy, extra fingers, watermark, text, ugly, deformed.
- Keep the prompt under 300 characters.
{char_context}
Conversation:
"""
        # Format messages as conversation text
        conv_lines = []
        for msg in messages[-6:]:  # last 6 messages
            role = msg.get("role", "")
            content = msg.get("content", "")[:200]
            if role == "user":
                conv_lines.append(f"User: {content}")
            elif role == "assistant":
                conv_lines.append(f"{char_name}: {content}")
        instruction += "\n".join(conv_lines)

        # Check if llama is online; if not, use fallback prompt immediately
        if not is_port_open(LLAMA_PORT):
            fallback = _make_fallback_prompt(character_id, char_name, messages)
            self.send_json(fallback)
            return

        # Call local LLM (non-streaming)
        try:
            import urllib.request, urllib.error
            payload = {
                "model": LLAMA_MODEL_NAME,
                "messages": [{"role": "user", "content": instruction}],
                "stream": False,
                "max_tokens": 800,
                "temperature": 0.7,
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{LLAMA_BASE_URL}/chat/completions",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            resp = urllib.request.urlopen(req, timeout=120)
            result = json.loads(resp.read())
            msg = result.get("choices", [{}])[0].get("message", {})
            content = msg.get("content", "") or msg.get("reasoning_content", "")

            # Parse JSON from response.
            # The model often wraps the answer in a long thinking block
            # (reasoning_content) that may contain stray braces, so prefer
            # extracting the "prompt"/"negative" fields directly.
            import re
            prompt_text = ""
            negative_text = ""
            try:
                # 1) Whole response is valid JSON
                prompt_data = json.loads(content)
                prompt_text = prompt_data.get("prompt", "")
                negative_text = prompt_data.get("negative", "")
            except Exception:
                pass
            if not prompt_text:
                # 2) Field-level extraction (robust against thinking noise)
                pm = re.search(r'"prompt"\s*:\s*"([^"]{1,500})"', content)
                nm = re.search(r'"negative"\s*:\s*"([^"]{1,500})"', content)
                if pm:
                    prompt_text = pm.group(1)
                if nm:
                    negative_text = nm.group(1)
            if not prompt_text:
                # 3) Old-style whole-object match
                json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
                if json_match:
                    try:
                        prompt_data = json.loads(json_match.group())
                        prompt_text = prompt_data.get("prompt", "")
                        negative_text = prompt_data.get("negative", "")
                    except Exception:
                        pass
            if prompt_text:
                self.send_json({
                    "prompt": prompt_text.strip(),
                    "negative": negative_text.strip() or "bad quality, worst quality, blurry",
                })
            else:
                # Fallback: strip any thinking preamble, keep last clean line
                lines = [l.strip() for l in content.splitlines() if l.strip()]
                clean_lines = [l for l in lines if not re.match(r'^(Here.s a thinking|1\.\s|\*\*Analyze|I need to)', l)]
                prompt_text = " ".join(clean_lines) if clean_lines else content
                prompt_text = prompt_text.strip().strip('"').strip("'")
                if len(prompt_text) > 500:
                    prompt_text = prompt_text[:500]
                self.send_json({
                    "prompt": prompt_text,
                    "negative": "bad quality, worst quality, blurry, distorted, lowres, bad anatomy, extra fingers, watermark, text",
                })
        except Exception as e:
            # LLM failed - use fallback prompt instead of returning error
            fallback = _make_fallback_prompt(character_id, char_name, messages)
            self.send_json(fallback)

    def _handle_media_proxy(self):
        """Proxy local file paths so the browser can load generated images.

        Security: only serves files under WORKSPACE/media (dynamic, derived
        from this file's location so the repo stays portable). Anything else
        (configs, secrets, system files) is rejected.
        """
        from urllib.parse import unquote
        parsed = urlparse(self.path)
        file_path = unquote(parsed.query) if parsed.query else None
        # Also handle /api/media/<path> style
        if not file_path:
            prefix = "/api/media/"
            if parsed.path.startswith(prefix):
                file_path = unquote(parsed.path[len(prefix):])
        if not file_path:
            self.send_error(400)
            return
        try:
            file_path = os.path.abspath(file_path)
        except Exception:
            self.send_error(400)
            return
        if not os.path.isfile(file_path):
            self.send_error(404)
            return
        # Path whitelist: WORKSPACE/media (and subdirs) + config media dirs may be served.
        media_roots = [os.path.abspath(os.path.join(WORKSPACE, "media"))]
        cfg_media_audio = CFG.get("media_qqbot_audio", "")
        cfg_media_images = CFG.get("media_qqbot_images", "")
        if cfg_media_audio:
            media_roots.append(os.path.abspath(cfg_media_audio))
        if cfg_media_images:
            media_roots.append(os.path.abspath(cfg_media_images))
        allowed = False
        for mr in media_roots:
            if file_path == mr or file_path.startswith(mr + os.sep):
                allowed = True
                break
        if not allowed:
            print(f"[media proxy] blocked path outside media roots: {file_path}", file=sys.stderr)
            self.send_error(403)
            return
        try:
            # Determine content type
            ext = os.path.splitext(file_path)[1].lower()
            content_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                           ".gif": "image/gif", ".webp": "image/webp", ".mp3": "audio/mpeg",
                           ".wav": "audio/wav", ".mp4": "video/mp4"}
            content_type = content_types.get(ext, "application/octet-stream")
            with open(file_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(data)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass
        except Exception as e:
            self.send_error(500)
            print(f"[media proxy] Error serving {file_path}: {e}")

    def _handle_debug_llama(self):
        """Debug chat endpoint — passes all params through, returns raw response."""
        req_data = getattr(self, "_post_data", None)
        if not isinstance(req_data, dict):
            try:
                body_len = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(body_len) if body_len else b"{}"
                req_data = json.loads(body)
            except Exception:
                self.send_json({"error": "Invalid JSON"}, 400)
                return

        model_id = req_data.get("model", LOCAL_MODEL_ID)
        messages = req_data.get("messages", [])
        stream = req_data.get("stream", False)

        # Resolve backend
        if model_id.startswith("local/"):
            api_key = ""
            base_url = LLAMA_BASE_URL
            backend_model = LLAMA_MODEL_NAME
        else:
            provider_cfg = _resolve_provider_for_model(model_id)
            if not provider_cfg:
                self.send_json({"error": f"Unknown model: {model_id}"}, 400)
                return
            api_key = provider_cfg.get("apiKey", "")
            base_url = provider_cfg.get("baseUrl", "").rstrip("/")
            backend_model = model_id.split("/")[-1]

        # Forward all llama-compatible params
        payload = {
            "model": backend_model,
            "messages": messages,
            "stream": stream,
            "max_tokens": req_data.get("max_tokens", 2048),
            "temperature": req_data.get("temperature", 0.7),
            "top_p": req_data.get("top_p", 0.9),
            "top_k": req_data.get("top_k", 40),
            "frequency_penalty": req_data.get("frequency_penalty", 0.0),
            "presence_penalty": req_data.get("presence_penalty", 0.0),
            "repeat_penalty": req_data.get("repeat_penalty", 1.1),
            "min_p": req_data.get("min_p", 0.05),
        }
        if req_data.get("logprobs"):
            payload["logprobs"] = True
            payload["top_logprobs"] = req_data.get("top_logprobs", 3)

        endpoint = base_url + "/chat/completions"
        auth_header = ("Bearer " + api_key) if api_key else ""

        try:
            import urllib.request, urllib.error
            data = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if auth_header:
                headers["Authorization"] = auth_header
            req = urllib.request.Request(endpoint, data=data, headers=headers)
            resp = urllib.request.urlopen(req, timeout=120)

            if stream:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                for line_bytes in resp:
                    line = line_bytes.decode("utf-8", errors="replace")
                    self.wfile.write((line.rstrip("\n") + "\n").encode("utf-8"))
                    self.wfile.flush()
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            else:
                self.send_json(json.loads(resp.read()))
        except Exception as e:
            self.send_json({"error": str(e)}, 502)

import pystray
from PIL import Image, ImageDraw

def make_icon():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], fill="#d4787a")
    draw.ellipse([16, 16, 48, 48], fill="#1a1a2e")
    return img

class ThreadingDashboardServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server so chat proxy doesn't block status checks."""
    daemon_threads = True
    
class ThreadingWebChatServer(ThreadingMixIn, http.server.HTTPServer):
    """Multi-threaded HTTP server for web-chat static files."""
    daemon_threads = True

def run_dashboard_server(daemon):
    global daemon_instance
    daemon_instance = daemon
    server = ThreadingDashboardServer(("127.0.0.1", DASHBOARD_PORT), DashboardHandler)
    print(f"[dashboard] http://127.0.0.1:{DASHBOARD_PORT}")
    server.serve_forever()

def run_webchat_server():
    """Simple file server for web-chat with no-cache headers."""
    import http.server
    os.chdir(WEBCHAT_DIR)

    class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            super().end_headers()

    server = ThreadingWebChatServer(("127.0.0.1", WEBCHAT_PORT), NoCacheHandler)
    print(f"[webchat] http://127.0.0.1:{WEBCHAT_PORT}")
    server.serve_forever()

def main():
    daemon = ShikiDaemon()

    # Start dashboard server
    dash_thread = threading.Thread(target=run_dashboard_server, args=(daemon,), daemon=True)
    dash_thread.start()

    # Start webchat server
    if os.path.isdir(WEBCHAT_DIR):
        wc_thread = threading.Thread(target=run_webchat_server, daemon=True)
        wc_thread.start()
        time.sleep(1)

    # Auto-start services
    if AUTO_START:
        print("[daemon] Auto-starting services...")
        threading.Thread(target=daemon.start_all_services, daemon=True).start()

    # Open webchat (dashboard is embedded there)
    webbrowser.open(f"http://127.0.0.1:{WEBCHAT_PORT}")

    # Tray icon
    icon = pystray.Icon(
        "shiki_daemon",
        make_icon(),
        "Shiki Daemon — AI Girlfriend",
        menu=pystray.Menu(
            pystray.MenuItem("Open Web Chat", lambda: webbrowser.open(f"http://127.0.0.1:{WEBCHAT_PORT}")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Start All", lambda: threading.Thread(target=daemon.start_all_services, daemon=True).start()),
            pystray.MenuItem("Stop All", lambda: stop_all()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda: on_quit(icon, daemon)),
        )
    )

    def on_quit(icon, daemon):
        print("[daemon] Shutting down...")
        icon.stop()
        stop_all()
        daemon.stop()
        os._exit(0)

    icon.run()


if __name__ == "__main__":
    # Check deps
    try:
        import pystray
    except ImportError:
        print("[daemon] Missing pystray. Install: pip install pystray pillow")
        sys.exit(1)

    main()
