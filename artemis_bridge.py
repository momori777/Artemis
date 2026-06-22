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
COMFYUI_PYTHON = CFG["comfyui_python"]
MEDIA_AUDIO = CFG.get("media_qqbot_audio", os.path.join(WORKSPACE_ROOT, "media", "qqbot", "audio"))
MEDIA_IMAGES = CFG.get("media_qqbot_images", os.path.join(WORKSPACE_ROOT, "media", "qqbot", "images"))

# Detect available TTS characters
TTs_DIR = os.path.join(WORKSPACE_ROOT, "skills", "tts")
AVAILABLE_CHARACTERS = {}
for entry in os.listdir(TTs_DIR):
    if entry.startswith("ref_wavs") and os.path.isdir(os.path.join(TTs_DIR, entry)):
        wavs = [f for f in os.listdir(os.path.join(TTs_DIR, entry)) if f.endswith('.wav')]
        if wavs:
            name = entry.replace("ref_wavs_", "").replace("ref_wavs", "natsume")
            AVAILABLE_CHARACTERS[name] = os.path.join(TTs_DIR, entry)
if not AVAILABLE_CHARACTERS:
    AVAILABLE_CHARACTERS["natsume"] = os.path.join(TTs_DIR, "ref_wavs")

# Flask app
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Job store
jobs = {}
jobs_lock = threading.Lock()

# ================================================================
# Routes
# ================================================================

@app.route("/api/status")
def api_status():
    return jsonify({
        "ok": True,
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

            cmd = [TTs_PYTHON, TTs_SCRIPT, text, lang, mood, "--no-manage-llama"]
            proc = subprocess.run(cmd, capture_output=True, text=False, timeout=120,
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
    width = int(data.get("width", 1200))
    height = int(data.get("height", 1500))
    steps = int(data.get("steps", 30))
    cfg = float(data.get("cfg", 6.0))
    checkpoint = data.get("checkpoint", "WAI-Nsfw-Illustrious-17.safetensors")

    if not positive:
        return jsonify({"error": "positive prompt is required"}), 400

    job_id = "comfyui_" + uuid.uuid4().hex[:8]
    with jobs_lock:
        jobs[job_id] = {"status": "running", "type": "comfyui", "created": time.time()}

    def run_comfyui():
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"

            cmd = [COMFYUI_PYTHON, COMFYUI_SCRIPT,
                   positive, negative, str(-1),
                   str(width), str(height), str(steps), str(cfg),
                   checkpoint, "--no-manage-llama"]

            proc = subprocess.run(cmd, capture_output=True, text=False, timeout=600,
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
                with jobs_lock:
                    jobs[job_id] = {"status": "done", "type": "comfyui", "path": img_path,
                                    "elapsed": time.time() - jobs[job_id]["created"]}
            else:
                with jobs_lock:
                    jobs[job_id] = {"status": "failed", "type": "comfyui",
                                    "error": stderr_out[-300:] or "No output generated"}
        except Exception as e:
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
