# -*- coding: utf-8 -*-
"""
llama_config.py — 统一 LLM 启动参数解析器

从 config.yaml 读取 llama 区块 + model_profiles 预设表，
按模型文件名自动匹配预设参数，合并返回最终启动参数。

用法 (Python import):
    from skills.shared.llama_config import resolve_llama_params, build_llama_args
    cfg = load_config("config.yaml")
    params = resolve_llama_params(cfg)
    args = build_llama_args(params)

用法 (CLI 输出 JSON):
    python skills/shared/llama_config.py --json
    python skills/shared/llama_config.py --model <path> --json
"""

import os
import sys
import json


# ── config.yaml 读取 ──────────────────────────────────────

def load_config(path=None):
    """读取 config.yaml，返回 dict。path 为 None 时自动在项目根目录查找。"""
    if path is None:
        # 向上查找项目根 (skills/shared/llama_config.py → 项目根)
        _dir = os.path.dirname(os.path.abspath(__file__))
        for _ in range(3):
            _parent = os.path.dirname(_dir)
            if os.path.isfile(os.path.join(_parent, "config.yaml")):
                path = os.path.join(_parent, "config.yaml")
                break
            _dir = _parent
    if not path or not os.path.isfile(path):
        return {}
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # 无 yaml 时使用简单回退
        return {}
    except Exception:
        return {}


# ── 模型预设匹配 ──────────────────────────────────────────

def _basename_lower(p):
    """提取文件名全小写"""
    if not p:
        return ""
    return os.path.basename(p).lower()


def match_profile(model_path, profiles):
    """
    按模型文件名匹配第一个命中预设。
    profiles: [{ name, match: ["keyword", ...], params: {...} }]
    返回命中的 params dict，或 None。
    """
    bl = _basename_lower(model_path)
    if not bl or not profiles:
        return None
    for p in profiles:
        matches = p.get("match", [])
        if not matches:
            continue
        for kw in matches:
            if not kw:
                continue
            if kw.lower() in bl:
                # 返回该预设的 params + name
                return {
                    "name": p.get("name", ""),
                    "params": p.get("params", {}),
                }
    return None


# ── 参数解析 ──────────────────────────────────────────────

def resolve_llama_params(cfg, model_path=None):
    """
    返回最终 llama 启动参数字典。

    合并优先级: model_profile.params > llama 区块 > 内置默认值。

    Args:
        cfg: load_config() 返回的 dict。
        model_path: 可选，覆盖 cfg["llama_model"]。

    Returns: dict 包含所有启动参数。
    """
    if model_path is None:
        model_path = cfg.get("llama_model", "")

    llm_block = cfg.get("llama", {})
    profiles = cfg.get("model_profiles", [])
    profile_match = match_profile(model_path, profiles)
    p_params = (profile_match or {}).get("params", {})

    def _v(key, default):
        """带优先级的取值: profile > llama_block > default"""
        if key in p_params:
            return p_params[key]
        return llm_block.get(key, default)

    def _rea(key="rea", default="off"):
        """rea 参数规范化：YAML 的 on/off 会被解析成 bool，这里转回字符串"""
        v = _v(key, default)
        if isinstance(v, bool):
            return "on" if v else "off"
        return str(v)

    model_name = cfg.get("llama_model_name", "") or (
        os.path.basename(model_path) if model_path else "local-model"
    )
    model_id = cfg.get("llama_model_id", "") or ("local/" + model_name)

    # ── 自动校准: 单一真源 = llama_model ──
    # 问题：llama_model_name / llama_model_id 是独立字段，用户改 llama_model 后
    # 常常忘记同步，导致 model id 指向旧模型（例如 27B 模型却配 llama/qwen3.6-35b）。
    # 校准：若 model_id 的后缀（/ 之后）与 model_name 不一致，说明是残留值，
    #       用 model_name 重构 id，前缀（local/或 llama/）保留。
    _id_suffix = model_id.rsplit("/", 1)[-1] if "/" in model_id else ""
    if _id_suffix and _id_suffix != model_name:
        _prefix = model_id.rsplit("/", 1)[0] if "/" in model_id else "local"
        model_id = _prefix + "/" + model_name
        # 静默校准：多数情况下前缀 local/ 与 llama/ 是等价的本地别名，
        # 这里不打印噪声日志，避免脚本输出被污染。

    params = {
        "model_path": model_path,
        "model_name": model_name,
        "model_id": model_id,
        "exe_path": cfg.get("llama_exe", ""),
        "port": int(cfg.get("llama_port", 8080)),
        "log_dir": cfg.get("llama_log_dir", ""),
        "restart_script": cfg.get("restart_script", ""),
        # llama 区块参数 + profile 覆盖
        "context": int(_v("context", 150000)),
        "batch_size": int(_v("batch_size", 2048)),
        "ubatch_size": int(_v("ubatch_size", 1024)),
        "threads": int(_v("threads", 24)),
        "ngl": int(_v("ngl", 41)),
        "ctk": _v("ctk", "q8_0"),
        "ctv": _v("ctv", "q8_0"),
        "cpu_moe": bool(_v("cpu_moe", False)),
        "cpu_mask": _v("cpu_mask", ""),
        "cache_ram": int(_v("cache_ram", 0)),       # 0 = 不传
        "no_warmup": bool(_v("no_warmup", False)),
        # 只在 profile 明确指定时启用 MTP；否则由 _auto_mtp 决定
        "spec_draft_n_max": int(p_params.get("spec_draft_n_max", 0)),
        "rea_mode": _rea(),
        # MTP 自动检测 fallback: 只在无 profile 且模型名含 "mtp" 时启用
        "_auto_mtp": profile_match is None and "mtp" in _basename_lower(model_path),
        "_default_mtp_n": int(llm_block.get("spec_draft_n_max", 1)),
        # 附加信息
        "_profile_name": (profile_match or {}).get("name", ""),
    }
    return params


