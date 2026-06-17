"""
Lightweight OpenAI-compatible embedding server for OpenClaw memory search.
Serves all-MiniLM-L6-v2 (384-dim) on http://127.0.0.1:9999/v1/embeddings

Usage:
    python embedding_server.py

Uses the model cached in skills/sakura/runtime/hf-cache/ if available,
otherwise downloads to the same cache directory.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path

# ── Configure model cache ────────────────────────────────
WORKSPACE = Path(os.environ.get(
    "OPENCLAW_WORKSPACE",
    os.path.expandvars(r"%USERPROFILE%\.openclaw\workspace")
))
HF_CACHE = WORKSPACE / "skills" / "sakura" / "runtime" / "hf-cache"
os.environ.setdefault("HF_HOME", str(HF_CACHE))
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(HF_CACHE))

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
PORT = 9999
HOST = "127.0.0.1"

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [embed] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("embed-server")

# ── Lazy load model to keep startup fast ──────────────────
_model = None

def get_model():
    global _model
    if _model is None:
        log.info(f"Loading embedding model: {MODEL_NAME}")
        log.info(f"HF cache: {os.environ['HF_HOME']}")
        from sentence_transformers import SentenceTransformer
        # Force offline mode to avoid HuggingFace connection issues in China
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        _model = SentenceTransformer(
            MODEL_NAME,
            cache_folder=str(HF_CACHE),
            local_files_only=True,
        )
        log.info("Model loaded successfully")
    return _model

# ── Flask app ─────────────────────────────────────────────
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/v1/embeddings", methods=["POST"])
def embeddings():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    model_name = data.get("model", MODEL_NAME)
    input_data = data.get("input")

    if input_data is None:
        return jsonify({"error": "input field is required"}), 400

    # Normalize input to list of strings
    if isinstance(input_data, str):
        texts = [input_data]
    elif isinstance(input_data, list):
        texts = [str(t) for t in input_data]
    else:
        return jsonify({"error": "input must be string or array of strings"}), 400

    if not texts:
        return jsonify({"error": "input cannot be empty"}), 400

    # Generate embeddings
    try:
        model = get_model()
        vectors = model.encode(texts, normalize_embeddings=True)
    except Exception as e:
        log.error(f"Embedding failed: {e}")
        return jsonify({"error": str(e)}), 500

    # Format response
    data_out = []
    for i, vec in enumerate(vectors):
        data_out.append({
            "object": "embedding",
            "index": i,
            "embedding": vec.tolist(),
        })

    return jsonify({
        "object": "list",
        "data": data_out,
        "model": model_name,
        "usage": {
            "prompt_tokens": sum(len(t.split()) for t in texts),
            "total_tokens": sum(len(t.split()) for t in texts),
        },
    })

@app.route("/v1/models", methods=["GET"])
def models():
    return jsonify({
        "object": "list",
        "data": [{"id": MODEL_NAME, "object": "model"}],
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service": "embedding-server",
        "model": MODEL_NAME,
        "dimensions": 384,
        "endpoint": "/v1/embeddings",
    })


def main():
    log.info(f"Starting embedding server on {HOST}:{PORT}")
    log.info(f"Model: {MODEL_NAME}")
    log.info("Preloading model...")
    get_model()  # Preload
    log.info(f"Ready! Listening on http://{HOST}:{PORT}/v1/embeddings")
    app.run(host=HOST, port=PORT, threaded=True, use_reloader=False)

if __name__ == "__main__":
    main()
