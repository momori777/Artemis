#!/usr/bin/env python3
"""
GPT-SoVITS HTTP TTS 调用脚本 — 不停 llama 版本
用法: python tts_http_call.py "目标文本" "语言代码" [情绪模式] [参考音频路径]

核心改进：
1. 通过 HTTP API 调用 GPT-SoVITS（端口 9880），不停 llama
2. 自动启动 GPT-SoVITS HTTP 服务（如果未运行）
3. 参考音频自动选择（与 tts_call.py 逻辑一致）
4. 音频音量归一化
5. 输出 wav 文件路径到 stdout

依赖：GPT-SoVITS 需要在端口 9880 上提供 HTTP TTS API
      首次运行会自动启动：python GPT_SoVITS/inference_webui.py --port 9880
"""
import sys
import os
import time
import json
import random
import re
import urllib.request
import urllib.error
import subprocess
import tempfile

# --- 路径配置 ---
_def = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_path = os.path.join(_def, 'config.yaml')

def _load_config():
    if not os.path.exists(config_path):
        print(f"[ERROR] 找不到 config.yaml: {config_path}", file=sys.stderr)
        sys.exit(1)
    import yaml
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

_cfg = _load_config()

# ========== 路径配置 ==========
SOVITS_ROOT = _cfg['sovits_root']
OUTPUT_DIR = _cfg['tts_temp_output_dir']
LOCK_FILE = os.path.join(OUTPUT_DIR, ".tts_http_running.lock")

# ========== 文本到情绪模式的映射规则 ==========
TEXT_MOODS = {
    "casual": [
        "おはよう", "お疲れ", "ありがとう", "がんば", "大変", "仕事",
        "今日", "また", "さあ", "さて", "もう", "ちゃんと", "しっかり",
    ],
    "tsundere": [
        "キモ", "変態", "変な", "いいわ", "しない", "大丈夫", "おやすみ",
        "だって", "しょうがない", "バカ", "うるさい", "ふん", "哼", "笨蛋",
        "哼", "随便你", "我才没有", "别以为", "哼", "ふん",
    ],
    "romantic": [
        "好き", "大好き", "愛", "君のこと", "あなた", "幸せ", "エッチ",
        "気持ちいい", "大好き", "愛してる", "大好きよ", "宝贝", "老公",
        "喜欢你", "我爱你", "想你", "爱你", "永远",
    ],
}

MOOD_MAP = {
    "日常": "casual", "casual": "casual",
    "傲娇": "tsundere", "tsundere": "tsundere", "困惑": "tsundere",
    "深情": "romantic", "romantic": "romantic",
    "长句": "long", "long": "long",
}

# ========== 参考音频目录 ==========
_tts_dir = os.path.dirname(os.path.abspath(__file__))


def _detect_character():
    """检测当前活跃角色名（从 workspace 的 SOUL.md）"""
    ws_root = os.path.join(_tts_dir, "..", "..")
    soul_path = os.path.join(ws_root, "SOUL.md")
    if os.path.exists(soul_path):
        with open(soul_path, "r", encoding="utf-8") as f:
            first = f.readline().strip()
        m = re.match(r"^# SOUL\.md\s*-\s*(.+)$", first)
        if m:
            return m.group(1).strip().lower().replace(" ", "-")
    return None


def _resolve_ref_dir():
    """根据活跃角色解析参考音频目录。"""
    chara = _detect_character()
    if chara:
        chara_dir = os.path.join(_tts_dir, f"ref_wavs_{chara}")
        if os.path.isdir(chara_dir) and os.listdir(chara_dir):
            return chara_dir
    return os.path.join(_tts_dir, "ref_wavs")


def _load_ref_waves(ref_dir):
    """扫描参考音频目录，按文件名约定归类。"""
    ref_waves = {"casual": [], "tsundere": [], "romantic": [], "long": []}
    if not os.path.isdir(ref_dir):
        return ref_waves
    for fname in sorted(os.listdir(ref_dir)):
        if not fname.lower().endswith(".wav"):
            continue
        fpath = os.path.join(ref_dir, fname)
        stem = os.path.splitext(fname)[0]
        parts = stem.split("_")
        mood = None
        for p in parts:
            if p in MOOD_MAP:
                mood = MOOD_MAP[p]
                break
        if mood is None:
            mood = "casual"
        txt_path = os.path.join(ref_dir, stem + ".txt")
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                ref_text = f.read().strip()
        else:
            text_parts = []
            capture = False
            for p in parts:
                if capture:
                    text_parts.append(p)
                elif p in MOOD_MAP:
                    capture = True
            ref_text = " ".join(text_parts) if text_parts else stem
        ref_waves[mood].append({
            "path": fpath,
            "text": ref_text,
            "lang": "ja",
        })
    return ref_waves


