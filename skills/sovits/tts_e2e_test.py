#!/usr/bin/env python3
"""End-to-end GPT-SoVITS smoke test against api_v2 (http://127.0.0.1:9880).

For each character it hot-swaps the voice weights (/set_gpt_weights +
/set_sovits_weights, resolved from weight_<char>.json) and synthesizes a short
line through /tts, then verifies the returned bytes are a real, audible wav
(frames > 0 and peak amplitude above a noise floor).

Usually launched by skills/sovits/tts_handoff_run.ps1 (the GPU handoff job that
pauses the LLM engine first); it can also be called by hand while api_v2 runs:

    python skills/sovits/tts_e2e_test.py --only atori,natsume

No hardcoded absolute paths: everything comes from repo-root config.yaml.
Results are written as UTF-8 JSON to --report so the caller never has to parse
stdout (Windows console codepages eat CJK).
"""

import argparse
import array
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import wave

HERE = os.path.dirname(os.path.abspath(__file__))          # <repo>/skills/sovits
REPO = os.path.dirname(os.path.dirname(HERE))              # repo root
TTS_DIR = os.path.join(REPO, "skills", "tts")
BASE_DEFAULT = "http://127.0.0.1:9880"

# Ref sidecars: <ref>.txt next to the wav holds the word-for-word prompt text.
# A missing sidecar is a hard error in synth(): the fixed policy for this repo is
# "reference audio always ships with its transcript" (see skills/asr/asr_sidecars.py).
TESTS = [
    {
        "id": "atori-ja",
        "character": "atri",
        "lang": "ja",
        "ref": "ref_01_日常_おはよう.wav",
        "text": "阿陶，今日もいっしょに海へ行こうね。アトリは、阿陶といっしょなら、どこでもたのしいよ。",
    },
    {
        "id": "atori-zh",
        "character": "atri",
        "lang": "zh",
        "ref": "ref_01_日常_おはよう.wav",
        "text": "阿陶，今天也一起去看海嘛。只要是和你在一起，去哪里都好。",
    },
    {
        "id": "natsume-ja",
        "character": "natsume",
        "lang": "ja",
        "ref": "ref_06_傲娇_変なこと.wav",
        "text": "阿陶、おそい。……別に、まってたりしないけど。",
    },
    {
        "id": "natsume-zh",
        "character": "natsume",
        "lang": "zh",
        "ref": "ref_06_傲娇_変なこと.wav",
        "text": "阿陶，你怎么才来呀。我才没有一直等着你呢。",
    },
]


