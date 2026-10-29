#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Transcribe reference-audio sidecars (<stem>.wav -> <stem>.txt) for GPT-SoVITS.

GPT-SoVITS voice cloning is most stable when the reference clip ships with its
word-for-word transcript (prompt_text + prompt_lang). Without it the engine runs
in "no prompt text" mode: the timbre survives but prosody flattens and sentences
stretch. This tool fills the missing .txt sidecars automatically.

Engine: faster-whisper (CTranslate2) running on **CPU int8**.
 - CPU on purpose: the GPU is reserved for the chat engine / ComfyUI / SoVITS.
 - faster-whisper is pure Python; it reuses the CTranslate2 that already ships in
   the ComfyUI env, which Smart App Control already whitelists (no new binaries).

Usage (run with the ComfyUI interpreter, which owns ctranslate2):
    F:\\comfyui\\ComfyUI-aki-v3\\python\\python.exe skills/asr/asr_sidecars.py \
        --dir skills/tts/ref_wavs_natsume --model Systran/faster-whisper-large-v3

Options:
    --dir DIR        reference dir to scan (repeatable)
    --model NAME     CTranslate2 whisper repo id or a local path
    --lang CODE      force language (default "ja"; "auto" to detect)
    --force          rewrite sidecars that already exist
    --dry-run        print transcripts, write nothing
    --report PATH    write a JSON review sheet (default: <dir>/sidecar_report.json)

Nothing here touches llama/Strata, so it is safe to run while chat is serving.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "4")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MODEL_CACHE = os.environ.get(
    "ASR_MODEL_DIR", os.path.join(ROOT, "skills", "asr", "models")
)
DEFAULT_MODEL = "Systran/faster-whisper-large-v3"


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def duration(path: str) -> float:
    import wave

    try:
        with wave.open(path, "rb") as w:
            rate = w.getframerate()
            return w.getnframes() / rate if rate else 0.0
    except Exception:
        try:
            import soundfile as sf

            info = sf.info(path)
            return float(info.duration)
        except Exception:
            return 0.0


def decode_audio(path: str):
    """Read a wav as the float32 mono 16 kHz array whisper expects.

    Decoded with **soundfile/libsndfile** (already Smart-App-Control approved) so
    no extra native decoder (av/torchcodec) is ever loaded, and resampled with
    numpy only. Returns (numpy.ndarray, 16000).
    """
    import numpy as np
    import soundfile as sf

    data, sr = sf.read(path, dtype="float32", always_2d=True)
    data = data.mean(axis=1)
    target = 16000
    if sr != target:
        n = int(round(data.shape[0] * target / float(sr)))
        idx = np.linspace(0.0, data.shape[0] - 1, n, dtype=np.float64)
        data = np.interp(idx, np.arange(data.shape[0], dtype=np.float64), data).astype(np.float32)
    return data, target


def load_model(name: str):
    from faster_whisper import WhisperModel

    local = name if os.path.isdir(name) else os.path.join(MODEL_CACHE, name.replace("/", "__"))
    log(f"[asr] loading {name} on cpu/int8 (cache: {MODEL_CACHE})")
    t0 = time.time()
    try:
        model = WhisperModel(
            local if os.path.isdir(local) else name,
            device="cpu",
            compute_type="int8",
            download_root=MODEL_CACHE,
            cpu_threads=int(os.environ.get("OMP_NUM_THREADS", "4")),
        )
    except Exception as exc:  # noqa: BLE001
        log(f"[asr] local path failed ({exc}); retrying by repo id")
        model = WhisperModel(
            name,
            device="cpu",
            compute_type="int8",
            download_root=MODEL_CACHE,
            cpu_threads=int(os.environ.get("OMP_NUM_THREADS", "4")),
        )
    log(f"[asr] model ready in {time.time() - t0:.1f}s")
    return model


def transcribe(model, wav: str, lang: str) -> dict:
    audio, _ = decode_audio(wav)
    segments, info = model.transcribe(
        audio,
        language=None if lang == "auto" else lang,
        beam_size=5,
        temperature=0.0,
        condition_on_previous_text=False,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300},
        initial_prompt="日本語、です・ますとタメ口が混ざる日常会話。",
    )
    parts, ts = [], []
    nll_sum, nll_n = 0.0, 0
    for seg in segments:
        text = (seg.text or "").strip()
        if not text:
            continue
        parts.append(text)
        ts.append([round(seg.start, 2), round(seg.end, 2)])
        if getattr(seg, "avg_logprob", None) is not None:
            nll_sum += float(seg.avg_logprob)
            nll_n += 1
    text = "".join(parts)
    nll = (nll_sum / nll_n) if nll_n else None
    conf = None
    if nll is not None:
        import math

        conf = round(100.0 * math.exp(nll), 1)
    return {
        "text": text,
        "language": getattr(info, "language", lang),
        "language_probability": round(float(getattr(info, "language_probability", 0.0) or 0.0), 3),
        "avg_logprob": None if nll is None else round(nll, 4),
        "confidence_pct": conf,
        "segments": ts,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Fill GPT-SoVITS reference sidecars with ASR.")
    ap.add_argument("--dir", action="append", required=True, help="reference dir (repeatable)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--lang", default="ja")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    dirs = [d if os.path.isabs(d) else os.path.join(ROOT, d) for d in args.dir]
    todo = []
    for d in dirs:
        if not os.path.isdir(d):
            log(f"[asr] missing dir: {d}")
            continue
        for fname in sorted(os.listdir(d)):
            if not fname.lower().endswith(".wav"):
                continue
            stem = os.path.splitext(fname)[0]
            txt = os.path.join(d, stem + ".txt")
            if os.path.exists(txt) and not args.force:
                continue
            todo.append((os.path.join(d, fname), txt))
    if not todo:
        log("[asr] every wav already has a sidecar; nothing to do")
        return 0

    log(f"[asr] {len(todo)} clip(s) to transcribe")
    model = load_model(args.model)

    rows = []
    t_all = time.time()
    for wav, txt in todo:
        dur = duration(wav)
        t0 = time.time()
        try:
            res = transcribe(model, wav, args.lang)
        except Exception as exc:  # noqa: BLE001
            log(f"[asr] FAILED {os.path.basename(wav)}: {exc}")
            rows.append({"wav": os.path.basename(wav), "error": str(exc)})
            continue
        took = time.time() - t0
        flag = ""
        if res["confidence_pct"] is not None and res["confidence_pct"] < 60:
            flag = "  <-- LOW CONFIDENCE, verify by ear"
        elif dur and (res["text"].count("") == 0):
            flag = ""
        log(
            f"[asr] {os.path.basename(wav)} [{dur:.2f}s -> {took:.1f}s] "
            f"conf={res['confidence_pct']} lang={res['language']}{flag}\n      {res['text']}"
        )
        if not args.dry_run and res["text"]:
            with open(txt, "w", encoding="utf-8") as fh:
                fh.write(res["text"] + "\n")
        rows.append({"wav": os.path.basename(wav), "wav_seconds": round(dur, 2),
                     "asr_seconds": round(took, 2), "sidecar": txt, **res})

    report = args.report or os.path.join(dirs[0], "sidecar_report.json")
    if not args.dry_run:
        with open(report, "w", encoding="utf-8") as fh:
            json.dump({"model": args.model, "lang": args.lang,
                       "total_seconds": round(time.time() - t_all, 1), "rows": rows},
                      fh, ensure_ascii=False, indent=2)
        log(f"[asr] review sheet: {report}")
    log(f"[asr] done in {time.time() - t_all:.1f}s ({'dry-run' if args.dry_run else 'written'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
