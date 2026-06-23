"""
共享 Llama Server 生命周期管理模块 (AMD GPU / Vulkan 适配版)。

与 NVIDIA 版的区别:
  - _wait_for_vram_stable: 不再依赖 torch.cuda, 改用通用等待 + vulkaninfo fallback
  - start_llama: 去掉 CUDA 专属参数 (--flash-attn, -ctk, -ctv), ngl 改为 99

提供统一的 llama-server 启停、文件锁、硬超时守卫和清理钩子，
供 tts_call.py 和 comfyui_call.py 复用。

用法:
    import sys, os
    _dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    from skills.shared.llama_lifecycle import (
        acquire_lock, release_lock,
        stop_llama, start_llama,
        TimeoutGuard, register_cleanup_handlers,
    )
"""

import os
import sys
import time
import json
import atexit
import signal
import subprocess
import threading


# ---- 共享底层（端口检测 / 健康检查） ----

def _port_open(host, port, timeout=2):
    """检测指定端口是否开启"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False
    finally:
        s.close()


def _detect_gpu_backend():
    """
    检测可用的 GPU 后端，返回 "cuda" / "vulkan" / "none"。
    A 卡优先尝试 Vulkan，N 卡保留 CUDA 路径兼容。
    """
    # 优先检测 CUDA (NVIDIA)
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass

    # 检测 Vulkan (AMD / Intel / NVIDIA 通用)
    try:
        result = subprocess.run(
            ["vulkaninfo", "--summary"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and "deviceName" in result.stdout:
            return "vulkan"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 尝试 vulkaninfo 的常见路径
    try:
        vk_paths = [
            os.path.join(os.environ.get("VULKAN_SDK", ""), "Bin", "vulkaninfo.exe"),
            "vulkaninfo.exe",
            "vulkaninfo",
        ]
        for vk in vk_paths:
            if vk and os.path.exists(vk):
                result = subprocess.run([vk, "--summary"],
                    capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and "deviceName" in result.stdout:
                    return "vulkan"
    except Exception:
        pass

    return "none"


def _get_vram_mb():
    """
    通用 VRAM 查询，依次尝试:
    1. torch.cuda (NVIDIA + ROCm)
    2. vulkaninfo 命令
    3. WMI (Windows)
    返回空闲 VRAM (MiB)，失败返回 0。
    """
    # 方法 1: torch.cuda (NVIDIA 和 ROCm 都映射到这里)
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
            free = torch.cuda.mem_get_info()[0] / (1024 ** 2)
            total = torch.cuda.mem_get_info()[1] / (1024 ** 2)
            print(f"[VRAM] CUDA/HIP: {free:.0f} MiB free / {total:.0f} MiB total",
                  file=sys.stderr, flush=True)
            return free
    except Exception:
        pass

    # 方法 2: vulkaninfo (AMD / Intel)
    try:
        result = subprocess.run(
            ["vulkaninfo", "--summary"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                # Vulkan 堆大小，找 maxMemoryAllocationSize 或 deviceLocal
                if "maxMemoryAllocationSize" in line:
                    # 格式: maxMemoryAllocationSize = 12345678900
                    val = line.split("=")[-1].strip().split()[0]
                    try:
                        mb = int(val) / (1024 * 1024)
                        print(f"[VRAM] Vulkan heap max: {mb:.0f} MiB",
                              file=sys.stderr, flush=True)
                        # 不能直接得到 free，返回总容量作为参考
                        return mb
                    except (ValueError, IndexError):
                        pass
    except Exception:
        pass

    # 方法 3: WMI (Windows 通用)
    try:
        import subprocess as sp
        result = sp.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_VideoController | "
             "Where-Object { $_.AdapterRAM -gt 0 } | "
             "Select-Object -ExpandProperty AdapterRAM) -join ','"],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip():
            vrams = [int(x) for x in result.stdout.strip().split(",") if x.strip().isdigit()]
            if vrams:
                mb = max(vrams) / (1024 * 1024)
                print(f"[VRAM] WMI total: {mb:.0f} MiB", file=sys.stderr, flush=True)
                # WMI 只能拿到总容量，返回作为参考
                return mb
    except Exception:
        pass

    return 0


def _wait_for_vram_stable(initial_free=None, stable_threshold=50, max_wait=30,
                          min_free_mb=None, label="[LLAMA]"):
    """
    等待 GPU VRAM 稳定（释放完成），兼容 CUDA / Vulkan / 无 GPU。

    与 NVIDIA 版的区别:
      - 不硬依赖 torch.cuda，优先尝试 CUDA 路径，fallback 到通用等待
      - fallback 时直接 sleep 等待，不做精确 VRAM 监测

    返回最终稳定时的空闲 VRAM (MiB)。
    """
    backend = _detect_gpu_backend()

    if backend == "cuda":
        # ── CUDA 精确路径（保留原逻辑） ──
        try:
            import torch
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
            if initial_free is None:
                initial_free = torch.cuda.mem_get_info()[0] / (1024 ** 2)
            free_vram = initial_free
            print(f"{label} CUDA sync done, free VRAM: {free_vram:.0f} MiB",
                  file=sys.stderr, flush=True)

            stable_count = 0
            peak_free = free_vram
            for i in range(max_wait):
                time.sleep(1)
                cur_free = torch.cuda.mem_get_info()[0] / (1024 ** 2)
                peak_free = max(peak_free, cur_free)
                if abs(cur_free - free_vram) < stable_threshold:
                    stable_count += 1
                    if stable_count >= 3:
                        if min_free_mb and cur_free < min_free_mb:
                            print(f"{label} VRAM stable at {cur_free:.0f} MiB but below "
                                  f"{min_free_mb} MiB minimum, waiting more...",
                                  file=sys.stderr, flush=True)
                            stable_count = 0
                            free_vram = cur_free
                            continue
                        print(f"{label} VRAM stable at {cur_free:.0f} MiB "
                              f"(peak {peak_free:.0f}, {i + 1}s)",
                              file=sys.stderr, flush=True)
                        return cur_free
                else:
                    stable_count = 0
                free_vram = cur_free

            print(f"{label} VRAM still settling after {max_wait}s "
                  f"(current {free_vram:.0f} MiB, peak {peak_free:.0f})",
                  file=sys.stderr, flush=True)
            return free_vram
        except Exception:
            pass

    # ── Vulkan / 无 GPU — 通用等待 ──
    print(f"{label} GPU backend={backend}, waiting {max_wait}s for VRAM release...",
          file=sys.stderr, flush=True)

    # 通用等待策略：先获取当前 VRAM 估算，然后等稳定
    estimated_free = _get_vram_mb()
    if estimated_free > 0:
        print(f"{label} Estimated VRAM available: {estimated_free:.0f} MiB",
              file=sys.stderr, flush=True)

    # 如果无法精确监控 VRAM，等待固定时间让 GPU 驱动回收
    wait_seconds = min(max_wait, 10) if backend == "vulkan" else max_wait
    print(f"{label} Waiting {wait_seconds}s for GPU cleanup...",
          file=sys.stderr, flush=True)
    time.sleep(wait_seconds)

    final_est = _get_vram_mb()
    print(f"{label} After wait, estimated VRAM: {final_est:.0f} MiB",
          file=sys.stderr, flush=True)
    return final_est if final_est > 0 else estimated_free


def _wait_for_llama_ready(port=8080, timeout=180, label="[LLAMA]"):
    """
    四阶段等待 llama-server 完全就绪：
    1. 端口打开
    2. /health 返回 200
    3. /completion 返回有效响应
    4. /v1/chat/completions 返回有效响应

    返回 True 表示就绪，False 表示超时。
    """
    import urllib.request
    import urllib.error

    deadline = time.time() + timeout

    # 阶段 1: 端口打开
    while time.time() < deadline:
        if _port_open("127.0.0.1", port, timeout=1):
            print(f"{label} 端口 {port} 已打开", file=sys.stderr, flush=True)
            break
        time.sleep(0.5)
    else:
        print(f"{label} 超时：端口 {port} 在 {timeout}s 内未打开",
              file=sys.stderr, flush=True)
        return False

    # 阶段 2: /health 端点
    health_deadline = min(time.time() + 30, deadline + 10)
    health_ok = False
    while time.time() < health_deadline:
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/health", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    print(f"{label} /health 200 OK", file=sys.stderr, flush=True)
                    health_ok = True
                    break
        except Exception:
            pass
        time.sleep(0.5)
    if not health_ok:
        print(f"{label} /health 端点超时", file=sys.stderr, flush=True)
        return False

    # 阶段 3: /completion 功能验证
    comp_deadline = min(time.time() + 60, deadline + 10)
    import json as _json
    test_payload = _json.dumps({
        "prompt": "hi",
        "n_predict": 1,
        "temperature": 0,
        "cache_prompt": False,
    }).encode("utf-8")
    while time.time() < comp_deadline:
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/completion",
                data=test_payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "***",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    body = resp.read()
                    data = _json.loads(body)
                    if data.get("content") or data.get("stop"):
                        print(f"{label} /completion 验证通过",
                              file=sys.stderr, flush=True)
                        break
        except Exception:
            pass
        time.sleep(0.5)

    # 阶段 4: /v1/chat/completions 端点验证（OpenClaw 用这个）
    v1_deadline = min(time.time() + 60, deadline + 10)
    chat_payload = _json.dumps({
        "model": "qwen3.6-35b",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1,
        "temperature": 0,
    }).encode("utf-8")
    while time.time() < v1_deadline:
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/v1/chat/completions",
                data=chat_payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "***",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    body = resp.read()
                    data = _json.loads(body)
                    if data.get("choices"):
                        print(f"{label} /v1/chat/completions 验证通过 — 就绪 ✓",
                              file=sys.stderr, flush=True)
                        return True
        except Exception:
            pass
        time.sleep(0.5)

    print(f"{label} 警告：/v1/chat/completions 在超时前未响应，但端口可用，允许尝试",
          file=sys.stderr, flush=True)
    return True  # 至少端口和 /health 都过了


# ---- 文件锁 ----

def acquire_lock(lock_file, label="skill"):
    """
    获取文件锁，防止同一 skill 重复执行。

    返回 (pid_str, exe_path)；如果已有实例在运行则返回 (None, None)。
    """
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                data = json.loads(f.read().strip())
            old_pid = data.get('pid')
            old_exe = data.get('exe', '')
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {old_pid}', '/NH'],
                capture_output=True, text=True, timeout=5
            )
            if (old_pid and str(old_pid) in result.stdout
                    and 'python.exe' in result.stdout):
                if old_exe and old_exe in result.stdout:
                    print(f"[LOCK] 检测到正在运行的 {label} (PID={old_pid})，跳过",
                          file=sys.stderr, flush=True)
                    return None, None
        except (ValueError, OSError, json.JSONDecodeError,
                subprocess.TimeoutExpired):
            pass

    pid = os.getpid()
    exe_path = sys.executable
    lock_data = json.dumps({'pid': pid, 'exe': exe_path})
    os.makedirs(os.path.dirname(lock_file), exist_ok=True)
    tmp = lock_file + ".tmp" + str(pid)
    with open(tmp, 'w') as f:
        f.write(lock_data)
    try:
        os.replace(tmp, lock_file)
    except OSError:
        try:
            os.remove(tmp)
        except OSError:
            pass
        print(f"[LOCK] 锁已被另一个进程持有",
              file=sys.stderr, flush=True)
        return None, None
    print(f"[LOCK] 已获取锁 (PID={pid}, exe={exe_path})",
          file=sys.stderr, flush=True)
    return str(pid), exe_path


def release_lock(lock_file):
    """释放锁文件"""
    try:
        if os.path.exists(lock_file):
            os.remove(lock_file)
            print("[LOCK] 已释放锁", file=sys.stderr, flush=True)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[LOCK] 释放锁异常: {e}", file=sys.stderr, flush=True)


# ---- Llama Server 启停 ----

def stop_llama(port=8080, wait_vram_stable=True):
    """
    停止 llama-server（如果正在运行）。

    先尝试 HTTP /shutdown 优雅关闭，失败后 taskkill 强杀。
    wait_vram_stable=True 时等待 GPU VRAM 完全释放后再返回。

    返回 True 表示已停止（或本来就没运行）。
    """
    print("[LLAMA] 检查 llama-server 状态...", file=sys.stderr, flush=True)

    if not _port_open("127.0.0.1", port, timeout=1):
        print("[LLAMA] llama-server 未运行，跳过", file=sys.stderr, flush=True)
        return False

    print("[LLAMA] 停止 llama-server...", file=sys.stderr, flush=True)
    try:
        import urllib.request
        urllib.request.urlopen(f"http://127.0.0.1:{port}/shutdown", timeout=2)
        print("[LLAMA] 已发送优雅关闭请求", file=sys.stderr, flush=True)
    except Exception:
        print("[LLAMA] HTTP 关闭失败，使用 taskkill", file=sys.stderr, flush=True)
        subprocess.run(
            ["taskkill", "/f", "/im", "llama-server.exe"],
            capture_output=True, text=False
        )

    # 等待端口释放
    for i in range(30):
        if not _port_open("127.0.0.1", port, timeout=1):
            print(f"[LLAMA] 端口 {port} 已释放 ({i + 1}s)",
                  file=sys.stderr, flush=True)
            break
        time.sleep(0.5)
    else:
        print(f"[LLAMA] 警告：端口 {port} 仍未释放，继续执行",
              file=sys.stderr, flush=True)

    # VRAM 稳定检测 (GPU 无关)
    if wait_vram_stable:
        _wait_for_vram_stable(min_free_mb=None, max_wait=10)

    return True


def start_llama(port=8080, exe_path=None, model_path=None,
                log_dir=None, timeout=180):
    """
    启动 llama-server 并等待就绪 (Vulkan 版)。

    与 NVIDIA 版的区别:
      - 去掉 --flash-attn on (Vulkan 不支持)
      - 去掉 -ctk q8_0 / -ctv q8_0 (CUDA 专属)
      - ngl 改为 99 (Vulkan 可以全部层 offload)
      - VRAM 检测改为 GPU 无关的 _get_vram_mb()

    返回 True 表示启动成功，False 表示失败。
    """
    print("[LLAMA] 启动 llama-server (Vulkan)...", file=sys.stderr, flush=True)

    # VRAM 激进清理
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
            import gc
            gc.collect()
            time.sleep(3)
            torch.cuda.empty_cache()
            gc.collect()
            time.sleep(2)
            free = torch.cuda.mem_get_info()[0] / (1024 ** 2)
            total = torch.cuda.mem_get_info()[1] / (1024 ** 2)
            print(f"[LLAMA] VRAM (CUDA): {free:.0f} MiB free / {total:.0f} MiB total",
                  file=sys.stderr, flush=True)
    except Exception:
        # AMD/Vulkan fallback
        vram_mb = _get_vram_mb()
        if vram_mb > 0:
            print(f"[LLAMA] VRAM (generic): {vram_mb:.0f} MiB estimated",
                  file=sys.stderr, flush=True)
        import gc
        gc.collect()
        time.sleep(3)

    # 先确保旧进程被清理干净
    if _port_open("127.0.0.1", port, timeout=1):
        print("[LLAMA] 端口仍被占用，强制清理...", file=sys.stderr, flush=True)
        subprocess.run(
            ["taskkill", "/f", "/im", "llama-server.exe"],
            capture_output=True, text=False
        )
        for i in range(10):
            if not _port_open("127.0.0.1", port, timeout=1):
                print(f"[LLAMA] 端口已释放 ({i + 1}s)",
                      file=sys.stderr, flush=True)
                break
            time.sleep(0.5)

    # ── Vulkan 自适应参数 ──
    backend = _detect_gpu_backend()
    print(f"[LLAMA] GPU backend: {backend}", file=sys.stderr, flush=True)

    # Vulkan 默认全部层 offload 到 GPU
    ngl = 99

    # VRAM 自适应 batch size
    vram_mb = _get_vram_mb()
    if vram_mb > 0:
        if vram_mb < 4000:
            batch_size = 512
            ubatch_size = 256
            print(f"[LLAMA] Low VRAM ({vram_mb:.0f} MiB), batch=512",
                  file=sys.stderr, flush=True)
        elif vram_mb < 6000:
            batch_size = 1024
            ubatch_size = 512
            print(f"[LLAMA] Mid VRAM ({vram_mb:.0f} MiB), batch=1024",
                  file=sys.stderr, flush=True)
        elif vram_mb < 10000:
            batch_size = 2048
            ubatch_size = 1024
            print(f"[LLAMA] Good VRAM ({vram_mb:.0f} MiB), batch=2048",
                  file=sys.stderr, flush=True)
        else:
            batch_size = 4096
            ubatch_size = 2048
            print(f"[LLAMA] Large VRAM ({vram_mb:.0f} MiB), batch=4096",
                  file=sys.stderr, flush=True)
    else:
        # 无法检测 VRAM，保守值
        batch_size = 1024
        ubatch_size = 512
        print(f"[LLAMA] VRAM unknown, conservative batch=1024",
              file=sys.stderr, flush=True)

    # ── Vulkan 参数 ──
    args = [
        exe_path or "llama-server.exe",
        "-m", model_path or "",
        "-c", "120000",
        "-ngl", str(ngl),
        "--cpu-moe",
        "--batch-size", str(batch_size),
        "--ubatch-size", str(ubatch_size),
        "--threads", "24",
        "-rea", "off",
        "--jinja",
        "--cache-ram", "5000",
        "--parallel", "1",
        "--kv-unified",
        "--no-mmap",
        "--no-warmup",
    ]

    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    out_fh = None
    err_fh = None
    try:
        if log_dir:
            out_fh = open(os.path.join(log_dir, "llama-out.log"), "ab")
            err_fh = open(os.path.join(log_dir, "llama-err.log"), "ab")
        proc = subprocess.Popen(
            args,
            stdout=out_fh or subprocess.DEVNULL,
            stderr=err_fh or subprocess.DEVNULL,
        )
    finally:
        if out_fh:
            out_fh.close()
        if err_fh:
            err_fh.close()

    print(f"[LLAMA] 已启动 (Vulkan, ngl={ngl})，PID={proc.pid}，等待端口 {port}...",
          file=sys.stderr, flush=True)
    return _wait_for_llama_ready(port=port, timeout=timeout)


# ---- 硬超时守卫 ----

class TimeoutGuard:
    """子进程硬超时守卫：超时后强杀自身，清理锁"""

    def __init__(self, timeout_sec, lock_file=None):
        self.timeout_sec = timeout_sec
        self.lock_file = lock_file
        self._timer = None

    def __enter__(self):
        self._timer = threading.Timer(self.timeout_sec, self._timeout_exit)
        self._timer.daemon = True
        self._timer.start()
        return self

    def __exit__(self, *args):
        if self._timer:
            self._timer.cancel()

    def _timeout_exit(self):
        print(f"[FATAL] 硬超时 {self.timeout_sec}s，强制退出防止死锁",
              file=sys.stderr, flush=True)
        if self.lock_file:
            release_lock(self.lock_file)
        subprocess.run(
            ["taskkill", "/f", "/t", "/pid", str(os.getpid())],
            capture_output=True, text=True, timeout=3
        )
        os._exit(2)


# ---- atexit / signal 清理钩子 ----

_cleanup_lock_file = None
_cleanup_restart_script = None
_cleanup_llama_port = None
_lock_released = False


def _cleanup_lock():
    global _lock_released
    if not _lock_released:
        _lock_released = True
        if _cleanup_lock_file:
            release_lock(_cleanup_lock_file)


def _atexit_handler():
    _cleanup_lock()
    if _cleanup_llama_port and _cleanup_restart_script:
        try:
            if not _port_open("127.0.0.1", _cleanup_llama_port, timeout=0.5):
                subprocess.Popen(
                    ["powershell", "-Command",
                     f"Start-Process -WindowStyle Hidden -FilePath '{_cleanup_restart_script}'"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
        except Exception:
            pass


def _signal_handler(signum, frame):
    _cleanup_lock()
    sys.exit(1)


def register_cleanup_handlers(lock_file, llama_port=None,
                              restart_script=None):
    """
    注册 atexit 和 signal 钩子，确保进程退出时：
    1. 释放文件锁
    2. 重启 llama-server（如果端口未占用）
    """
    global _cleanup_lock_file, _cleanup_restart_script
    global _cleanup_llama_port, _lock_released
    _cleanup_lock_file = lock_file
    _cleanup_restart_script = restart_script
    _cleanup_llama_port = llama_port
    _lock_released = False

    atexit.register(_atexit_handler)

    try:
        signal.signal(signal.SIGINT, _signal_handler)
    except (OSError, ValueError):
        pass
    try:
        signal.signal(signal.SIGTERM, _signal_handler)
    except (OSError, ValueError):
        pass
