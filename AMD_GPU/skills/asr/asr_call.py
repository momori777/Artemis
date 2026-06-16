#!/usr/bin/env python3
"""
ASR (Automatic Speech Recognition) — 语音转文字 (AMD GPU 适配版)
================================================
基于 Faster-Whisper small 模型，不杀 llama-server。

与 NVIDIA 版的区别:
  - GPU 设备选择: 优先 CUDA/ROCm, fallback Vulkan/DirectML, 最终 CPU
  - 不硬依赖 torch.cuda (AMD 上 torch.cuda 映射到 HIP 才可用)
  - CPU fallback 对 small 模型完全可用 (推理 ~2-3x 实时速度)

用法:
    python asr_call.py <audio_file_path> [output_dir]
"""

import sys
import os
import json
import time
import traceback
import subprocess

# ---- 国内用户 HF mirror ----
if not os.environ.get("HF_ENDPOINT"):
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# ---- 路径设置 ----
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.dirname(SCRIPT_DIR)
WORKSPACE_DIR = os.path.dirname(SKILLS_DIR)

if SKILLS_DIR not in sys.path:
    sys.path.insert(0, SKILLS_DIR)

from shared.llama_lifecycle import (
    acquire_lock, release_lock,
    TimeoutGuard, register_cleanup_handlers,
)


# ---- 从 config.yaml 读取路径 ----
def _load_config():
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

MEDIA_AUDIO_DIR = _config.get("media_qqbot_audio") or os.path.join(
    WORKSPACE_DIR, "media", "qqbot", "audio"
)
ASR_OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "skills", "asr", "output")
OUTPUT_DIR = ASR_OUTPUT_DIR

LLAMA_PORT = int(_config.get("llama_port", 8080))
RESTART_SCRIPT = _config.get("restart_script")

# ---- 模型管理 ----
MODEL_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "asr_models")
MODEL_SIZE = "small"

os.makedirs(MODEL_CACHE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _detect_gpu_device():
    """
    检测最佳 GPU 设备。返回 (device_type, compute_type)。
    优先级: CUDA/HIP > Vulkan/DirectML > CPU
    """
    # 方法 1: torch.cuda (NVIDIA CUDA + AMD ROCm 都映射到这里)
    try:
        import torch
        if torch.cuda.is_available():
            # AMD ROCm 下 torch.cuda 也可用，因为 HIP 做了 CUDA 兼容层
            device_name = torch.cuda.get_device_name(0)
            free = torch.cuda.mem_get_info()[0] / (1024 ** 2)
            print(f"[ASR] GPU detected via CUDA/HIP: {device_name} ({free:.0f} MiB free)",
                  file=sys.stderr, flush=True)

            # 判断是 NVIDIA 还是 AMD
            if any(x in device_name.lower() for x in ["amd", "radeon", "rx ", "rx7", "rx6"]):
                print("[ASR] AMD GPU via ROCm — using HIP backend", file=sys.stderr, flush=True)
                # ROCm 下 float16 可能有精度问题，用 float32 更安全
                return "cuda", "float32"
            else:
                print("[ASR] NVIDIA GPU — using CUDA float16", file=sys.stderr, flush=True)
                return "cuda", "float16"
    except Exception as e:
        print(f"[ASR] torch.cuda not available: {e}", file=sys.stderr, flush=True)

    # 方法 2: Vulkan 检测 (AMD / Intel)
    try:
        result = subprocess.run(
            ["vulkaninfo", "--summary"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and "deviceName" in result.stdout:
            for line in result.stdout.splitlines():
                if "deviceName" in line:
                    dev = line.split("=")[-1].strip()
                    print(f"[ASR] GPU detected via Vulkan: {dev}",
                          file=sys.stderr, flush=True)
                    break
            # Whisper 不支持 Vulkan 直接推理，但说明了有 GPU
            # 如果显存足够，后续可以尝试 ONNX Runtime DirectML
            print("[ASR] Vulkan GPU present but Faster-Whisper uses CUDA/CPU",
                  file=sys.stderr, flush=True)
    except Exception:
        pass

    # Fallback: CPU
    print("[ASR] No GPU backend available — using CPU", file=sys.stderr, flush=True)
    return "cpu", "float32"


def load_model(model_size=MODEL_SIZE):
    """加载 Faster-Whisper 模型（GPU/CPU 自适应）"""
    from faster_whisper import WhisperModel

    device, compute_type = _detect_gpu_device()

    print(f"[ASR] 加载模型 {model_size} (device={device}, compute={compute_type})...",
          file=sys.stderr, flush=True)

    if device == "cuda":
        try:
            import torch
            free = torch.cuda.mem_get_info()[0] / (1024 ** 2)
            print(f"[ASR] VRAM free before load: {free:.0f} MiB",
                  file=sys.stderr, flush=True)
        except Exception:
            pass

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
        err_str = str(e)
        if "ConnectTimeout" in err_str or "LocalEntryNotFoundError" in err_str:
            print(f"[ASR] 网络不通，尝试从缓存加载...", file=sys.stderr, flush=True)
            model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                download_root=MODEL_CACHE_DIR,
                local_files_only=True,
            )
        elif "out of memory" in err_str.lower() or "OOM" in err_str:
            print(f"[ASR] GPU OOM — falling back to CPU", file=sys.stderr, flush=True)
            model = WhisperModel(
                model_size,
                device="cpu",
                compute_type="float32",
                download_root=MODEL_CACHE_DIR,
                local_files_only=False,
            )
        else:
            raise

    print(f"[ASR] 模型就绪 (device={device}, compute_type={compute_type})",
          file=sys.stderr, flush=True)
    return model


def transcribe(model, audio_path):
    """
    转写音频文件为文本。

    返回 (text, info) 元组。
    """
    print(f"[ASR] 转写中: {os.path.basename(audio_path)}",
          file=sys.stderr, flush=True)

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
        ),
    )

    full_text = []
    for segment in segments:
        full_text.append(segment.text.strip())

    text = " ".join(full_text).strip()

    # 确定实际使用的设备
    try:
        if hasattr(model, 'model') and hasattr(model.model, 'device'):
            raw_device = model.model.device
            if hasattr(raw_device, 'type'):
                actual_device = raw_device.type
            else:
                actual_device = str(raw_device)
        else:
            actual_device = "unknown"
    except Exception:
        actual_device = "unknown"

    meta = {
        "audio_file": os.path.basename(audio_path),
        "language": info.language,
        "language_probability": f"{info.language_probability:.4f}",
        "duration_seconds": f"{info.duration:.1f}",
        "text": text,
        "device": actual_device,
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

    # ---- 锁机制 ----
    lock_file = os.path.join(OUTPUT_DIR, ".asr_running.lock")
    pid, exe = acquire_lock(lock_file, label="asr")
    if pid is None:
        sys.exit(0)

    # 不清掉 llama！ASR 只用 ~1.5GB VRAM，对 Vulkan 也是互不干扰
    register_cleanup_handlers(
        lock_file=lock_file,
        llama_port=LLAMA_PORT,
        restart_script=RESTART_SCRIPT,
    )

    start_time = time.time()

    try:
        with TimeoutGuard(300, lock_file=lock_file):
            model = load_model(MODEL_SIZE)
            text, meta = transcribe(model, audio_path)

            elapsed = time.time() - start_time
            print(f"[ASR] 完成 ({elapsed:.1f}s)", file=sys.stderr, flush=True)

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
