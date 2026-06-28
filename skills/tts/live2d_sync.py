#!/usr/bin/env python3
"""
TTS → Live2D Lip-Sync Bridge
─────────────────────────────
When TTS generates audio, this module sends the audio to the Live2D bridge
so the frontend plays it with real audio-driven lip-sync.

Usage (from tts_call.py or any TTS caller):
    from skills.tts.live2d_sync import sync_audio_to_live2d
    sync_audio_to_live2d(wav_path, text="hello")

This calls the Live2D bridge's /api/speak_audio endpoint which:
1. Caches the WAV file
2. Broadcasts a WS message to the frontend with the audio URL
3. Frontend fetches it, decodes with Web Audio API, and does real lip-sync
"""

import sys
import os
import urllib.request
import urllib.parse
import urllib.error
import time

BRIDGE_URL = "http://localhost:19200"


def _is_bridge_online(timeout=2):
    """Check if Live2D bridge is running."""
    try:
        urllib.request.urlopen(
            f"{BRIDGE_URL}/api/status",
            timeout=timeout
        )
        return True
    except (urllib.error.URLError, OSError):
        return False


def sync_audio_to_live2d(wav_path, text="", wait_for_end=True):
    """
    Send a TTS-generated WAV to the Live2D bridge for lip-synced playback.

    Args:
        wav_path: Full path to the .wav file
        text: The text being spoken (for display, optional)
        wait_for_end: If True, poll and wait until playback ends

    Returns:
        dict with keys: ok (bool), audio_url (str), message (str)
    """
    if not os.path.exists(wav_path):
        return {"ok": False, "message": f"WAV not found: {wav_path}"}

    if not _is_bridge_online():
        return {"ok": False, "message": "Live2D bridge not running"}

    # Encode text for URL
    safe_text = urllib.parse.quote(text or "", safe="")

    # Start playback
    try:
        params = urllib.parse.urlencode({
            "action": "start",
            "audio_path": wav_path,
            "text": text or "",
        })
        url = f"{BRIDGE_URL}/api/speak_audio?{params}"
        resp = urllib.request.urlopen(url, timeout=10)
        result = resp.read().decode("utf-8")
        import json
        data = json.loads(result)

        if not data.get("ok"):
            return {"ok": False, "message": data.get("error", "Unknown error")}

        audio_url = data.get("audio_url", "")

        if wait_for_end:
            # Poll the bridge — audio playback is tracked by the frontend
            # We estimate duration from WAV file size (~176KB/s for 16-bit 22050Hz mono)
            file_size = os.path.getsize(wav_path)
            estimated_duration = file_size / (22050 * 2)  # 16-bit mono = 2 bytes/sample
            # Wait with some buffer
            wait_sec = max(estimated_duration + 2.0, 3.0)
            time.sleep(wait_sec)

        return {"ok": True, "audio_url": audio_url, "message": "sent to Live2D"}

    except urllib.error.URLError as e:
        return {"ok": False, "message": f"Bridge request failed: {e}"}
    except Exception as e:
        return {"ok": False, "message": str(e)}


def end_speak():
    """Send speak_end to Live2D bridge (stops lip-sync)."""
    if not _is_bridge_online():
        return {"ok": False, "message": "Live2D bridge not running"}

    try:
        url = f"{BRIDGE_URL}/api/speak_audio?action=end"
        urllib.request.urlopen(url, timeout=5)
        return {"ok": True, "message": "speak ended"}
    except Exception as e:
        return {"ok": False, "message": str(e)}


# ---- CLI for testing ----
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Send TTS audio to Live2D for lip-sync")
    parser.add_argument("wav_path", help="Path to WAV file")
    parser.add_argument("--text", "-t", default="", help="Text being spoken")
    parser.add_argument("--no-wait", action="store_true", help="Don't wait for playback to finish")
    args = parser.parse_args()

    result = sync_audio_to_live2d(args.wav_path, args.text, wait_for_end=not args.no_wait)
    print(result)
