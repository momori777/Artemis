"""
llama 调试面板后端 — 轻量 HTTP API + 进程管理
启动: python server.py (默认 http://127.0.0.1:8765)
"""
import os, sys, json, subprocess, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ── 路径解析 ──
BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(BASE)
CONFIG = os.path.join(PROJECT, "data", "llama_debugger_config.json")
LOG_DIR = os.path.join(PROJECT, "data", "llama_debugger_logs")
LLAMA_SERVER = os.path.join(PROJECT, "llama-server", "llama-server.exe")
STATIC_DIR = BASE

os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ── 配置 ──
DEFAULT_CONFIG = {
    "model": "",
    "gpu_layers": -1,
    "threads": -1,
    "threads_batch": -1,
    "ctx_size": 0,
    "predict": -1,
    "batch_size": 2048,
    "ubatch_size": 512,
    "keep": 0,
    "flash_attn": "auto",
    "kv_offload": True,
    "mmap": True,
    "mlock": False,
    "temp": 0.80,
    "top_k": 40,
    "top_p": 0.95,
    "min_p": 0.05,
    "xtc_probability": 0.00,
    "xtc_threshold": 0.10,
    "typical_p": 1.00,
    "repeat_last_n": 64,
    "repeat_penalty": 1.00,
    "presence_penalty": 0.00,
    "frequency_penalty": 0.00,
    "mirostat": 0,
    "mirostat_lr": 0.10,
    "mirostat_ent": 5.00,
    "seed": -1,
    "rope_scaling": "linear",
    "rope_scale": 1.0,
    "rope_freq_base": 0,
    "rope_freq_scale": 1.0,
    "numa": "",
    "cpu_prio": 0,
    "poll": 50,
    "log_verbosity": 3,
    "log_colors": "auto",
    "lora": "",
    "control_vector": "",
    "spec_type": "none",
    "spec_draft_model": "",
    "spec_draft_ngl": -1,
    "json_schema_file": "",
    "override_kv": "",
    "device": "",
    "split_mode": "layer",
    "tensor_split": "",
    "main_gpu": 0,
    "fit": True,
    "fit_target": 1024,
    "fit_ctx": 4096,
    "swa_full": False,
    "repack": True,
    "log_prefix": False,
    "log_timestamps": False,
    "offline": False,
}

def load_config():
    if os.path.exists(CONFIG):
        try:
            with open(CONFIG, "r", encoding="utf-8") as f:
                user = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in user:
                    user[k] = v
            return user
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)

def save_config(cfg):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

# ── 进程管理 ──
llama_proc = None
llama_log_file = None
llama_log_lock = threading.Lock()
_log_lines = []
_start_time = 0

