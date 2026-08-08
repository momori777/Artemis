#!/usr/bin/env python3
"""
ComfyUI 文生图调用脚本 — 直接加载模型推理，不走 WebUI HTTP API。
用法: python comfyui_call.py "正prompt" "负prompt" [seed] [宽] [高] [步数] [CFG] [模型名]
输出: 标准输出打印生成的 PNG 文件路径

路径: 从 workspace 根目录的 config.yaml 读取
可用模型:
  WAI-Nsfw-Illustrious-17.safetensors  (6.5GB, 训练至 2025-05, 层次分明)
  miaomiaoHarem_v20.safetensors        (6.5GB, 训练至 2026-01, 偏油但库新)
"""
import sys
import os
import time
import random
import re
import json
import numpy as np

# --- 从 workspace/config.yaml 读取路径 ---
_def = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_d = _def

def _load_config():
    """从 workspace 根目录 config.yaml 加载路径配置，不存在则报错退出"""
    config_path = os.path.join(_def, 'config.yaml')
    if not os.path.exists(config_path):
        print(f"[ERROR] 找不到 config.yaml: {config_path}", file=sys.stderr)
        print("请先运行 quick_setup.ps1 或在 workspace 根目录创建 config.yaml",
              file=sys.stderr)
        sys.exit(1)
    import yaml
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

_cfg = _load_config()

# --- shared 生命周期模块 ---
if _def not in sys.path:
    sys.path.insert(0, _def)

from skills.shared.llama_lifecycle import (
    acquire_lock, release_lock,
    stop_llama, start_llama,
    TimeoutGuard, register_cleanup_handlers,
)

# ========== 路径配置（从 config.yaml 读取） ==========
# ComfyUI 推理引擎：优先 config.yaml 中的 comfyui_root，
# 其次从 comfyui_python 路径推导（取父目录的父目录），最后 fallback 内置目录
_COMFYUI_ROOT = _cfg.get('comfyui_root')
if not _COMFYUI_ROOT:
    _py_path = _cfg.get('comfyui_python', '')
    if _py_path:
        _py_dir = os.path.dirname(_py_path)
        _comfy_parent = os.path.dirname(_py_dir)
        if os.path.isdir(_comfy_parent) and os.path.exists(os.path.join(_comfy_parent, 'main.py')):
            _COMFYUI_ROOT = _comfy_parent
if not _COMFYUI_ROOT:
    _COMFYUI_ROOT = os.path.join(_def, 'skills', 'comfyui_core')
COMFYUI_ROOT = _COMFYUI_ROOT
if not os.path.isdir(COMFYUI_ROOT):
    print(f"[ERROR] ComfyUI 推理引擎未找到: {COMFYUI_ROOT}", file=sys.stderr)
    print("请从 GitHub 克隆完整项目或设置 config.yaml 中的 comfyui_root",
          "或确保 comfyui_python 指向包含 ComfyUI 主目录的 Python", file=sys.stderr)
    sys.exit(1)
PYTHON_PATH = _cfg['comfyui_python']
CHECKPOINTS_DIR = _cfg['comfyui_checkpoints_dir']
OUTPUT_DIR = _cfg['comfyui_temp_output_dir']

# ========== Llama Server 配置 ==========
LLAMA_LOG_DIR = _cfg['llama_log_dir']
LLAMA_EXE_PATH = _cfg['llama_exe']
LLAMA_MODEL_PATH = _cfg['llama_model']
RESTART_SCRIPT = _cfg['restart_script']
LLAMA_PORT = _cfg.get('llama_port', 8080)

# ========== 硬超时（防止子进程卡死不退出，导致 gateway session 锁死） ==========
HARD_TIMEOUT = 900  # 秒（推理最长 2min + llama 重启两轮含 VRAM 回收 ~10min，留余量）

# ========== 默认参数 ==========
DEFAULT_CKPT = "WAI-Nsfw-Illustrious-17.safetensors"
DEFAULT_WIDTH = 768  # 8GB VRAM safe (RTX 5070 Laptop); 1200x1500 OOMs
DEFAULT_HEIGHT = 1024
DEFAULT_STEPS = 24
DEFAULT_CFG = 6.0
DEFAULT_SAMPLER = "dpmpp_2s_ancestral"
DEFAULT_SCHEDULER = "karras"

