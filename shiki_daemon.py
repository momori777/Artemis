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

import sys, os, json, time, threading, subprocess
import socket, signal, webbrowser
import http.server
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
os.chdir(WORKSPACE)

# Config
import yaml
with open(os.path.join(WORKSPACE, "config.yaml"), "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)

LLAMA_EXE = CFG["llama_exe"]
LLAMA_MODEL = CFG["llama_model"]
LLAMA_PORT = int(CFG.get("llama_port", 8080))
LLAMA_LOG = os.path.join(CFG.get("llama_log_dir", WORKSPACE), "llama-err.log")
LIVE2D_DIR = os.path.join(WORKSPACE, "live2d")
EMBED_SCRIPT = os.path.join(WORKSPACE, "skills", "shared", "embedding_server.py")
BRIDGE_SCRIPT = os.path.join(WORKSPACE, "artemis_bridge.py")
WEBCHAT_DIR = os.path.join(WORKSPACE, "web-chat")
DASHBOARD_PORT = 19260
WEBCHAT_PORT = 19270

SERVICES = [
    {"name": "llama-server",    "port": LLAMA_PORT,  "enabled": True},
    {"name": "Embedding",       "port": 9999,         "enabled": True},
    {"name": "Live2D Bridge",   "port": 19200,        "enabled": True},
    {"name": "Artemis Bridge",  "port": 19250,        "enabled": True},
    {"name": "OpenClaw Gateway","port": 18789,        "enabled": True},
    {"name": "Task Board",      "port": 19280,        "enabled": True,  "note": "AgentRQ-style task queue UI"},
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
        except: pass
    return "python"

PYTHON = find_python()

def is_port_open(port):
    try:
        sock = socket.create_connection(("127.0.0.1", port), timeout=1)
        sock.close()
        return True
    except: return False

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

    args = [
        LLAMA_EXE, "-m", LLAMA_MODEL,
        "-c", "120000", "--flash-attn", "on",
        "-ctk", "q8_0", "-ctv", "q8_0",
        "-ngl", "41", "--cpu-moe",
        "--batch-size", "2048", "--ubatch-size", "1024",
        "--threads", "24",
        "-rea", "off", "--jinja", "--cache-ram", "3000",
        "--parallel", "1", "--kv-unified", "--no-mmap",
        "--port", str(LLAMA_PORT), "--timeout", "600",
    ]
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
    os.chdir(WEBCHAT_DIR)
    threading.Thread(target=lambda: http.server.HTTPServer(
        ("127.0.0.1", WEBCHAT_PORT),
        http.server.SimpleHTTPRequestHandler
    ).serve_forever(), daemon=True).start()
    for _ in range(3):
        if is_port_open(WEBCHAT_PORT): return "ready"
        time.sleep(1)
    return "timeout"

def start_gateway():
    if is_port_open(18789):
        return "already running"

    # Find openclaw CLI and start directly (no Scheduled Task)
    import shutil
    openclaw_cmd = shutil.which("openclaw") or shutil.which("openclaw.cmd")
    if not openclaw_cmd:
        openclaw_cmd = os.path.expandvars(r"%APPDATA%\npm\openclaw.cmd")

    # Resolve the actual gateway entry point — node + dist/index.js
    node_exe = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
    gateway_js = os.path.expandvars(
        r"%APPDATA%\npm\node_modules\openclaw\dist\index.js"
    )

    if not os.path.isfile(gateway_js):
        return "gateway dist not found"

    print(f"[daemon]   Starting gateway directly: {node_exe} {gateway_js} gateway --port 18789")

    subprocess.Popen(
        [node_exe, gateway_js, "gateway", "--port", "18789"],
        cwd=os.path.expandvars(r"%USERPROFILE%\.openclaw"),
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(20):
        if is_port_open(18789): return "ready"
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
    "Live2D Bridge": start_live2d,
    "Artemis Bridge": start_bridge,
    "OpenClaw Gateway": start_gateway,
    "Task Board": start_task_board,
    "WebChat": start_webchat,
}

SERVICE_KILLERS = {
    "llama-server": "llama-server.exe",
    "Embedding": "python.exe",
    "Live2D Bridge": "node.exe",
    "Artemis Bridge": "python.exe",
    "OpenClaw Gateway": "node.exe",
    "Task Board": "python.exe",
    "WebChat": None,  # WebChat runs in daemon thread, can't kill separately
}

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


def _inject_system_prompt(messages, character_id, custom_system_prompt=None):
    """Ensure a system message is first in the messages list.
    If the first message is already a system message, replace it.
    Otherwise, insert a new system message at the beginning.
    
    Priority: custom_system_prompt > harem file > root SOUL.md
    """
    if custom_system_prompt:
        prompt = custom_system_prompt.strip()
    else:
        prompt = _build_system_prompt(character_id)
    
    if not prompt:
        return messages
    
    result = list(messages)  # shallow copy
    if result and result[0].get("role") == "system":
        result[0] = {"role": "system", "content": prompt}
    else:
        result.insert(0, {"role": "system", "content": prompt})
    return result


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

        if path == "/api/start":
            results = daemon_instance.start_all_services()
            self.send_json({"ok": True, "results": results})
            return

        if path == "/api/stop":
            msg = stop_all()
            self.send_json({"ok": True, "message": msg})
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

        if path == "/api/chat":
            self._handle_chat_proxy()
            return

        if path == "/api/gen-prompt":
            self._handle_gen_prompt()
            return

        if path == "/api/debug-llama":
            self._handle_debug_llama()
            return

        cl = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(cl).decode("utf-8") if cl else "{}"
        try:
            data = json.loads(body)
        except:
            data = {}

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
            process_name = SERVICE_KILLERS.get(name)
            if process_name is None:
                self.send_json({"ok": False, "error": f"Service '{name}' cannot be stopped individually (runs in daemon)"})
            elif process_name:
                try:
                    subprocess.run(["taskkill", "/F", "/IM", process_name], capture_output=True, timeout=5)
                    self.send_json({"ok": True, "result": f"Killed {process_name}"})
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

    def _handle_chat_proxy(self):
        body_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(body_len)
        try:
            req_data = json.loads(body)
        except Exception:
            self.send_json({"error": "Invalid JSON"}, 400)
            return

        # Run the upstream request in a background thread so this handler
        # can stream the response without blocking the whole server loop.
        from threading import Thread, Event

        model_id = req_data.get("model", "local/qwen3.6-35b")
        messages = req_data.get("messages", [])
        stream = req_data.get("stream", False)
        max_tokens = req_data.get("max_tokens", 4096)
        character_id = req_data.get("characterId", "natsume")
        custom_system_prompt = req_data.get("systemPrompt", None)  # imported characters pass their own prompt

        # Inject system prompt from custom/harem/SOUL.md
        messages = _inject_system_prompt(messages, character_id, custom_system_prompt)

        # Local llama: skip provider lookup, use hardcoded endpoint
        if model_id.startswith("local/"):
            api_key = ""
            auth_header = ""  # no auth needed (--api-key breaks llama-server)
            base_url = "http://127.0.0.1:8080/v1"
            # llama.cpp server's model name is the full gguf filename
            backend_model = "Qwen3.6-35B-A3B-uncensored-heretic-APEX-I-Compact.gguf"
        else:
            provider_cfg = _resolve_provider_for_model(model_id)
            if not provider_cfg:
                self.send_json({"error": f"Unknown model: {model_id}"}, 400)
                return
            api_key = provider_cfg.get("apiKey", "")
            auth_header = "Bearer " + api_key
            base_url = provider_cfg.get("baseUrl", "").rstrip("/")
            backend_model = model_id.split("/")[-1]

        endpoint = base_url + "/chat/completions"
        payload = {"model": backend_model, "messages": messages, "stream": stream, "max_tokens": max_tokens}

        error_evt = Event()
        error_msg = [None]

        def upstream():
            try:
                import urllib.request, urllib.error
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(endpoint, data=data,
                    headers=({"Authorization": auth_header, "Content-Type": "application/json"} if auth_header else {"Content-Type": "application/json"}))
                resp = urllib.request.urlopen(req, timeout=120)
                return resp, None
            except Exception as e:
                error_msg[0] = str(e)
                error_evt.set()
                return None, e

        # Send response headers now (we'll stream as data arrives)
        try:
            import urllib.request
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(endpoint, data=data,
                headers=({"Authorization": auth_header, "Content-Type": "application/json"} if auth_header else {"Content-Type": "application/json"}))
        except Exception as e:
            self.send_json({"error": str(e)}, 502)
            return

        # Open upstream in the same thread. If it hangs for > 120 s the
        # client will time out (Python HTTP server will not kill the
        # upstream, but urllib timeout handles it).
        try:
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

    def _handle_gen_prompt(self):
        """Use LLM to generate a ComfyUI image prompt from conversation context."""
        body_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(body_len)
        try:
            req_data = json.loads(body)
        except Exception:
            self.send_json({"error": "Invalid JSON"}, 400)
            return

        character_id = req_data.get("characterId", "natsume")
        messages = req_data.get("messages", [])

        # Get character name for the prompt instruction
        char_name = character_id.capitalize()
        # Try to get display name from harem
        identity_path = os.path.join(WORKSPACE, "skills", "harem", character_id, "IDENTITY.md")
        if os.path.isfile(identity_path):
            try:
                with open(identity_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("- Name:") or line.strip().startswith("* **Name:**"):
                            # Extract name
                            char_name = line.split(":", 1)[1].strip()
                            # Remove parenthetical English
                            import re
                            char_name = re.sub(r"\s*[（(][^)）]*[)）]", "", char_name).strip()
                            break
            except Exception:
                pass

        # Build the instruction for LLM
        instruction = f"""You are an AI prompt engineer for image generation. Based on the conversation context below, generate a ComfyUI/Stable Diffusion prompt for the character "{char_name}".

Rules:
- Output ONLY a JSON object with "prompt" and "negative" fields, nothing else.
- The prompt should be in English, detailed, include character appearance, clothing, setting, mood, lighting.
- Use tags like: masterpiece, best quality, 1girl, {character_id}, highly detailed, etc.
- Describe the current scene/mood based on the conversation. If no specific scene is mentioned, create a beautiful portrait.
- The negative prompt should cover common issues: bad quality, worst quality, blurry, distorted, lowres, bad anatomy, extra fingers, watermark, text, ugly, deformed.
- Keep the prompt under 300 characters.

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

        # Call local LLM (non-streaming)
        try:
            import urllib.request, urllib.error
            payload = {
                "model": "Qwen3.6-35B-A3B-uncensored-heretic-APEX-I-Compact.gguf",
                "messages": [{"role": "user", "content": instruction}],
                "stream": False,
                "max_tokens": 300,
                "temperature": 0.7,
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                "http://127.0.0.1:8080/v1/chat/completions",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            resp = urllib.request.urlopen(req, timeout=30)
            result = json.loads(resp.read())
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Parse JSON from response
            # Try to find JSON block
            import re
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                prompt_data = json.loads(json_match.group())
                self.send_json({
                    "prompt": prompt_data.get("prompt", ""),
                    "negative": prompt_data.get("negative", "bad quality, worst quality, blurry"),
                })
            else:
                # Fallback: treat the whole response as prompt
                prompt_text = content.strip().strip('"').strip("'")
                if len(prompt_text) > 500:
                    prompt_text = prompt_text[:500]
                self.send_json({
                    "prompt": prompt_text,
                    "negative": "bad quality, worst quality, blurry, distorted, lowres, bad anatomy, extra fingers, watermark, text",
                })
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.send_json({"error": f"LLM prompt generation failed: {e}\n{tb[-500:]}"}, 502)

    def _handle_media_proxy(self):
        """Proxy local file paths so the browser can load generated images."""
        # The file path comes after ? in the URL, e.g. /api/media?C:/Users/.../image.png
        # parse_qs won't work because file paths don't have key=value format
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
        if not os.path.isfile(file_path):
            self.send_error(404)
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
        body_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(body_len)
        try:
            req_data = json.loads(body)
        except Exception:
            self.send_json({"error": "Invalid JSON"}, 400)
            return

        model_id = req_data.get("model", "local/qwen3.6-35b")
        messages = req_data.get("messages", [])
        stream = req_data.get("stream", False)

        # Resolve backend
        if model_id.startswith("local/"):
            api_key = ""
            base_url = "http://127.0.0.1:8080/v1"
            backend_model = "Qwen3.6-35B-A3B-uncensored-heretic-APEX-I-Compact.gguf"
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
    """Simple file server for web-chat"""
    import http.server
    os.chdir(WEBCHAT_DIR)
    server = ThreadingWebChatServer(("127.0.0.1", WEBCHAT_PORT),
        http.server.SimpleHTTPRequestHandler)
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