REF_DIR = _resolve_ref_dir()
REF_WAVES = _load_ref_waves(REF_DIR)

REF_INDEX = {}
for mood, items in REF_WAVES.items():
    for item in items:
        basename = os.path.basename(item["path"])
        REF_INDEX[basename] = item


def pick_ref(text, mood_hint):
    """根据文本内容和情绪提示选择参考音频。"""
    if mood_hint and mood_hint in REF_WAVES:
        refs = REF_WAVES[mood_hint]
        if refs:
            return random.choice(refs)

    text_lower = text.lower()
    scores = {}
    for mood, keywords in TEXT_MOODS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[mood] = score

    max_score = max(scores.values())
    if max_score > 0:
        candidates = [m for m, s in scores.items() if s == max_score]
        mood = random.choice(candidates)
        refs = REF_WAVES[mood]
        if refs:
            return random.choice(refs)

    all_refs = []
    for group in REF_WAVES.values():
        all_refs.extend(group)
    if all_refs:
        return random.choice(all_refs)
    return None


def lookup_ref_info(ref_path):
    """查找参考音频的信息（文本和语言）"""
    basename = os.path.basename(ref_path)
    info = REF_INDEX.get(basename)
    if info:
        return info["text"], info["lang"]
    return "", "ja"


def slugify(text, max_len=20):
    """从文本提取安全文件名标签"""
    cleaned = re.sub(r'[^\w\u4e00-\u9fff ]', ' ', text, flags=re.ASCII)
    cleaned = re.sub(r'\s+', '_', cleaned).strip('_')
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip('_')
    return cleaned or 'untitled'


# ========== GPT-SoVITS HTTP 服务管理 ==========
TTS_HTTP_PORT = 9880
TTS_API_URL = f"http://127.0.0.1:{TTS_HTTP_PORT}/tts"