# ========== 防重复执行 ==========
LOCK_FILE = os.path.join(OUTPUT_DIR, ".comfyui_running.lock")
LAST_OUTPUT_FILE = os.path.join(OUTPUT_DIR, ".comfyui_last_output.txt")


def slugify(text, max_len=30):
    """从文本提取安全文件名标签（英文/数字/中文保留）"""
    cleaned = re.sub(r'[^\w\u4e00-\u9fff ]', ' ', text, flags=re.ASCII)
    cleaned = re.sub(r'\s+', '_', cleaned).strip('_')
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip('_')
    return cleaned or 'untitled'


def safe_load_safetensors(ckpt_path):
    """
    手动加载 safetensors 文件，绕过 cu130 在 RTX 5070 (Blackwell) 上
    safetensors.torch.load_file 的 torch.storage 访问崩溃 bug。
    """
    import torch

    with open(ckpt_path, 'rb') as f:
        header_len = int.from_bytes(f.read(8), 'little')
        header = json.loads(f.read(header_len))
        data_start = 8 + header_len

        dtype_map = {
            'F32': np.float32, 'F16': np.float16, 'F64': np.float64,
            'I32': np.int32, 'I64': np.int64, 'I8': np.int8, 'I16': np.int16,
            'U8': np.uint8, 'U16': np.uint16, 'U32': np.uint32, 'U64': np.uint64,
            'BF16': np.float16,
        }

        state_dict = {}
        for key, info in header.items():
            start, end = info['data_offsets']
            f.seek(data_start + start)
            raw = f.read(end - start)
            dt = dtype_map.get(info['dtype'], np.float32)
            arr = np.frombuffer(raw, dtype=dt).reshape(info['shape'])
            state_dict[key] = torch.from_numpy(arr.copy())

    return state_dict


