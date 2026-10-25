#!/usr/bin/env python3
"""
Artemis Bridge — HTTP API for TTS + ComfyUI
============================================
Lightweight Flask server that wraps tts_call.py and comfyui_call.py
for the web-chat frontend.

Run separately from Artemis Studio GUI (both can coexist).

Usage:
    python artemis_bridge.py [--port 19250]
    http://localhost:19250/

Endpoints:
    GET  /api/status
    POST /api/tts       { text, lang, mood, character }
    POST /api/comfyui   { positive, negative, width, height, steps, cfg, checkpoint }
    GET  /api/media/<path>  -- serve generated files
"""

import sys, os, json, time, subprocess, glob, threading, uuid
from datetime import datetime

WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORKSPACE_ROOT)

# Load config
import yaml
with open(os.path.join(WORKSPACE_ROOT, "config.yaml"), "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)

TTs_SCRIPT = os.path.join(WORKSPACE_ROOT, "skills", "tts", "tts_call.py")
TTs_PYTHON = CFG["sovits_python"]
COMFYUI_SCRIPT = os.path.join(WORKSPACE_ROOT, "skills", "comfyui", "comfyui_call.py")
COMFYUI_WORKFLOW_SCRIPT = os.path.join(WORKSPACE_ROOT, "skills", "comfyui", "comfyui_workflow_run.py")
COMFYUI_PYTHON = CFG["comfyui_python"]

# Named API-format workflow presets (server mode, custom-node capable)
WORKFLOW_PRESETS = {
    "qwen2.1": os.path.join(WORKSPACE_ROOT, "skills", "comfyui", "qwen image2.1", "qwen-image-2.1-api.json"),
    "qwen-image-2.1": os.path.join(WORKSPACE_ROOT, "skills", "comfyui", "qwen image2.1", "qwen-image-2.1-api.json"),
}
# Directory where workflows imported from webchat are stored (UI or API format;
# comfyui_workflow_run.py converts UI format on the fly).
WORKFLOW_DIR = os.path.join(WORKSPACE_ROOT, "skills", "comfyui", "workflows")
MEDIA_AUDIO = CFG.get("media_qqbot_audio", os.path.join(WORKSPACE_ROOT, "media", "qqbot", "audio"))
MEDIA_IMAGES = CFG.get("media_qqbot_images", os.path.join(WORKSPACE_ROOT, "media", "qqbot", "images"))
SKILL_TIMEOUT = int(CFG.get("skill_timeout", 9000))  # unified from config.yaml

# VRAM level scheduling — decides whether skills should stop/restart llama
from skills.shared.vram import get_vram_level, should_stop_llama as _should_stop_llama

# Detect available TTS characters
TTs_DIR = os.path.join(WORKSPACE_ROOT, "skills", "tts")

# Map charId (frontend) to ref_wavs directory name (some have different spelling)
CHAR_ID_TO_REF = {
    "natsume": "natsume",
    "atori": "atri",
    "sakura": "sakura",
    "enola": "enola",
    "ruruka": "ruruka",
}

AVAILABLE_CHARACTERS = {}
for entry in os.listdir(TTs_DIR):
    if entry.startswith("ref_wavs") and os.path.isdir(os.path.join(TTs_DIR, entry)):
        wavs = [f for f in os.listdir(os.path.join(TTs_DIR, entry)) if f.endswith('.wav')]
        if wavs:
            # Extract the actual name by stripping the ref_wavs_ prefix
            if entry.startswith("ref_wavs_"):
                name = entry[len("ref_wavs_"):]
            elif entry.startswith("ref_wavs"):
                name = entry[len("ref_wavs"):].lstrip("_")
            else:
                name = entry
            if not name:
                name = "natsume"  # fallback
            # Register under the directory-derived name
            AVAILABLE_CHARACTERS[name] = os.path.join(TTs_DIR, entry)
            # Also register under all CHAR_ID_TO_REF aliases that map to this name
            for cid, cref in CHAR_ID_TO_REF.items():
                if cref == name and cid != name:
                    AVAILABLE_CHARACTERS[cid] = os.path.join(TTs_DIR, entry)
                # Also register when the directory name itself is an alias target
                if cid in CHAR_ID_TO_REF.values() and cref == name and cid != name:
                    pass  # already registered above
            # Register the directory-derived name as a character ID too if it exists
            # This handles cases like "atri" directory → character "atori" can use "atri" too
            if name not in CHAR_ID_TO_REF.values():
                # It's a direct name match, no extra alias needed
                pass
if not AVAILABLE_CHARACTERS:
    # Fallback: use ref_wavs directly or natsume
    fb_dir = os.path.join(TTs_DIR, "ref_wavs")
    if os.path.isdir(fb_dir):
        AVAILABLE_CHARACTERS["natsume"] = fb_dir
    else:
        # Create a placeholder so the app doesn't crash
        AVAILABLE_CHARACTERS["natsume"] = TTs_DIR

# Flask app
from flask import Flask, request, jsonify, send_file, send_from_directory
try:
    from flask_cors import CORS
except ImportError:
    CORS = None

app = Flask(__name__)
if CORS:
    CORS(app)
else:
    # Manual CORS fallback — missing flask_cors must not crash the bridge
    # (a dead bridge makes the webchat UI show "failed to fetch").
    @app.after_request
    def _add_cors_headers(resp):
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

# Job store
jobs = {}
jobs_lock = threading.Lock()

# ================================================================
# Llama health check & recovery
# ================================================================

LLAMA_PORT = CFG.get("llama_port", 9931)
LLAMA_EXE = CFG.get("llama_exe", "")
LLAMA_MODEL = CFG.get("llama_model", "")
LLAMA_LOG_DIR = CFG.get("llama_log_dir", WORKSPACE_ROOT)
LLAMA_RESTART_SCRIPT = CFG.get("restart_script", "")
STRATA_PORT = int(CFG.get("strata_port", 0) or 0)
STRATA_DIR = CFG.get("strata_dir", "")


def _strata_configured():
    return bool(STRATA_PORT and STRATA_DIR and os.path.isdir(STRATA_DIR))


def _is_strata_running():
    """True if the Strata engine answers /health on strata_port."""
    if not _strata_configured():
        return False
    try:
        import urllib.request
        req = urllib.request.Request(
            f"http://127.0.0.1:{STRATA_PORT}/health", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def _is_llama_running():
    """True if the resident LLM engine (Strata or llama.cpp) is responsive."""
    if _is_strata_running():
        return True
    try:
        import urllib.request
        req = urllib.request.Request(
            f"http://127.0.0.1:{LLAMA_PORT}/health", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False



def _ensure_llama_running():
    """Check if llama is alive after ComfyUI; restart if not."""
    if _is_llama_running():
        print("[Bridge] llama-server: alive \u2713", flush=True)
        return True

    print("[Bridge] LLM engine down after ComfyUI, restarting...", flush=True)

    # ===== Step 1: VRAM reclaim first, THEN start the engine =====
    _release_vram_before_llama()

    # ===== Step 2a: Strata is the resident engine on this machine =====
    if _strata_configured():
        try:
            _def = WORKSPACE_ROOT
            if _def not in sys.path:
                sys.path.insert(0, _def)
            from skills.shared.llama_lifecycle import start_strata
            for attempt in range(3):
                if attempt > 0:
                    wait = 10 + attempt * 10
                    print(f"[Bridge] Strata retry {attempt + 1}/3 after {wait}s...", flush=True)
                    time.sleep(wait)
                    _release_vram_before_llama()
                if start_strata(port=STRATA_PORT, timeout=300, cfg=CFG):
                    print("[Bridge] Strata: restarted successfully", flush=True)
                    return True
            print("[Bridge] Strata: all restart attempts failed", flush=True)
        except Exception as e:
            print(f"[Bridge] Strata restart error: {e}", flush=True)

    # ===== Step 2b: fall back to llama.cpp =====
    try:
        _def = WORKSPACE_ROOT
        if _def not in sys.path:
            sys.path.insert(0, _def)
        from skills.shared.llama_lifecycle import start_llama

        for attempt in range(3):
            if attempt > 0:
                wait = 10 + attempt * 10
                print(f"[Bridge] Retry {attempt + 1}/3 after {wait}s...", flush=True)
                time.sleep(wait)
                _release_vram_before_llama()

            ok = start_llama(
                port=LLAMA_PORT,
                exe_path=LLAMA_EXE,
                model_path=LLAMA_MODEL,
                log_dir=LLAMA_LOG_DIR,
                timeout=180,
                use_mmap=True,  # after ComfyUI: avoid --no-mmap full-VK-alloc OOM
            )
            if ok:
                print("[Bridge] llama-server: restarted successfully", flush=True)
                return True

        print("[Bridge] llama-server: all restart attempts failed", flush=True)
    except Exception as e:
        print(f"[Bridge] llama restart error: {e}", flush=True)

    # Fallback: try the restart script
    if LLAMA_RESTART_SCRIPT and os.path.isfile(LLAMA_RESTART_SCRIPT):
        try:
            print("[Bridge] Trying restart script fallback...", flush=True)
            subprocess.Popen(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", LLAMA_RESTART_SCRIPT],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(30)
            if _is_llama_running():
                print("[Bridge] Restart script succeeded", flush=True)
                return True
        except Exception:
            pass

    print("[Bridge] CRITICAL: llama-server could not be recovered!", flush=True)
    return False


def _gpu_free_mib():
    """Read free VRAM via nvidia-smi (read-only).

    NOTE: never import torch in the bridge process — it would create a CUDA
    context (~300MB) inside the long-lived bridge and *consume* VRAM while
    trying to measure it.
    """
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return float(r.stdout.strip().splitlines()[0])
    except Exception:
        pass
    return None


def _release_vram_before_llama():
    """Wait for the GPU driver to reclaim VRAM before restarting llama-server.

    ComfyUI runs as a subprocess and has already released its own CUDA
    context by the time we get here; the driver frees it asynchronously.
    We only observe via nvidia-smi and wait until free VRAM stops rising.
    """
    free = _gpu_free_mib()
    print(f"[Bridge] VRAM free now: {free if free is not None else 'unknown'} MiB", flush=True)
    if free is None:
        time.sleep(10)  # nvidia-smi unavailable: conservative fixed wait
        return

    prev = free
    for sec in (5, 10, 15):
        time.sleep(5)
        free = _gpu_free_mib()
        if free is None:
            break
        print(f"[Bridge] VRAM after {sec}s: {free:.0f} MiB", flush=True)
        if free - prev < 50:  # stabilized — driver reclaim finished
            break
        prev = free


@app.route("/api/status")
def api_status():
    return jsonify({
        "ok": True,
        "llama": "online" if _is_llama_running() else "offline",
        "characters": list(AVAILABLE_CHARACTERS.keys()),
        "checkpoints": ["WAI-Nsfw-Illustrious-17.safetensors", "miaomiaoHarem_v20.safetensors"],
    })

@app.route("/api/tts", methods=["POST"])
def api_tts():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    lang = data.get("lang", "ja")
    mood = data.get("mood", "casual")
    character = data.get("character", "")

    if not text:
        return jsonify({"error": "text is required"}), 400

    job_id = "tts_" + uuid.uuid4().hex[:8]
    with jobs_lock:
        jobs[job_id] = {"status": "running", "type": "tts", "created": time.time()}

    def run_tts():
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"

            ref_dir = AVAILABLE_CHARACTERS.get(character)
            if ref_dir:
                env["REF_WAVS_DIR"] = ref_dir
            if character:
                env["TTS_CHARACTER"] = character

            cmd = [TTs_PYTHON, TTs_SCRIPT, text, lang, mood]
            # VRAM level decides: only keep llama alive when the level says so
            if not _should_stop_llama("tts"):
                cmd.append("--no-manage-llama")
            proc = subprocess.run(cmd, capture_output=True, text=False, timeout=SKILL_TIMEOUT,
                                 cwd=WORKSPACE_ROOT, env=env)

            stdout_text = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
            stderr_out = proc.stderr.decode("utf-8", errors="replace") if proc.stderr else ""

            # Find output wav
            wav_path = None
            for line in reversed(stdout_text.strip().splitlines()):
                line = line.strip()
                if line.endswith('.wav') and os.path.exists(line):
                    wav_path = line
                    break
            if not wav_path:
                candidates = glob.glob(os.path.join(MEDIA_AUDIO, "*.wav"))
                if candidates:
                    wav_path = max(candidates, key=os.path.getmtime)

            if wav_path and os.path.exists(wav_path):
                with jobs_lock:
                    jobs[job_id] = {"status": "done", "type": "tts", "path": wav_path,
                                    "elapsed": time.time() - jobs[job_id]["created"]}
            else:
                with jobs_lock:
                    jobs[job_id] = {"status": "failed", "type": "tts",
                                    "error": stderr_out[-300:] or "No output generated"}
        except Exception as e:
            with jobs_lock:
                jobs[job_id] = {"status": "failed", "type": "tts", "error": str(e)}

    threading.Thread(target=run_tts, daemon=True).start()
    return jsonify({"job_id": job_id, "status": "running"})

@app.route("/api/comfyui", methods=["POST"])
def api_comfyui():
    data = request.get_json(silent=True) or {}
    positive = data.get("positive", "").strip()
    negative = data.get("negative", "")
    width = int(data.get("width", 768))                                                
    height = int(data.get("height", 1024))                                              
    steps = int(data.get("steps", 24))                                                
    cfg = float(data.get("cfg", 6.0))
    checkpoint = data.get("checkpoint", "WAI-Nsfw-Illustrious-17.safetensors")
    workflow = (data.get("workflow") or "").strip()  # named preset or path to API-format json

    if not positive:
        return jsonify({"error": "positive prompt is required"}), 400

    if workflow and not os.path.isabs(workflow):
        workflow = WORKFLOW_PRESETS.get(workflow.lower(), workflow)
        if not os.path.isabs(workflow):
            cand = os.path.join(WORKFLOW_DIR, workflow + ("" if workflow.lower().endswith(".json") else ".json"))
            if os.path.isfile(cand):
                workflow = cand
    if workflow and not os.path.isfile(workflow):
        return jsonify({"error": f"workflow json not found: {workflow}"}), 400

    # manage_llama=True → stop llama before ComfyUI (default, safer)
    # manage_llama=False → keep llama alive, risk OOM on low VRAM
    # VRAM level overrides: ALL_ONLINE (level 2) never stops llama
    manage_llama = bool(data.get("manage_llama", True)) and _should_stop_llama("comfyui")

    job_id = "comfyui_" + uuid.uuid4().hex[:8]
    with jobs_lock:
        jobs[job_id] = {"status": "running", "type": "comfyui", "created": time.time()}

    def run_comfyui():
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"

            if workflow:
                cmd = [COMFYUI_PYTHON, COMFYUI_WORKFLOW_SCRIPT,
                       positive, negative, str(-1),
                       str(width), str(height), str(steps), str(cfg),
                       "--workflow", workflow]
            else:
                cmd = [COMFYUI_PYTHON, COMFYUI_SCRIPT,
                       positive, negative, str(-1),
                       str(width), str(height), str(steps), str(cfg),
                       checkpoint]
            if not manage_llama:
                cmd.append("--no-manage-llama")

            proc = subprocess.run(cmd, capture_output=True, text=False, timeout=SKILL_TIMEOUT,
                                 cwd=WORKSPACE_ROOT, env=env)

            stdout_text = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
            stderr_out = proc.stderr.decode("utf-8", errors="replace") if proc.stderr else ""

            img_path = None
            for line in reversed(stdout_text.strip().splitlines()):
                line = line.strip()
                if line.endswith('.png') and os.path.exists(line):
                    img_path = line
                    break

            comfyui_temp = CFG.get("comfyui_temp_output_dir", "")
            if not img_path and comfyui_temp:
                candidates = glob.glob(os.path.join(comfyui_temp, "comfyui_*.png"))
                if candidates:
                    img_path = max(candidates, key=os.path.getmtime)

            if img_path and os.path.exists(img_path):
                # Copy to media dir so it persists and is accessible via daemon proxy
                import shutil
                media_images = MEDIA_IMAGES if os.path.isdir(MEDIA_IMAGES) else os.path.join(WORKSPACE_ROOT, "media", "qqbot", "images")
                os.makedirs(media_images, exist_ok=True)
                media_name = "comfyui_" + job_id + ".png"
                media_path = os.path.join(media_images, media_name)
                try:
                    shutil.copy2(img_path, media_path)
                    persist_path = media_path  # Use persistent copy for frontend
                except Exception:
                    persist_path = img_path  # Fallback to original if copy fails
                # After successful image generation, check llama health
                if manage_llama:
                    _ensure_llama_running()
                with jobs_lock:
                    jobs[job_id] = {"status": "done", "type": "comfyui", "path": persist_path,
                                    "elapsed": time.time() - jobs[job_id]["created"]}
            else:
                # Don't leak full stderr to frontend — find last error line
                error_msg = "No output generated"
                for line in reversed(stderr_out.strip().splitlines()):
                    line = line.strip()
                    if line and ("rror" in line or "Error" in line or "FAIL" in line or "fail" in line):
                        error_msg = line[-200:]
                        break
                # Even on failure, try to recover llama
                if manage_llama:
                    _ensure_llama_running()
                with jobs_lock:
                    jobs[job_id] = {"status": "failed", "type": "comfyui",
                                    "error": error_msg}
        except Exception as e:
            # On exception, still try to recover llama
            if manage_llama:
                _ensure_llama_running()
            with jobs_lock:
                jobs[job_id] = {"status": "failed", "type": "comfyui", "error": str(e)}

    threading.Thread(target=run_comfyui, daemon=True).start()
    return jsonify({"job_id": job_id, "status": "running"})

@app.route("/api/jobs/<job_id>")
def api_job_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    return jsonify(dict(job, job_id=job_id))

def _list_workflows():
    """Presets + imported workflows in WORKFLOW_DIR (UI or API format json)."""
    items = []
    seen = set()
    for name, path in sorted(WORKFLOW_PRESETS.items()):
        rp = os.path.realpath(path)
        if rp in seen:
            continue
        seen.add(rp)
        items.append({"name": name, "preset": True,
                      "file": os.path.basename(path),
                      "mtime": int(os.path.getmtime(path)) if os.path.isfile(path) else 0})
    if os.path.isdir(WORKFLOW_DIR):
        for fn in sorted(os.listdir(WORKFLOW_DIR), key=str.lower):
            if not fn.lower().endswith(".json"):
                continue
            full = os.path.join(WORKFLOW_DIR, fn)
            rp = os.path.realpath(full)
            if rp in seen:
                continue
            seen.add(rp)
            items.append({"name": os.path.splitext(fn)[0], "preset": False,
                          "file": fn, "mtime": int(os.path.getmtime(full))})
    return items

@app.route("/api/workflows")
def api_workflows():
    return jsonify({"workflows": _list_workflows()})

@app.route("/api/workflow/import", methods=["POST"])
def api_workflow_import():
    """Import a ComfyUI workflow exported from the webchat side.

    Body: {"name": optional, "json": <UI or API format workflow object or string>}.
    UI format ({"nodes","links"}) is validated/converted server-side; both
    formats are stored under WORKFLOW_DIR and the runner converts on use."""
    data = request.get_json(silent=True) or {}
    raw = data.get("json")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception as e:
            return jsonify({"error": f"invalid json: {e}"}), 400
    if not isinstance(raw, dict):
        return jsonify({"error": "json must be a workflow object"}), 400
    is_ui = "nodes" in raw
    if not is_ui and not any(isinstance(v, dict) and "class_type" in v for v in raw.values()):
        return jsonify({"error": "not a ComfyUI workflow (neither UI nor API format)"}), 400
    if is_ui:
        import sys as _sys
        conv_dir = os.path.join(WORKSPACE_ROOT, "skills", "comfyui")
        if conv_dir not in _sys.path:
            _sys.path.insert(0, conv_dir)
        try:
            from workflow_convert import ui_to_api
            api_graph, warnings = ui_to_api(raw)
        except Exception as e:
            return jsonify({"error": f"UI workflow conversion failed: {e}"}), 400
        if not any(n["class_type"] in ("KSampler", "KSamplerAdvanced") for n in api_graph.values()):
            return jsonify({"error": "workflow has no KSampler node"}), 400
    name = (data.get("name") or "").strip()
    if not name:
        name = os.path.splitext(os.path.basename(str(data.get("filename") or "")))[0].strip()
    name = "".join(c for c in name if c.isalnum() or c in "-_ .")[:60] or \
        "wf_" + uuid.uuid4().hex[:8]
    os.makedirs(WORKFLOW_DIR, exist_ok=True)
    path = os.path.join(WORKFLOW_DIR, name + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False)
    return jsonify({"ok": True, "name": name,
                    "format": "ui" if is_ui else "api",
                    "workflows": _list_workflows()})


@app.route("/api/media/<path:filepath>")
def serve_media(filepath):
    """Serve generated media files by full path encoding"""
    # Decode the path
    decoded = filepath
    # Try different base directories
    for base in [MEDIA_AUDIO, MEDIA_IMAGES, CFG.get("comfyui_temp_output_dir", ""),
                 os.path.join(WORKSPACE_ROOT, "media")]:
        if not base: continue
        full = os.path.join(base, os.path.basename(decoded))
        if os.path.isfile(full):
            return send_file(full)

    # Try direct path
    # Security: only allow paths under known media dirs
    normalized = os.path.abspath(decoded)
    allowed_roots = [os.path.abspath(p) for p in [MEDIA_AUDIO, MEDIA_IMAGES,
                     CFG.get("comfyui_temp_output_dir", ""), os.path.join(WORKSPACE_ROOT, "media")]
                     if p]
    for root in allowed_roots:
        try:
            if normalized.startswith(root) and os.path.isfile(normalized):
                return send_file(normalized)
        except: pass

    return jsonify({"error": "file not found"}), 404

@app.route("/api/restart-llama", methods=["POST"])
def api_restart_llama():
    """Manually restart llama-server (recovery endpoint)."""
    if _is_llama_running():
        return jsonify({"ok": True, "message": "llama-server already running"})
    ok = _ensure_llama_running()
    if ok:
        return jsonify({"ok": True, "message": "llama-server restarted"})
    return jsonify({"ok": False, "error": "Failed to restart llama-server"}), 500

# ================================================================
# Main
# ================================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Artemis Bridge API")
    parser.add_argument("--port", type=int, default=19250, help="HTTP port (default: 19250)")
    args = parser.parse_args()

    print(f"[Artemis Bridge] Starting on http://localhost:{args.port}")
    print(f"[Artemis Bridge] TTS characters: {list(AVAILABLE_CHARACTERS.keys())}")
    print(f"[Artemis Bridge] ComfyUI python: {COMFYUI_PYTHON}")
    app.run(host="127.0.0.1", port=args.port, debug=False, threaded=True)