def analyze_wav(path):
    """Return (rate, channels, sample_width, payload, kind) for a wav file.

    `kind` is "pcm" or "f" (32-bit float payload). GPT-SoVITS usually writes
    PCM-16, but soundfile may emit IEEE float; `wave` chokes on the latter, so
    fall back to a minimal RIFF walk instead of reporting a false failure.
    """
    try:
        with wave.open(path, "rb") as w:
            rate, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
            frames = w.readframes(w.getnframes())
        return rate, ch, sw, frames, "pcm"
    except Exception:
        pass
    with open(path, "rb") as fh:
        blob = fh.read()
    if len(blob) < 44 or blob[:4] != b"RIFF" or blob[8:12] != b"WAVE":
        raise RuntimeError("response is not a wav file (%d bytes)" % len(blob))
    rate = ch = sw = 2
    bits = 16
    audio_fmt = 1
    pos, data = 12, b""
    while pos + 8 <= len(blob):
        cid = blob[pos:pos + 4]
        clen = int.from_bytes(blob[pos + 4:pos + 8], "little")
        body = blob[pos + 8:pos + 8 + clen]
        if cid == b"fmt " and len(body) >= 16:
            audio_fmt = int.from_bytes(body[0:2], "little")
            ch = int.from_bytes(body[2:4], "little") or 1
            rate = int.from_bytes(body[4:8], "little") or 32000
            bits = int.from_bytes(body[14:16], "little") or 16
            sw = max(1, bits // 8)
        elif cid == b"data":
            data = body
        pos += 8 + clen + (clen % 2)
    kind = "f" if (audio_fmt == 3 and bits == 32) else "pcm"
    if not data:  # some writers put the payload right after the header
        data = blob[44:]
    return rate, ch, sw, data, kind


def load_cfg():
    """Top-level `key: value` pairs from repo-root config.yaml (flat subset)."""
    cfg = {}
    path = os.path.join(REPO, "config.yaml")
    if not os.path.isfile(path):
        return cfg
    with io.open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if line[0] in (" ", "\t", "-"):
                continue
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and val:
                cfg[key] = val
    return cfg


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def resolve_weights(character):
    """weight_<char>.json -> (abs gpt path, abs sovits path)."""
    wjson = os.path.join(HERE, "weight_%s.json" % character)
    if not os.path.isfile(wjson):
        raise SystemExit("weight json not found: %s" % wjson)
    spec = read_json(wjson)
    gpt_rel = spec.get("GPT", {}).get("v2", "")
    sov_rel = spec.get("SoVITS", {}).get("v2", "")
    out = []
    for rel in (gpt_rel, sov_rel):
        if not rel:
            raise SystemExit("weight_%s.json is missing a v2 path" % character)
        found = None
        for base in (HERE, os.path.join(HERE, "weights")):
            cand = rel if os.path.isabs(rel) else os.path.join(base, rel)
            if os.path.isfile(cand):
                found = cand
                break
        if not found:
            raise SystemExit("weight file missing on disk: %s" % rel)
        out.append(found)
    return out[0], out[1]


def get(url, timeout=600):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def wait_ready(base, timeout=600):
    """api_v2 has no `/` route; /docs is the cheap liveness probe."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if get(base + "/docs", timeout=5):
                return True
        except Exception:
            time.sleep(3)
    return False


def set_weights(base, character):
    gpt, sov = resolve_weights(character)
    res = {}
    for ep, path in (("/set_gpt_weights", gpt), ("/set_sovits_weights", sov)):
        url = "%s%s?weights_path=%s" % (base, ep, urllib.parse.quote(path))
        t0 = time.time()
        body = get(url)
        if '"success"' not in body:
            raise RuntimeError("%s failed: %s" % (ep, body[:200]))
        res[ep] = {"path": path, "seconds": round(time.time() - t0, 1)}
    return res


def synth(base, case, ref_dir, out_dir):
    ref = os.path.join(ref_dir, case["ref"])
    if not os.path.isfile(ref):
        raise RuntimeError("reference audio not found: %s" % ref)
    # Fixed policy: reference audio must ship with its verbatim transcript.
    # GPT-SoVITS v2/v2Pro silently degrades to voice-only cloning when
    # prompt_text is empty (flat prosody, stretched sentences), and v3/v4
    # hard-fails with NO_PROMPT_ERROR, so the smoke test refuses to run
    # without a sidecar instead of reporting a green-but-wrong result.
    sidecar = os.path.splitext(ref)[0] + ".txt"
    if not os.path.isfile(sidecar):
        raise RuntimeError(
            "reference transcript missing: %s (write the word-for-word text "
            "of the clip into this file, e.g. with skills/asr/asr_sidecars.py)"
            % sidecar
        )
    with io.open(sidecar, "r", encoding="utf-8-sig") as fh:
        prompt_text = fh.read().strip().lstrip("\ufeff").strip()
    if not prompt_text:
        raise RuntimeError("reference transcript is empty: %s" % sidecar)
    payload = {
        "text": case["text"],
        "text_lang": case["lang"],
        "ref_audio_path": ref,
        "prompt_text": prompt_text,
        "prompt_lang": "ja",
        "text_split_method": "cut5",
        "batch_size": 1,
        "media_type": "wav",
        "streaming_mode": False,
        "seed": 622539,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        base + "/tts",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            audio = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise RuntimeError("HTTP %s from /tts: %s" % (exc.code, detail))
    elapsed = round(time.time() - t0, 1)
    if len(audio) < 1000:
        raise RuntimeError("suspiciously small response (%d bytes): %r" % (len(audio), audio[:120]))

    out_path = os.path.join(out_dir, "e2e_%s.wav" % case["id"])
    with open(out_path, "wb") as fh:
        fh.write(audio)

    rate, ch, sw, frames, fmt = analyze_wav(out_path)
    dur = round(len(frames) / float(max(1, rate * ch * sw)), 2)
    peak = 0
    if fmt == "f":  # 32-bit float payload -> report in int16 units
        smp = array.array("f")
        smp.frombytes(frames[: len(frames) - (len(frames) % 4)])
        peak = int(max((abs(s) for s in smp), default=0.0) * 32767)
    elif sw == 2:
        smp = array.array("h")
        smp.frombytes(frames[: len(frames) - (len(frames) % 2)])
        peak = max((abs(s) for s in smp), default=0)
    return {
        "wav": out_path,
        "bytes": len(audio),
        "seconds": dur,
        "sample_rate": rate,
        "peak": peak,
        "elapsed_s": elapsed,
        "ref": ref,
        "prompt_text": prompt_text,
        "prompt_mode": "text" if prompt_text else "no_prompt_text",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=BASE_DEFAULT)
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--report", default="")
    ap.add_argument("--skip-wait", action="store_true")
    args = ap.parse_args()

    cfg = load_cfg()
    base = os.environ.get("SOVITS_API", args.base).rstrip("/")
    out_dir = args.out or cfg.get("tts_temp_output_dir") or os.path.join(REPO, "media", "qqbot", "audio")
    os.makedirs(out_dir, exist_ok=True)
    report_path = args.report or os.path.join(HERE, "tts_e2e_result.json")

    wanted = [t.strip() for t in args.only.split(",") if t.strip()]
    cases = [c for c in TESTS if not wanted or c["id"] in wanted or c["character"] in wanted]

    report = {
        "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "base": base,
        "out_dir": out_dir,
        "weights": {},
        "cases": [],
        "ok": 0,
        "fail": 0,
    }

    def flush():
        report["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        with io.open(report_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)

    if not args.skip_wait and not wait_ready(base, timeout=900):
        report["fatal"] = "api_v2 not answering on %s" % base
        flush()
        print("FAIL: %s" % report["fatal"])
        return 1

    loaded = set()
    for case in cases:
        entry = dict(case)
        try:
            key = case["character"]
            if key not in loaded:
                report["weights"][key] = set_weights(base, key)
                loaded.add(key)
            entry.update(synth(base, case, os.path.join(TTS_DIR, "ref_wavs_%s" % key), out_dir))
            if entry["seconds"] < 0.4 or entry["peak"] < 200:
                entry["ok"] = False
                entry["error"] = "audio too short/quiet (seconds=%s peak=%s)" % (entry["seconds"], entry["peak"])
                report["fail"] += 1
            else:
                entry["ok"] = True
                report["ok"] += 1
        except Exception as exc:  # keep going: one bad voice must not hide the others
            entry["ok"] = False
            entry["error"] = "%s: %s" % (type(exc).__name__, exc)
            report["fail"] += 1
        report["cases"].append(entry)
        flush()
        print("%s %s %s%s" % ("PASS" if entry.get("ok") else "FAIL", entry["id"], entry.get("wav", ""), (" | " + entry["error"]) if entry.get("error") else ""))
    flush()
    print("SUMMARY ok=%d fail=%d report=%s" % (report["ok"], report["fail"], report_path))
    return 0 if report["fail"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
