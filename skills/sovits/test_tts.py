import sys
import os
os.environ["TORCHAUDIO_BACKEND"] = "sox"
import torchaudio

# Test if torchaudio can load with sox backend
audio_path = "logs/xxx/5-wav32k/DLsite Play.mp3.reformatted_vocals.flac_0000304640_0000413120.wav"
try:
    waveform, sr = torchaudio.load(audio_path, backend="sox")
    print(f"Loaded successfully: sr={sr}, shape={waveform.shape}")
except Exception as e:
    print(f"Failed: {e}")
    sys.exit(1)

# Now test full TTS API
import requests
import json

url = "http://127.0.0.1:9880/tts"
payload = {
    "text": "你好，我是四季夏目。今天过得怎么样？",
    "text_lang": "zh",
    "ref_audio_path": audio_path,
    "prompt_text": "",
    "prompt_lang": "zh",
    "top_k": 5,
    "top_p": 0.9,
    "temperature": 0.7,
    "speed": 1,
    "repetition_penalty": 1.1,
    "media_type": "wav"
}

resp = requests.post(url, json=payload)
print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
print(f"Body length: {len(resp.content)} bytes")
if resp.headers.get("Content-Type", "").startswith("application/json"):
    print(f"Response: {resp.text}")
else:
    out_path = "test_output.wav"
    with open(out_path, "wb") as f:
        f.write(resp.content)
    print(f"Audio saved to {out_path}")