def run_txt2img(positive_prompt, negative_prompt, seed, width, height,
                steps, cfg, ckpt_name, manage_llama=True):
    """
    主推理函数
    manage_llama: 自动管理 llama-server（停→跑图→启），默认开启
    """
    import torch

    if manage_llama:
        stop_llama(port=LLAMA_PORT, wait_vram_stable=True)

    # 导入 ComfyUI 路径
    sys.path.insert(0, COMFYUI_ROOT)
    sys.path.insert(0, PYTHON_PATH)
    os.environ["COMFYUI_PATH"] = COMFYUI_ROOT
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["DO_NOT_TRACK"] = "1"
    os.environ["MIMALLOC_PURGE_DELAY"] = "0"

    import folder_paths  # noqa: E402
    import comfy.options  # noqa: E402
    comfy.options.enable_args_parsing()

    t0 = time.time()

    # ---------- 1. 加载模型 ----------
    ckpt_path = os.path.join(CHECKPOINTS_DIR, ckpt_name)
    if not os.path.exists(ckpt_path):
        for root, dirs, files in os.walk(CHECKPOINTS_DIR):
            if ckpt_name in files:
                ckpt_path = os.path.join(root, ckpt_name)
                break
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"找不到模型: {ckpt_name}")

    from comfy.sd import load_state_dict_guess_config  # noqa: E402
    from comfy import model_management  # noqa: E402

    print(f"读取模型: {os.path.basename(ckpt_path)} "
          f"({os.path.getsize(ckpt_path) / 1024 ** 3:.1f}GB)",
          file=sys.stderr, flush=True)
    state_dict = safe_load_safetensors(ckpt_path)
    print(f"模型加载完成 ({time.time() - t0:.1f}s)", file=sys.stderr, flush=True)

    result = load_state_dict_guess_config(sd=state_dict)
    model, clip, vae = result[0], result[1], result[2]
    print(f"模型导入完成 ({time.time() - t0:.1f}s)", file=sys.stderr, flush=True)

    # ---------- 2. 文本编码 ----------
    from nodes import CLIPTextEncode  # noqa: E402
    dev = model_management.get_torch_device()

    pos_out = CLIPTextEncode().encode(text=positive_prompt, clip=clip)[0]
    neg_out = CLIPTextEncode().encode(text=negative_prompt, clip=clip)[0]
    print(f"文本编码完成 ({time.time() - t0:.1f}s)", file=sys.stderr, flush=True)

    # ---------- 3. 采样 ----------
    from nodes import common_ksampler  # noqa: E402

    latent = {"samples": torch.zeros((1, 4, height // 8, width // 8), device=dev)}
    samples = common_ksampler(
        model, seed=seed, steps=steps, cfg=cfg,
        sampler_name=DEFAULT_SAMPLER,
        scheduler=DEFAULT_SCHEDULER,
        positive=pos_out, negative=neg_out,
        latent=latent, denoise=1.0,
    )
    print(f"采样完成 ({time.time() - t0:.1f}s)", file=sys.stderr, flush=True)

    # ---------- 4. VAE 解码 ----------
    try:
        from nodes import VAEDecode  # noqa: E402
        images = VAEDecode().decode(vae, samples[0])[0]
    except Exception:
        print("VAE decode 失败，尝试 tiled decode...", file=sys.stderr, flush=True)
        vae.vae_dtype = torch.float32
        images = vae.decode_tiled(samples[0]["samples"],
                                  tile_x=64, tile_y=64, overlap=16)
    print(f"VAE解码完成 ({time.time() - t0:.1f}s), shape={images.shape}",
          file=sys.stderr, flush=True)

    # ---------- 5. 保存 ----------
    from PIL import Image  # noqa: E402
    from datetime import datetime  # noqa: E402

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    tag = slugify(positive_prompt.split(',')[0])
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    fname = f"comfyui_{tag}_{ts}.png"
    out_path = os.path.join(OUTPUT_DIR, fname)

    for img in images:
        img = img.detach().cpu().numpy()
        img = np.clip(img * 255, 0, 255).astype(np.uint8)
        if img.shape[0] == 3 or img.shape[0] == 1:
            img = img.transpose(1, 2, 0)
        if img.shape[2] == 1:
            img = img.squeeze(2)
        Image.fromarray(img).save(out_path)
        break

    with open(LAST_OUTPUT_FILE, 'w') as f:
        f.write(out_path)

    total = time.time() - t0
    print("=" * 60, file=sys.stderr, flush=True)
    print(f"完成! 总耗时: {total:.1f}s", file=sys.stderr, flush=True)
    print(f"输出: {out_path}", file=sys.stderr, flush=True)
    print("=" * 60, file=sys.stderr, flush=True)

    # --- 释放 ComfyUI 模型显存，防止 start_llama OOM ---
    # CRITICAL: ComfyUI model_management holds internal references
    # that del + gc.collect() won't catch. Must use ComfyUI's own
    # unload + force CUDA context reset.
    #
    # Step 1: ComfyUI-level unload
    try:
        from comfy import model_management as _mm
        _mm.unload_all_models()
        _mm.soft_empty_cache()
    except Exception:
        pass

    # Step 2: Delete all Python references
    del pos_out, neg_out, images, state_dict, samples, latent
    if model is not None:
        del model
    if clip is not None:
        del clip
    if vae is not None:
        del vae

    # Step 3: Aggressive GC
    import gc as _gc
    _gc.collect()
    _gc.collect()

    # Step 4: Force CUDA context release (destroys all GPU allocations)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        # Reset the CUDA memory allocator entirely
        torch.cuda.reset_max_memory_allocated()
        torch.cuda.reset_max_memory_cached()
        _gc.collect()
        torch.cuda.empty_cache()
        _gc.collect()

    # Step 5: Release process RSS
    try:
        import ctypes
        ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
    except Exception:
        pass

    # Step 6: Wait for GPU driver deferred-free + recheck
    if manage_llama:
        free0 = torch.cuda.mem_get_info()[0] / (1024 ** 2)
        total0 = torch.cuda.mem_get_info()[1] / (1024 ** 2)
        print(f"[VRAM] Initial after cleanup: {free0:.0f}/{total0:.0f} MiB",
              file=sys.stderr, flush=True)

        peak_free = free0
        for i in range(10):
            time.sleep(3)
            _gc.collect()
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
            cur = torch.cuda.mem_get_info()[0] / (1024 ** 2)
            peak_free = max(peak_free, cur)
            print(f"[VRAM] +{(i+1)*3}s: {cur:.0f} MiB (peak {peak_free:.0f})",
                  file=sys.stderr, flush=True)

        print(f"[VRAM] Reclaim done, peak: {peak_free:.0f}/{total0:.0f} MiB",
              file=sys.stderr, flush=True)
    # ---

    if manage_llama:
        sys.stderr.flush()
        ok = start_llama(
            port=LLAMA_PORT,
            exe_path=LLAMA_EXE_PATH,
            model_path=LLAMA_MODEL_PATH,
            log_dir=LLAMA_LOG_DIR,
            use_mmap=True,  # after ComfyUI, avoid --no-mmap fragmentation
        )
        if not ok:
            # 首次启动失败 → VRAM 还是不够，再等一轮+更激进回收
            print(f"[LLAMA] 启动失败，激进回收 VRAM 后重试...",
                  file=sys.stderr, flush=True)
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
            _gc.collect()
            torch.cuda.empty_cache()
            _gc.collect()
            try:
                ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
            except Exception:
                pass
            time.sleep(15)
            torch.cuda.empty_cache()
            free_retry = torch.cuda.mem_get_info()[0] / (1024 ** 2)
            print(f"[LLAMA] 重试前 VRAM: {free_retry:.0f} MiB",
                  file=sys.stderr, flush=True)
            ok = start_llama(
                port=LLAMA_PORT,
                exe_path=LLAMA_EXE_PATH,
                model_path=LLAMA_MODEL_PATH,
                log_dir=LLAMA_LOG_DIR,
                use_mmap=True,
            )
        if not ok:
            print(f"[LLAMA] 启动失败(VRAM不足或超时)，图像已保存到 {out_path}",
                  file=sys.stderr, flush=True)
        else:
            print(f"[LLAMA] 已就绪，继续输出结果", file=sys.stderr, flush=True)

    sys.stdout.write(out_path + '\n')
    sys.stdout.flush()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"用法: python {sys.argv[0]} \"正prompt\" \"负prompt\" "
              f"[seed] [宽] [高] [步数] [CFG] [模型名] [--no-manage-llama]",
              file=sys.stderr)
        sys.exit(1)

    positive_prompt = sys.argv[1]
    negative_prompt = sys.argv[2]

    no_manage_llama = '--no-manage-llama' in sys.argv
    clean_args = [a for a in sys.argv if a != '--no-manage-llama']
    seed = int(clean_args[3]) if len(clean_args) > 3 else random.randint(0, 2 ** 63 - 1)
    width = int(clean_args[4]) if len(clean_args) > 4 else DEFAULT_WIDTH
    height = int(clean_args[5]) if len(clean_args) > 5 else DEFAULT_HEIGHT
    steps = int(clean_args[6]) if len(clean_args) > 6 else DEFAULT_STEPS
    cfg = float(clean_args[7]) if len(clean_args) > 7 else DEFAULT_CFG
    ckpt_name = clean_args[8] if len(clean_args) > 8 else DEFAULT_CKPT

    # 获取锁（使用 shared 模块）
    lock_pid, lock_exe = acquire_lock(LOCK_FILE, label="comfyui")
    if lock_pid is None:
        print("[ERROR] 已有 comfyui 实例在运行，跳过本次调用", file=sys.stderr)
        sys.exit(0)

    # 注册清理钩子（使用 shared 模块）
    register_cleanup_handlers(
        lock_file=LOCK_FILE,
        llama_port=LLAMA_PORT,
        restart_script=RESTART_SCRIPT,
    )

    out_path = None  # 声明在外层作用域
    try:
        manage_llama = not no_manage_llama
        if no_manage_llama:
            print("[LLAMA] 不停 llama-server，保持对话连续",
                  file=sys.stderr, flush=True)

        with TimeoutGuard(HARD_TIMEOUT, lock_file=LOCK_FILE):
            run_txt2img(positive_prompt, negative_prompt, seed, width, height,
                        steps, cfg, ckpt_name, manage_llama=manage_llama)
            # 读取输出路径
            if os.path.exists(LAST_OUTPUT_FILE):
                with open(LAST_OUTPUT_FILE, 'r') as f:
                    out_path = f.read().strip()
    except TimeoutError:
        # 超时时图片可能已保存（start_llama 阶段超时），检查 LAST_OUTPUT_FILE
        if os.path.exists(LAST_OUTPUT_FILE):
            with open(LAST_OUTPUT_FILE, 'r') as f:
                out_path = f.read().strip()
            if out_path and os.path.exists(out_path):
                print(f"[TIMEOUT] 超时但图片已生成: {out_path}", file=sys.stderr, flush=True)
                sys.stdout.write(out_path + '\n')
                sys.stdout.flush()
                sys.exit(0)
        print(f"[TIMEOUT] 超时，无输出文件", file=sys.stderr, flush=True)
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    finally:
        release_lock(LOCK_FILE)