def start_llama(cfg):
    global llama_proc, llama_log_file, _log_lines, _start_time
    if llama_proc and llama_proc.poll() is None:
        return {"ok": False, "msg": "llama-server already running", "pid": llama_proc.pid}

    model = cfg.get("model", "").strip()
    if not model:
        return {"ok": False, "msg": "model path is empty"}

    log_path = os.path.join(LOG_DIR, "llama_server.log")
    with llama_log_lock:
        _log_lines = []

    args = [LLAMA_SERVER, "-m", model, "--log-disable"]

    # GPU
    if cfg.get("gpu_layers", -1) != -1:
        args += ["--gpu-layers", str(cfg["gpu_layers"])]
    if cfg.get("device"):
        args += ["--device", cfg["device"]]
    if cfg.get("split_mode") != "layer":
        args += ["--split-mode", cfg["split_mode"]]
    if cfg.get("tensor_split"):
        args += ["--tensor-split", cfg["tensor_split"]]
    if cfg.get("main_gpu", 0) != 0:
        args += ["--main-gpu", str(cfg["main_gpu"])]

    # CPU/Threads
    if cfg.get("threads", -1) != -1:
        args += ["--threads", str(cfg["threads"])]
    if cfg.get("threads_batch", -1) != -1:
        args += ["--threads-batch", str(cfg["threads_batch"])]
    if cfg.get("cpu_prio", 0) != 0:
        args += ["--prio", str(cfg["cpu_prio"])]
    if cfg.get("poll", 50) != 50:
        args += ["--poll", str(cfg["poll"])]

    # Context
    if cfg.get("ctx_size", 0) != 0:
        args += ["--ctx-size", str(cfg["ctx_size"])]
    if cfg.get("predict", -1) != -1:
        args += ["--n-predict", str(cfg["predict"])]
    if cfg.get("batch_size", 2048) != 2048:
        args += ["--batch-size", str(cfg["batch_size"])]
    if cfg.get("ubatch_size", 512) != 512:
        args += ["--ubatch-size", str(cfg["ubatch_size"])]
    if cfg.get("keep", 0) != 0:
        args += ["--keep", str(cfg["keep"])]

    # Memory
    if cfg.get("flash_attn") != "auto":
        args += ["--flash-attn", cfg["flash_attn"]]
    if not cfg.get("kv_offload", True):
        args += ["--no-kv-offload"]
    if not cfg.get("mmap", True):
        args += ["--no-mmap"]
    if cfg.get("mlock", False):
        args += ["--mlock"]

    # Sampling
    args += ["--temp", str(cfg["temp"])]
    if cfg.get("top_k", 40) != 40:
        args += ["--top-k", str(cfg["top_k"])]
    if cfg.get("top_p", 0.95) != 0.95:
        args += ["--top-p", str(cfg["top_p"])]
    if cfg.get("min_p", 0.05) != 0.05:
        args += ["--min-p", str(cfg["min_p"])]
    if cfg.get("xtc_probability", 0.0) != 0.0:
        args += ["--xtc-probability", str(cfg["xtc_probability"])]
    if cfg.get("xtc_threshold", 0.1) != 0.1:
        args += ["--xtc-threshold", str(cfg["xtc_threshold"])]
    if cfg.get("typical_p", 1.0) != 1.0:
        args += ["--typical-p", str(cfg["typical_p"])]
    if cfg.get("repeat_last_n", 64) != 64:
        args += ["--repeat-last-n", str(cfg["repeat_last_n"])]
    if cfg.get("repeat_penalty", 1.0) != 1.0:
        args += ["--repeat-penalty", str(cfg["repeat_penalty"])]
    if cfg.get("presence_penalty", 0.0) != 0.0:
        args += ["--presence-penalty", str(cfg["presence_penalty"])]
    if cfg.get("frequency_penalty", 0.0) != 0.0:
        args += ["--frequency-penalty", str(cfg["frequency_penalty"])]
    if cfg.get("mirostat", 0) != 0:
        args += ["--mirostat", str(cfg["mirostat"])]
        args += ["--mirostat-lr", str(cfg["mirostat_lr"])]
        args += ["--mirostat-ent", str(cfg["mirostat_ent"])]
    if cfg.get("seed", -1) != -1:
        args += ["--seed", str(cfg["seed"])]

    # RoPE
    if cfg.get("rope_scaling") != "linear":
        args += ["--rope-scaling", cfg["rope_scaling"]]
    if cfg.get("rope_scale", 1.0) != 1.0:
        args += ["--rope-scale", str(cfg["rope_scale"])]
    if cfg.get("rope_freq_base", 0) != 0:
        args += ["--rope-freq-base", str(cfg["rope_freq_base"])]
    if cfg.get("rope_freq_scale", 1.0) != 1.0:
        args += ["--rope-freq-scale", str(cfg["rope_freq_scale"])]

    # Advanced
    if cfg.get("numa"):
        args += ["--numa", cfg["numa"]]
    if cfg.get("log_verbosity", 3) != 3:
        args += ["--log-verbosity", str(cfg["log_verbosity"])]
    if cfg.get("log_colors") != "auto":
        args += ["--log-colors", cfg["log_colors"]]
    if cfg.get("log_prefix", False):
        args += ["--log-prefix"]
    if cfg.get("log_timestamps", False):
        args += ["--log-timestamps"]
    if cfg.get("offline", False):
        args += ["--offline"]
    if cfg.get("lora"):
        args += ["--lora", cfg["lora"]]
    if cfg.get("control_vector"):
        args += ["--control-vector", cfg["control_vector"]]
    if cfg.get("spec_type") != "none":
        args += ["--spec-type", cfg["spec_type"]]
    if cfg.get("spec_draft_model"):
        args += ["--spec-draft-model", cfg["spec_draft_model"]]
    if cfg.get("spec_draft_ngl", -1) != -1:
        args += ["--spec-draft-ngl", str(cfg["spec_draft_ngl"])]
    if cfg.get("json_schema_file"):
        args += ["--json-schema-file", cfg["json_schema_file"]]
    if cfg.get("override_kv"):
        args += ["--override-kv", cfg["override_kv"]]
    if cfg.get("swa_full", False):
        args += ["--swa-full"]
    if not cfg.get("repack", True):
        args += ["--no-repack"]
    if cfg.get("fit", True):
        args += ["--fit"]
    if cfg.get("fit_target", 1024) != 1024:
        args += ["--fit-target", str(cfg["fit_target"])]
    if cfg.get("fit_ctx", 4096) != 4096:
        args += ["--fit-ctx", str(cfg["fit_ctx"])]

    try:
        llama_log_file = open(log_path, "w", encoding="utf-8", buffering=1)
        llama_proc = subprocess.Popen(
            args,
            stdout=llama_log_file,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        _start_time = time.time()
        return {"ok": True, "msg": "Started", "pid": llama_proc.pid}
    except Exception as e:
        return {"ok": False, "msg": str(e)}

def stop_llama():
    global llama_proc, llama_log_file, _start_time
    if llama_proc and llama_proc.poll() is None:
        try:
            llama_proc.terminate()
            try:
                llama_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                llama_proc.kill()
        except Exception as e:
            return {"ok": False, "msg": str(e)}
    llama_proc = None
    if llama_log_file:
        try:
            llama_log_file.close()
        except:
            pass
        llama_log_file = None
    _start_time = 0
    return {"ok": True, "msg": "Stopped"}

# ── HTTP Handler ──
class Handler(BaseHTTPRequestHandler):
    def _send_json(self, data, code=200):
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length).decode("utf-8") if length > 0 else ""

    def log_message(self, fmt, *args):
        pass  # silence

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # Serve static files
        if path == "" or path == "/":
            path = "/index.html"
        if path == "/api/status":
            status = {"running": False, "pid": None, "uptime": 0}
            if llama_proc and llama_proc.poll() is None:
                status = {"running": True, "pid": llama_proc.pid, "uptime": int(time.time() - _start_time)}
            return self._send_json(status)

        if path == "/api/config":
            return self._send_json(load_config())

        if path == "/api/logs":
            with llama_log_lock:
                lines = list(_log_lines) if _log_lines else []
            # Also tail the log file if it exists
            log_path = os.path.join(LOG_DIR, "llama_server.log")
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                        file_lines = f.readlines()
                    lines = file_lines[-500:]  # last 500 lines
                except:
                    pass
            return self._send_json({"lines": lines, "tail": True})

        if path == "/api/commands":
            return self._send_json({
                "commands": [
                    {"name": "Restart with current config", "cmd": "restart"},
                    {"name": "Stop llama-server", "cmd": "stop"},
                    {"name": "Restart with default config", "cmd": "restart_default"},
                ]
            })

        # Serve static files from STATIC_DIR
        if path.startswith("/static/"):
            filename = path[8:]  # remove /static/
            filepath = os.path.join(STATIC_DIR, filename)
            if os.path.exists(filepath) and os.path.isfile(filepath):
                self._send_file(filepath)
                return
        elif os.path.exists(os.path.join(STATIC_DIR, path.lstrip("/"))):
            filepath = os.path.join(STATIC_DIR, path.lstrip("/"))
            if os.path.isfile(filepath):
                self._send_file(filepath)
                return

        self.send_error(404)

    def _send_file(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        mime_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".png": "image/png",
            ".svg": "image/svg+xml",
        }
        mime = mime_types.get(ext, "application/octet-stream")
        with open(filepath, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = self._read_body()

        if path == "/api/config":
            try:
                cfg = json.loads(body)
                save_config(cfg)
                return self._send_json({"ok": True, "msg": "Config saved"})
            except Exception as e:
                return self._send_json({"ok": False, "msg": str(e)}, 400)

        if path == "/api/command":
            try:
                data = json.loads(body) if body else {}
                cmd = data.get("cmd", "")
                if cmd == "start":
                    cfg = load_config()
                    result = start_llama(cfg)
                    return self._send_json(result)
                elif cmd == "stop":
                    return self._send_json(stop_llama())
                elif cmd == "restart":
                    cfg = load_config()
                    stop_llama()
                    time.sleep(1)
                    result = start_llama(cfg)
                    time.sleep(0.5)
                    return self._send_json(result)
                elif cmd == "restart_default":
                    cfg = dict(DEFAULT_CONFIG)
                    save_config(cfg)
                    stop_llama()
                    time.sleep(1)
                    result = start_llama(cfg)
                    time.sleep(0.5)
                    return self._send_json(result)
                else:
                    return self._send_json({"ok": False, "msg": "Unknown command"}, 400)
            except Exception as e:
                return self._send_json({"ok": False, "msg": str(e)}, 400)

        if path == "/api/import":
            try:
                data = json.loads(body) if body else {}
                imported = data.get("config", {})
                if not imported:
                    return self._send_json({"ok": False, "msg": "No config data"}, 400)
                merged = load_config()
                merged.update(imported)
                save_config(merged)
                return self._send_json({"ok": True, "msg": "Config imported"})
            except Exception as e:
                return self._send_json({"ok": False, "msg": str(e)}, 400)

        self.send_error(404)


class ThreadedHTTPServer(HTTPServer):
    """Handle each request in a new thread for concurrent log polling."""
    allow_reuse_address = True

    def process_request(self, request, client_address):
        t = threading.Thread(target=self.process_request_thread, args=(request, client_address))
        t.daemon = True
        t.start()

    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


def main():
    port = 8765
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)

    server = ThreadedHTTPServer(("0.0.0.0", port), Handler)
    print(f"llama debugger panel: http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_llama()
        server.server_close()


if __name__ == "__main__":
    main()