def build_llama_args(params):
    """
    从 resolve_llama_params() 返回的 dict 构建命令行参数列表。
    返回完整 args 列表（适合 subprocess.Popen / Start-Process）。
    """
    args = [
        params["exe_path"],
        "-m", params["model_path"],
        "-c", str(params["context"]),
        "--flash-attn", "on",
        "-ctk", params["ctk"],
        "-ctv", params["ctv"],
        "--no-mmap",
    ]

    if params["cpu_moe"]:
        args.append("--cpu-moe")
    mask = params.get("cpu_mask", "")
    if mask:
        args += ["--cpu-mask", mask]

    args += [
        "--batch-size", str(params["batch_size"]),
        "--ubatch-size", str(params["ubatch_size"]),
        "--threads", str(params["threads"]),
        "-rea", params["rea_mode"],
        "--jinja",
        "--reasoning-preserve",
    ]

    if params["cache_ram"] > 0:
        args += ["--cache-ram", str(params["cache_ram"])]

    # CPU-only mode: hide CUDA devices so MTP draft context stays on CPU
    # (using --main-gpu -1 causes GGML assert failure, use env var instead)

    args += [
        "--parallel", "1",
        "--kv-unified",
    ]

    if params["no_warmup"]:
        args.append("--no-warmup")

    # MTP 投机解码:
    # 1) profile 指定了 spec_draft_n_max > 0
    # 2) 自动检测 (无 profile 匹配但模型名含 "mtp")
    mtp_n = params.get("spec_draft_n_max", 0)
    if mtp_n <= 0 and params.get("_auto_mtp"):
        mtp_n = params.get("_default_mtp_n", 1)
    if mtp_n > 0:
        args += ["--spec-type", "draft-mtp", "--spec-draft-n-max", str(mtp_n)]

    # ── 模型别名 ──
    # 通过 --alias 让 llama.cpp 返回 OpenClaw 能识别的模型 id
    # config.yaml 中设置 llama_model_name 来控制别名
    _alias = params.get("model_name", "")
    if _alias:
        args += ["--alias", _alias]

    args += [
        "--port", str(params["port"]),
        "--timeout", "600",
    ]

    return args


# ── CLI 入口 ──────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LLM Config Resolver")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出完整启动参数")
    parser.add_argument("--model", type=str, default=None, help="模型路径（覆盖 config.yaml）")
    parser.add_argument("--args-only", action="store_true", help="只输出命令行参数数组（JSON）")
    args = parser.parse_args()

    cfg = load_config()
    params = resolve_llama_params(cfg, model_path=args.model)
    params.pop("_auto_mtp", None)
    params.pop("_default_mtp_n", None)
    params.pop("_profile_name", None)

    if args.args_only:
        raw = build_llama_args(params)
        print(json.dumps(raw, ensure_ascii=False))
    elif args.json:
        raw = build_llama_args(params)
        result = {
            "params": {k: v for k, v in params.items() if not k.startswith("_")},
            "args": raw,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        raw = build_llama_args(params)
        print("=== Model Config ===")
        for k, v in params.items():
            if not k.startswith("_"):
                print(f"  {k}: {v}")
        print(f"\n  args ({len(raw)-1} items):")
        for i, a in enumerate(raw[1:], 1):
            print(f"    [{i}] {a}")