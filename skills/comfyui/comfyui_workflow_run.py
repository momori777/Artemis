#!/usr/bin/env python3
"""
ComfyUI 工作流运行器 — 停 LLM 引擎 → 拉起 ComfyUI 服务器 → POST 工作流 → 出图 → 重启引擎。

与 comfyui_call.py（进程内直推 SD checkpoint）不同，本脚本把 ComfyUI 作为完整服务器
(main.py) 拉起，走 /prompt HTTP API，因此支持任意 API 格式工作流 JSON
（含自定义节点，如 UnetLoaderGGUF / Qwen Image 2.1）。

用法:
    python comfyui_workflow_run.py "正prompt" "负prompt" [seed] [宽] [高] [步数] [CFG] \
        --workflow <api格式工作流.json> [--prefix qwen] [--no-manage-llama]

工作流 JSON 支持两种格式:
    - UI 格式（ComfyUI 前端导出的 {"nodes":..., "links":...}）：自动转换成 API 格式
      （需节点自带 widgets_values_named，aki 前端导出的 JSON 均有）
    - API 格式（node id 为字符串的 {"<id>": {"class_type", "inputs"}}）
覆盖逻辑（仅当请求值有意义时覆盖，否则保留工作流自带参数）:
    - 自动定位接通了 positive/negative/latent 的 KSampler(Advanced)，注入 seed/steps/cfg/宽高
    - 其 positive/negative 输入指向的节点（通常 CLIPTextEncode）注入正/负 prompt
输出: stdout 打印生成的 PNG 路径。
"""
import sys
import os
import json
import time
import random
import subprocess
import urllib.request
import urllib.error

_def = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_d = _def


def _load_config():
    config_path = os.path.join(_def, 'config.yaml')
    if not os.path.exists(config_path):
        print(f"[ERROR] 找不到 config.yaml: {config_path}", file=sys.stderr)
        sys.exit(1)
    import yaml
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


_cfg = _load_config()

if _def not in sys.path:
    sys.path.insert(0, _def)

from skills.shared.llama_lifecycle import (
    acquire_lock, release_lock,
    stop_llama, start_llama,
    stop_strata, start_strata,
    _port_open, _wait_for_vram_stable_nosmoke,
    TimeoutGuard, register_cleanup_handlers,
)

COMFYUI_ROOT = _cfg.get('comfyui_root') or os.path.join(_def, 'deps', 'ComfyUI')
PYTHON_PATH = _cfg['comfyui_python']
OUTPUT_DIR = _cfg['comfyui_temp_output_dir']
COMFY_PORT = int(_cfg.get('comfyui_port', 8188))

LLAMA_LOG_DIR = _cfg['llama_log_dir']
LLAMA_EXE_PATH = _cfg['llama_exe']
LLAMA_MODEL_PATH = _cfg['llama_model']
RESTART_SCRIPT = _cfg['restart_script']
LLAMA_PORT = _cfg.get('llama_port', 8080)

STRATA_PORT = _cfg.get('strata_port')
STRATA_DIR = _cfg.get('strata_dir')
STOPPED_ENGINE = None

HARD_TIMEOUT = int(_cfg.get('skill_timeout', 9000))

LOCK_FILE = os.path.join(OUTPUT_DIR, ".comfyui_running.lock")
LAST_OUTPUT_FILE = os.path.join(OUTPUT_DIR, ".comfyui_last_output.txt")

COMFY_BOOT_TIMEOUT = 300     # seconds for ComfyUI server to come up
RUN_TIMEOUT = int(_cfg.get('workflow_run_timeout', 2400))  # seconds for the job itself


def _strata_running():
    return bool(STRATA_PORT and STRATA_DIR and
                _port_open("127.0.0.1", int(STRATA_PORT), timeout=1))