def _find_sovits_runtime_python():
    """查找 GPT-SoVITS 的 Python 解释器。"""
    # config.yaml 中指定
    sovits_python = _cfg.get('sovits_python')
    if sovits_python and os.path.exists(sovits_python):
        return sovits_python

    # 尝试系统 python（sovits 的依赖已安装到系统环境）
    for py in ['python', 'python3']:
        try:
            result = subprocess.run([py, '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return py
        except Exception:
            pass
    return 'python'


def _probe_service(timeout=3):
    """探测 GPT-SoVITS HTTP 服务是否可用。"""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{TTS_HTTP_PORT}/")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True
    except Exception:
        return False


def _start_sovits_service():
    """启动 GPT-SoVITS HTTP 服务（如果未运行）。"""
    if _probe_service():
        print("[SOVITS] HTTP 服务已在运行", file=sys.stderr)
        return True

    runtime_python = _find_sovits_runtime_python()
    print(f"[SOVITS] 正在启动 HTTP 服务 (python={runtime_python})", file=sys.stderr)

    # 查找 inference_webui.py
    webui_path = None
    for root, dirs, files in os.walk(SOVITS_ROOT):
        if 'inference_webui.py' in files:
            webui_path = os.path.join(root, 'inference_webui.py')
            break

    if webui_path is None:
        # 尝试在 site-packages 中找
        import site
        for sp_dir in site.getsitepackages():
            candidate = os.path.join(sp_dir, 'GPT_SoVITS', 'inference_webui.py')
            if os.path.exists(candidate):
                webui_path = candidate
                break

    if webui_path is None:
        print("[SOVITS] 找不到 inference_webui.py，尝试直接从 site-packages 调用", file=sys.stderr)
        # 使用 -c 方式启动
        cmd = [
            runtime_python, '-c',
            f'import sys; sys.path.insert(0, r"{SOVITS_ROOT}"); '
            f'from GPT_SoVITS.inference_webui import *; '
            f'webui( port={TTS_HTTP_PORT} )'
        ]
    else:
        cmd = [runtime_python, webui_path, f'--port', str(TTS_HTTP_PORT)]

    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(webui_path) if webui_path else SOVITS_ROOT,
        env=env,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
    )

    # 等待服务就绪
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if _probe_service():
            print(f"[SOVITS] HTTP 服务启动成功 (PID={proc.pid})", file=sys.stderr)
            # 保存进程引用供后续清理
            _save_pid(proc.pid)
            return True
        time.sleep(2)

    print(f"[SOVITS] 服务启动超时 (PID={proc.pid})", file=sys.stderr)
    _save_pid(proc.pid)
    return False


def _save_pid(pid):
    """保存 PID 用于后续清理。"""
    pid_file = os.path.join(OUTPUT_DIR, ".tts_http_service.pid")
    with open(pid_file, 'w') as f:
        f.write(str(pid))


# ========== 音量归一化 ==========
def normalize_audio_wav(input_path, output_path):
    """读取 wav 文件，归一化音量到正常水平，写回。"""
    try:
        import numpy as np
        import scipy.io.wavfile as wavfile

        sr, audio = wavfile.read(input_path)
        original_max = np.max(np.abs(audio))
        if original_max > 0 and original_max < 10000:
            gain = 25000.0 / original_max
            audio_float = audio.astype(np.float32) * gain
            audio = np.clip(audio_float, -32768, 32767).astype(np.int16)
            wavfile.write(output_path, sr, audio)
            print(f"Applied gain: {gain:.2f}x (original max: {original_max})", file=sys.stderr)
            return output_path
        return input_path
    except Exception as e:
        print(f"[WARN] 音量归一化失败: {e}", file=sys.stderr)
        return input_path


# ========== 主流程 ==========
text = sys.argv[1]
lang = sys.argv[2] if len(sys.argv) > 2 else "ja"
mood_hint = sys.argv[3] if len(sys.argv) > 3 else None
ref_wav_arg = sys.argv[4] if len(sys.argv) > 4 else None

# 自动选择参考音频
ref_path = None
ref_prompt_text = ""
ref_prompt_lang = "ja"

if ref_wav_arg:
    ref_path = ref_wav_arg
    ref_prompt_text, ref_prompt_lang = lookup_ref_info(ref_path)
else:
    ref_pick = pick_ref(text, mood_hint)
    if ref_pick:
        ref_path = ref_pick["path"]
        ref_prompt_text = ref_pick["text"]
        ref_prompt_lang = ref_pick["lang"]

if not ref_path:
    # fallback: 用第一个可用的参考音频
    all_refs = []
    for group in REF_WAVES.values():
        all_refs.extend(group)
    if all_refs:
        ref_path = all_refs[0]["path"]
        ref_prompt_text = all_refs[0]["text"]
        ref_prompt_lang = all_refs[0]["lang"]

print(f"Selected ref: {os.path.basename(ref_path) if ref_path else 'none'}", file=sys.stderr)
print(f"Prompt text: {ref_prompt_text}", file=sys.stderr)
print(f"Prompt lang: {ref_prompt_lang}", file=sys.stderr)

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 启动 GPT-SoVITS HTTP 服务
if not _start_sovits_service():
    print("[ERROR] GPT-SoVITS HTTP 服务启动失败", file=sys.stderr)
    sys.exit(1)

# 构建 HTTP 请求
lang_map = {"zh": "zh", "ja": "ja", "en": "en", "yue": "yue", "ko": "ko"}
text_lang = lang_map.get(lang, "ja")

# 构造 GPT-SoVITS HTTP 请求体（与 inference_webui.py 兼容）
# 参考: https://github.com/RVC-Boss/GPT-SoVITS 的 HTTP API
payload = {
    "text": text,
    "text_language": text_lang,
    "how_to_cut": "不切",
    "prompt_text": ref_prompt_text or "",
    "prompt_language": ref_prompt_lang,
    "prompt_audio_path": ref_path or "",
}

body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

print(f"[TTS] 发送请求到 {TTS_API_URL}", file=sys.stderr)
req = urllib.request.Request(
    url=TTS_API_URL,
    data=body,
    method="POST",
    headers={"Content-Type": "application/json"},
)

# 发送请求，获取音频
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        audio_data = resp.read()
except urllib.error.URLError as e:
    print(f"[ERROR] HTTP 请求失败: {e}", file=sys.stderr)
    sys.exit(1)
except TimeoutError:
    print("[ERROR] HTTP 请求超时", file=sys.stderr)
    sys.exit(1)

if not audio_data:
    print("[ERROR] 收到空音频响应", file=sys.stderr)
    sys.exit(1)

# 写入临时文件并归一化音量
tmp_wav = None
final_wav = None
try:
    tmp_wav = tempfile.NamedTemporaryFile(
        prefix="tts_http_", suffix=".wav", delete=False, dir=OUTPUT_DIR
    )
    tmp_wav.write(audio_data)
    tmp_wav.close()

    # 归一化音量
    tag = slugify(text)
    final_name = f"tts_http_{tag}_{random.randint(10000, 99999)}.wav"
    final_wav = os.path.join(OUTPUT_DIR, final_name)
    normalize_audio_wav(tmp_wav.name, final_wav)

    print(f"[DONE] {final_wav}", file=sys.stdout)
    print(final_wav)
    sys.stdout.flush()

except Exception as e:
    print(f"[ERROR] 音频处理失败: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    if tmp_wav and os.path.exists(tmp_wav.name) and tmp_wav.name != final_wav:
        try:
            os.unlink(tmp_wav.name)
        except OSError:
            pass
