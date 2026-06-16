#!/usr/bin/env python3
"""
ASR (Automatic Speech Recognition) — 语音转文字
================================================
基于 Faster-Whisper small 模型，不杀 llama-server（GPU 推理，不抢显存架构）。

用法:
    python asr_call.py <audio_file_path> [output_dir]

    audio_file_path: 音频文件路径（支持 wav/mp3/ogg/flac/m4a 等）
    output_dir:      输出目录（默认父目录 media/qqbot/audio）

    输出到 stdout: 识别出的文本

架构:
    - 复用 shared/llama_lifecycle.py 的锁机制，避免并发
    - 不调用 stop_llama/start_llama（Whisper 小模型不跟 llama 抢显存）
    - 模型缓存到 ~/.cache/asr_models/

依赖:
    pip install faster-whisper
"""

import sys
import os
import json
import time
import traceback
import subprocess

# ---- 国内用户 HF mirror ----
# 如果 HF 官方被墙，设置此环境变量自动走镜像
if not os.environ.get("HF_ENDPOINT"):
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# ---- 路径设置 ----
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.dirname(SCRIPT_DIR)  # skills/
WORKSPACE_DIR = os.path.dirname(SKILLS_DIR)  # project root

# 确保 shared 模块可导入
if SKILLS_DIR not in sys.path:
    sys.path.insert(0, SKILLS_DIR)

from shared.llama_lifecycle import (
    acquire_lock, release_lock,
    TimeoutGuard, register_cleanup_handlers,
)


# ---- 从 config.yaml 读取路径 ----
def _load_config():
    """读取 config.yaml 中的路径配置"""
    config_path = os.path.join(WORKSPACE_DIR, "config.yaml")
    paths = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                for key in [
                    "workspace",
                    "media_qqbot_audio",
                    "llama_port",
                    "restart_script",
                ]:
                    if line.startswith(f"{key}:"):
                        val = line.split(":", 1)[1].strip().strip('"').strip("'")
                        paths[key] = val
    return paths


_config = _load_config()

# 默认输出到 media/qqbot/audio（QQ 的音频目录）或 workspace 的 asr 子目录
MEDIA_AUDIO_DIR = _config.get("media_qqbot_audio") or os.path.join(
    WORKSPACE_DIR, "media", "qqbot", "audio"
)
ASR_OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "skills", "asr", "output")
OUTPUT_DIR = ASR_OUTPUT_DIR  # asr 使用专用输出目录

# 并行调用保护
LLAMA_PORT = int(_config.get("llama_port", 8080))
RESTART_SCRIPT = _config.get("restart_script")

# ---- 模型管理 ----
MODEL_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "asr_models")
MODEL_SIZE = "small"  # small: 461MB, ~1.5GB VRAM GPU, 较快的速度 + 较好精度

os.makedirs(MODEL_CACHE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_model(model_size=MODEL_SIZE):
    """加载 Faster-Whisper 模型（首次自动下载到缓存目录）"""
    from faster_whisper import WhisperModel

    print(f"[ASR] 加载模型 {model_size}...", file=sys.stderr, flush=True)

    # 检测是否有 GPU
    device = "cpu"
    compute_type = "float32"
    try:
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            # float16 对 GPU 推理更快，且 small 模型精度损失可忽略
            compute_type = "float16"
            free = torch.cuda.mem_get_info()[0] / (1024 ** 2)
            print(f"[ASR] CUDA 可用，VRAM free: {free:.0f} MiB",
                  file=sys.stderr, flush=True)
    except Exception:
        print("[ASR] torch 不可用，使用 CPU 推理", file=sys.stderr, flush=True)

    # 网络不通时尝试从缓存加载
    try:
        model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            download_root=MODEL_CACHE_DIR,
            local_files_only=False,
        )
    except Exception as e:
        if "ConnectTimeout" in str(e) or "LocalEntryNotFoundError" in str(e):
            print(f"[ASR] 网络不通，尝试从缓存加载...", file=sys.stderr, flush=True)
            model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                download_root=MODEL_CACHE_DIR,
                local_files_only=True,
            )
        else:
            raise

    print(f"[ASR] 模型就绪 (device={device}, compute_type={compute_type})",
          file=sys.stderr, flush=True)
    return model


def transcribe(model, audio_path):
    """
    转写音频文件为文本。

    返回 (text, info) 元组:
        text: 识别的完整文本
        info: 包含语言、时长、片段等
    """
    print(f"[ASR] 转写中: {os.path.basename(audio_path)}",
          file=sys.stderr, flush=True)

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,           # 平衡精度和速度
        vad_filter=True,       # 过滤静音段
        vad_parameters=dict(
            min_silence_duration_ms=500,
        ),
    )

    # 收集所有片段
    full_text = []
    for segment in segments:
        full_text.append(segment.text.strip())

    text = " ".join(full_text).strip()

    # 保存元信息
    meta = {
        "audio_file": os.path.basename(audio_path),
        "language": info.language,
        "language_probability": f"{info.language_probability:.4f}",
        "duration_seconds": f"{info.duration:.1f}",
        "text": text,
        "device": model.model.device if isinstance(model.model.device, str) else (model.model.device.type if hasattr(model.model, 'device') else "unknown"),
    }

    meta_path = os.path.join(OUTPUT_DIR, os.path.splitext(os.path.basename(audio_path))[0] + ".json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[ASR] 语言: {info.language} ({info.language_probability:.2%}) | "
          f"时长: {info.duration:.1f}s | 文本长度: {len(text)}",
          file=sys.stderr, flush=True)

    return text, meta


def main():
    if len(sys.argv) < 2:
        print("用法: python asr_call.py <audio_file_path> [output_dir]",
              file=sys.stderr)
        sys.exit(1)

    audio_path = sys.argv[1]
    custom_output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(audio_path):
        print(f"ERROR: 音频文件不存在: {audio_path}", file=sys.stderr)
        sys.exit(1)

    if custom_output_dir:
        global OUTPUT_DIR
        OUTPUT_DIR = custom_output_dir
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ---- 锁机制：防止并发 ASR 调用 ----
    lock_file = os.path.join(OUTPUT_DIR, ".asr_running.lock")
    pid, exe = acquire_lock(lock_file, label="asr")
    if pid is None:
        # 已有实例在运行，退出
        sys.exit(0)

    # # # 不清掉 llama！ASR 只用 ~1.5GB VRAM，不影响 llama 6GB
    register_cleanup_handlers(
        lock_file=lock_file,
        llama_port=LLAMA_PORT,
        restart_script=RESTART_SCRIPT,
    )

    start_time = time.time()

    try:
        with TimeoutGuard(300, lock_file=lock_file):
            # 加载模型（首次下载，后续缓存）
            model = load_model(MODEL_SIZE)

            # 转写
            text, meta = transcribe(model, audio_path)

            elapsed = time.time() - start_time
            print(f"[ASR] 完成 ({elapsed:.1f}s)", file=sys.stderr, flush=True)

            # 输出到 stdout（供 PS 脚本提取）
            print(text)

    except Exception as e:
        print(f"[ASR] 错误: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        release_lock(lock_file)
        sys.exit(1)

    finally:
        release_lock(lock_file)


if __name__ == "__main__":
    main()