def _http_json(url, payload=None, timeout=20):
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(url, data=data,
                                 headers={'Content-Type': 'application/json'} if data else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8', errors='replace'))


def _load_workflow(path):
    """Load a workflow JSON in either UI or API format; convert UI -> API."""
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    if isinstance(raw, dict) and 'nodes' in raw:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from workflow_convert import ui_to_api
        api, warnings = ui_to_api(raw)
        for w in warnings:
            print(f"[CONVERT] {w}", file=sys.stderr, flush=True)
        return api
    return raw


def _apply_overrides(wf, positive, negative, seed, width, height, steps, cfg):
    """Find the sampler, wire prompt/size/params through its input links.

    Only override when a value is meaningful (>0 / non-empty): workflow JSON
    keeps its own values otherwise. Picks the sampler that actually has
    positive/negative links wired (orphaned/bypassed samplers are skipped)."""
    ks_id = None
    fallback = None
    for nid, node in wf.items():
        if node.get('class_type') not in ('KSampler', 'KSamplerAdvanced'):
            continue
        ins = node.get('inputs') or {}
        wired = lambda k: isinstance(ins.get(k), list) and len(ins[k]) == 2
        if wired('positive') or wired('negative') or wired('model'):
            ks_id = nid
            break
        if fallback is None:
            fallback = nid
    if ks_id is None:
        ks_id = fallback
    if ks_id is None:
        raise ValueError("workflow has no KSampler/KSamplerAdvanced node")
    ks = wf[ks_id]['inputs']
    if seed and seed > 0:
        key = 'noise_seed' if 'noise_seed' in ks else 'seed'
        ks[key] = seed
    if steps and steps > 0:
        ks['steps'] = steps
    if cfg and cfg > 0:
        ks['cfg'] = cfg
    for role, text in (('positive', positive), ('negative', negative)):
        if not text:
            continue
        ref = ks.get(role)
        if isinstance(ref, list) and len(ref) == 2:
            wf[str(ref[0])]['inputs']['text'] = text
    ref = ks.get('latent_image')
    if isinstance(ref, list) and len(ref) == 2 and width > 0 and height > 0:
        lat = wf[str(ref[0])]['inputs']
        lat['width'] = width
        lat['height'] = height
        lat['batch_size'] = 1
    return wf


def _start_comfy_server():
    comfy_main = os.path.join(COMFYUI_ROOT, 'main.py')
    if not os.path.exists(comfy_main):
        raise FileNotFoundError(f"ComfyUI main.py not found: {comfy_main}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    log_path = os.path.join(OUTPUT_DIR, "comfyui_server.log")
    log = open(log_path, 'ab')
    proc = subprocess.Popen(
        [PYTHON_PATH, comfy_main, '--port', str(COMFY_PORT)],
        cwd=COMFYUI_ROOT, stdout=log, stderr=subprocess.STDOUT,
    )
    print(f"[COMFY] server pid={proc.pid} launching on {COMFY_PORT} "
          f"(log: {log_path})", file=sys.stderr, flush=True)
    t0 = time.time()
    while time.time() - t0 < COMFY_BOOT_TIMEOUT:
        if proc.poll() is not None:
            raise RuntimeError(f"ComfyUI server exited early (code {proc.returncode}), "
                               f"see {log_path}")
        try:
            _http_json(f"http://127.0.0.1:{COMFY_PORT}/system_stats", timeout=4)
            print(f"[COMFY] up after {time.time()-t0:.0f}s", file=sys.stderr, flush=True)
            return proc
        except Exception:
            time.sleep(3)
    proc.kill()
    raise RuntimeError(f"ComfyUI did not come up within {COMFY_BOOT_TIMEOUT}s")


def _stop_comfy_server(proc):
    try:
        if proc and proc.poll() is None:
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                           capture_output=True, timeout=30)
            print("[COMFY] server tree killed", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[COMFY] kill failed: {e}", file=sys.stderr, flush=True)
    for _ in range(60):
        if not _port_open("127.0.0.1", COMFY_PORT, timeout=1):
            break
        time.sleep(1)
    _wait_for_vram_stable_nosmoke(max_wait=30)


def _run_workflow(proc, wf, prompt_prefix_unused=None):
    body = {"prompt": wf, "client_id": "artemis-workflow"}
    r = _http_json(f"http://127.0.0.1:{COMFY_PORT}/prompt", payload=body, timeout=30)
    if r.get('error'):
        raise RuntimeError(f"prompt validation error: {json.dumps(r, ensure_ascii=False)[:1500]}")
    prompt_id = r['prompt_id']
    print(f"[COMFY] queued prompt {prompt_id}", file=sys.stderr, flush=True)

    t0 = time.time()
    while time.time() - t0 < RUN_TIMEOUT:
        if proc.poll() is not None:
            raise RuntimeError(f"ComfyUI server died mid-run (code {proc.returncode})")
        try:
            h = _http_json(f"http://127.0.0.1:{COMFY_PORT}/history/{prompt_id}", timeout=15)
        except Exception as e:
            print(f"[COMFY] history poll err: {e}", file=sys.stderr, flush=True)
            time.sleep(5)
            continue
        entry = h.get(prompt_id)
        if entry:
            status = (entry.get('status') or {}).get('status_str')
            if status == 'error':
                msgs = (entry.get('status') or {}).get('messages', [])
                raise RuntimeError(f"workflow execution error: {json.dumps(msgs, ensure_ascii=False)[:1500]}")
            print(f"[COMFY] history ready after {time.time()-t0:.0f}s", file=sys.stderr, flush=True)
            return entry
        time.sleep(5)
    raise RuntimeError(f"workflow did not finish within {RUN_TIMEOUT}s")


def _collect_output(entry):
    out_root = os.path.join(COMFYUI_ROOT, 'output')
    images = []
    for node_out in (entry.get('outputs') or {}).values():
        for img in node_out.get('images', []) or []:
            if img.get('type') == 'output':
                images.append(img)
    if not images:
        raise RuntimeError(f"no output images in history: {json.dumps(entry.get('outputs', {}))[:500]}")
    img = images[-1]
    src = os.path.join(out_root, img.get('subfolder', ''), img['filename'])
    if not os.path.exists(src):
        raise RuntimeError(f"output image missing on disk: {src}")
    import shutil
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    from datetime import datetime
    stem = os.path.splitext(os.path.basename(img['filename']))[0]
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    dst = os.path.join(OUTPUT_DIR, f"comfyui_{stem}_{ts}.png")
    shutil.copy2(src, dst)
    with open(LAST_OUTPUT_FILE, 'w') as f:
        f.write(dst)
    print(f"[COMFY] saved {src} -> {dst} "
          f"({os.path.getsize(dst)/1024:.0f} KB)", file=sys.stderr, flush=True)
    return dst


def _restart_engine(out_path):
    """Bring the LLM engine back (mirrors comfyui_call.py)."""
    import torch
    if STOPPED_ENGINE == "strata":
        ok = start_strata(port=int(STRATA_PORT), timeout=300, cfg=_cfg)
        if not ok:
            print("[STRATA] 启动失败，等待 VRAM 后重试...", file=sys.stderr, flush=True)
            time.sleep(20)
            ok = start_strata(port=int(STRATA_PORT), timeout=300, cfg=_cfg)
        if not ok:
            print(f"[STRATA] 启动失败，图像已保存到 {out_path}", file=sys.stderr, flush=True)
        else:
            print("[STRATA] 引擎已就绪", file=sys.stderr, flush=True)
    elif STOPPED_ENGINE == "llama":
        ok = start_llama(port=LLAMA_PORT, exe_path=LLAMA_EXE_PATH,
                         model_path=LLAMA_MODEL_PATH, log_dir=LLAMA_LOG_DIR,
                         use_mmap=True)
        if not ok:
            time.sleep(15)
            ok = start_llama(port=LLAMA_PORT, exe_path=LLAMA_EXE_PATH,
                             model_path=LLAMA_MODEL_PATH, log_dir=LLAMA_LOG_DIR,
                             use_mmap=True)
        if not ok:
            print(f"[LLAMA] 启动失败，图像已保存到 {out_path}", file=sys.stderr, flush=True)
        else:
            print("[LLAMA] 已就绪", file=sys.stderr, flush=True)


def run_workflow(workflow_path, positive, negative, seed, width, height,
                 steps, cfg, manage_llama=True):
    t0 = time.time()
    wf = _load_workflow(workflow_path)
    wf = _apply_overrides(wf, positive, negative, seed, width, height, steps, cfg)

    global STOPPED_ENGINE
    if manage_llama:
        if _strata_running():
            STOPPED_ENGINE = "strata"
            print(f"[STRATA] 检测到常驻引擎 (port {STRATA_PORT})，停 Strata",
                  file=sys.stderr, flush=True)
            stop_strata(port=int(STRATA_PORT), wait_vram_stable=True)
        else:
            STOPPED_ENGINE = "llama"
            stop_llama(port=LLAMA_PORT, wait_vram_stable=True)

    proc = None
    out_path = None
    try:
        proc = _start_comfy_server()
        entry = _run_workflow(proc, wf)
        out_path = _collect_output(entry)
    finally:
        _stop_comfy_server(proc)

    if manage_llama:
        sys.stderr.flush()
        _restart_engine(out_path or '(no output yet)')
    print(f"完成! 总耗时: {time.time()-t0:.1f}s", file=sys.stderr, flush=True)
    sys.stdout.write(out_path + '\n')
    sys.stdout.flush()
    return out_path


if __name__ == "__main__":
    argv = sys.argv[1:]
    wf_path = None
    if '--workflow' in argv:
        i = argv.index('--workflow')
        wf_path = argv[i + 1]
        del argv[i:i + 2]

    no_manage = '--no-manage-llama' in argv
    argv = [a for a in argv if a != '--no-manage-llama']

    if not wf_path or len(argv) < 2:
        print('用法: python comfyui_workflow_run.py "正prompt" "负prompt" '
              '[seed] [宽] [高] [步数] [CFG] --workflow <api工作流.json> [--no-manage-llama]',
              file=sys.stderr)
        sys.exit(1)

    from skills.shared.vram import should_stop_llama
    if not no_manage and not should_stop_llama("comfyui"):
        no_manage = True

    positive, negative = argv[0], argv[1]
    seed = int(argv[2]) if len(argv) > 2 and int(argv[2]) > 0 else 0  # 0 => keep workflow's own seed
    width = int(argv[3]) if len(argv) > 3 else 832
    height = int(argv[4]) if len(argv) > 4 else 1216
    steps = int(argv[5]) if len(argv) > 5 else 20
    cfg = float(argv[6]) if len(argv) > 6 else 2.0

    lock_pid, lock_exe = acquire_lock(LOCK_FILE, label="comfyui")
    if lock_pid is None:
        print("[ERROR] 已有 comfyui 实例在运行，跳过本次调用", file=sys.stderr)
        sys.exit(0)

    _is_strata = _strata_running()
    register_cleanup_handlers(
        lock_file=LOCK_FILE,
        llama_port=None if (no_manage or _is_strata) else LLAMA_PORT,
        restart_script=None if (no_manage or _is_strata) else RESTART_SCRIPT,
    )

    try:
        with TimeoutGuard(HARD_TIMEOUT, lock_file=LOCK_FILE):
            run_workflow(wf_path, positive, negative, seed, width, height,
                         steps, cfg, manage_llama=not no_manage)
    except TimeoutError:
        if os.path.exists(LAST_OUTPUT_FILE):
            with open(LAST_OUTPUT_FILE) as f:
                p = f.read().strip()
            if p and os.path.exists(p):
                print(f"[TIMEOUT] 超时但图片已生成: {p}", file=sys.stderr, flush=True)
                sys.stdout.write(p + '\n')
                sys.exit(0)
        print("[TIMEOUT] 超时，无输出文件", file=sys.stderr, flush=True)
        sys.exit(1)
    except Exception:
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    finally:
        release_lock(LOCK_FILE)
