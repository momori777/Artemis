#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
START HERE — one entry point for the whole AI Girlfriend stack.

    START-HERE.bat          (Windows, double-click or from a terminal)
    START-HERE.sh           (Linux / macOS / Git-Bash / WSL)

What it does:

  1. shows the current selection (LLM engine+model, ComfyUI model, SoVITS voice,
     ports) and lets you change any of them from a menu;
  2. writes the selection into config.yaml (line-by-line — comments and hand
     formatting survive) plus skills/sovits/weights/weight.json for the voice;
  3. starts only what is not already up, then health-checks everything and
     prints the URLs: Strata (optional) → daemon (llama.cpp + embedding +
     headroom + live2d + artemis + gateway + task board + dashboard + webchat)
     → ComfyUI → GPT-SoVITS HTTP API.

Everything is optional-by-flag: `--no-comfy`, `--no-tts`, `--no-strata`, and
`--stop` closes the whole stack again.

This file is the cross-platform implementation; the .bat/.sh files are thin
shims so there is exactly one copy of the logic.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

# ── Layout ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
# The three overrides exist so the script can be exercised against a scratch
# copy (tests); normal runs use the repo paths.
CONFIG_PATH = Path(os.environ.get("START_HERE_CONFIG") or (ROOT / "config.yaml"))
STATE_PATH = Path(os.environ.get("START_HERE_STATE") or (ROOT / ".start-here.json"))
LOG_DIR = Path(os.environ.get("START_HERE_LOGDIR") or (ROOT / "logs" / "start-here"))

DASHBOARD_PORT = 19260   # fixed: web-chat scripts and openclaw.json reference it
WEBCHAT_PORT = 19270     # fixed: same reason (web-chat is served by the daemon)

IS_WIN = os.name == "nt"
MANAGED_MARKER = "# ── START-HERE managed keys (written by START-HERE.bat/.sh) ──"

# (config key, default, human label) — ordered as shown in the port menu
PORT_KEYS = [
    ("llama_port", 9931, "llama.cpp / OpenAI-compatible LLM API"),
    ("strata_port", 8080, "Strata engine (Qwen3.8-Flash-Next)"),
    ("comfyui_port", 8188, "ComfyUI"),
    ("tts_port", 9880, "GPT-SoVITS HTTP API"),
    ("headroom_port", 19251, "Headroom proxy (mem0 + context compression)"),
    ("embedding_port", 9999, "Embedding server"),
    ("live2d_port", 19200, "Live2D bridge"),
    ("artemis_bridge_port", 19250, "Artemis bridge (MCP)"),
    ("gateway_port", 18789, "OpenClaw gateway"),
    ("task_board_port", 19280, "Task board"),
    ("llama_debugger_port", 8765, "Llama debugger UI"),
]

# ── Tiny console layer ────────────────────────────────────────────────────
_COLOR = False
GREEN, RED, YELLOW, CYAN, DIM, BOLD, RESET = "32", "31", "33", "36", "2", "1", "0"


def _init_console() -> None:
    """UTF-8 output + ANSI on Windows consoles that support it."""
    global _COLOR
    if IS_WIN:
        try:  # enable VT processing (Windows 10+); harmless when unsupported
            import ctypes

            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    try:
        _COLOR = bool(sys.stdout.isatty()) and os.environ.get("NO_COLOR") is None
    except Exception:
        _COLOR = False


def paint(text: str, color: str) -> str:
    return f"\033[{color}m{text}\033[0m" if _COLOR else text


def say(text: str = "", **kwargs) -> None:
    """print() with immediate flush so progress dots appear while we wait."""
    kwargs.setdefault("flush", True)
    print(text, **kwargs)


def info(text: str) -> None:
    say("  " + text)


def ok(text: str) -> None:
    say("  " + paint("OK  ", GREEN) + text)


def warn(text: str) -> None:
    say("  " + paint("WARN", YELLOW) + "  " + text)


def fail(text: str) -> None:
    say("  " + paint("FAIL", RED) + "  " + text)


def section(title: str) -> None:
    say("")
    say(paint(f"── {title} " + "─" * max(0, 58 - len(title)), DIM))


def human_size(n: int) -> str:
    gb = n / (1024 ** 3)
    if gb >= 1:
        return f"{gb:5.2f} GB"
    return f"{n / (1024 ** 2):5.0f} MB"


def tail(path: Path, lines: int = 10) -> str:
    try:
        data = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return "(no log)"
    return "\n".join("      " + ln for ln in data[-lines:])


# ── config.yaml (comment-preserving line edits, never a YAML round-trip) ──
def load_yaml():
    try:
        import yaml  # noqa: WPS433 (runtime dependency, same as the daemon)

        return yaml
    except ImportError:
        return None


def _interpreter_has_yaml(cmd: list[str]) -> bool:
    try:
        return subprocess.run(
            [*cmd, "-c", "import yaml"], capture_output=True, timeout=25
        ).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def ensure_yaml() -> None:
    """Re-exec under an interpreter that has PyYAML.

    The `python` picked by START-HERE.bat/.sh can differ from the one that ran
    quick_setup (multiple versions on PATH, Microsoft Store stub, py launcher).
    Instead of installing anything, hand over to a candidate that already works —
    that is also the interpreter the daemon needs.
    """
    if load_yaml() is not None:
        return
    if os.environ.get("START_HERE_REEXEC") == "1":
        return  # one attempt only; load_cfg() prints the install hint
    candidates = [
        ["py", "-3.12"], ["py", "-3.13"], ["py", "-3"], ["python"], ["python3"],
        [os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python312\python.exe")],
        [sys.executable],
    ]
    for cmd in candidates:
        exe = cmd[0]
        path = exe if os.path.isabs(exe) else shutil.which(exe)
        if not path or not Path(path).is_file():
            continue
        if not _interpreter_has_yaml(cmd):
            continue
        try:
            same = os.path.samefile(path, sys.executable) and not cmd[1:]
        except OSError:
            same = False
        if same:
            continue
        env = dict(os.environ, START_HERE_REEXEC="1")
        try:
            os.execve(path, [path, *cmd[1:], str(Path(__file__).resolve()), *sys.argv[1:]], env)
        except OSError:
            continue
    raise SystemExit("PyYAML is required (the daemon uses it too):\n    python -m pip install pyyaml")


def load_cfg() -> dict:
    yaml = load_yaml()
    if yaml is None:
        raise SystemExit(
            "PyYAML is required (the daemon uses it too):\n"
            "    python -m pip install pyyaml"
        )
    if not CONFIG_PATH.is_file():
        raise SystemExit(
            f"config.yaml not found at {CONFIG_PATH}\n"
            "Run quick_setup.ps1 / quick_setup.sh first, or copy config.example.yaml."
        )
    text = read_config_text()[0]
    cfg = yaml.safe_load(text) or {}
    if not isinstance(cfg, dict):
        raise SystemExit(f"{CONFIG_PATH} does not contain a YAML mapping")
    return cfg


def read_config_text() -> tuple[str, bool]:
    raw = CONFIG_PATH.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    crlf = "\r\n" in text
    return text.replace("\r\n", "\n"), crlf


def write_config_text(text: str, crlf: bool) -> None:
    data = (text.replace("\n", "\r\n") if crlf else text).encode("utf-8")
    if CONFIG_PATH.exists():
        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = CONFIG_PATH.with_name(f"{CONFIG_PATH.name}.bak-starthere-{stamp}")
        try:
            backup.write_bytes(CONFIG_PATH.read_bytes())
            for old in sorted(CONFIG_PATH.parent.glob(f"{CONFIG_PATH.name}.bak-starthere-*"))[:-5]:
                old.unlink(missing_ok=True)
        except OSError as exc:
            warn(f"could not back up config.yaml: {exc}")
    CONFIG_PATH.write_bytes(data)


_WIN_PATH = re.compile(r"^[A-Za-z]:[\\/]")


def format_value(value) -> str:
    s = str(value)
    if s == "":
        return '""'
    if _WIN_PATH.match(s):
        return s  # D:\model2\x.gguf — plain scalar, backslashes are literal
    if re.search(r"[#:]|^\s|\s$", s) or s.lower() in (
        "yes", "no", "true", "false", "null", "on", "off", "~"
    ):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def set_scalar(text: str, key: str, value) -> str:
    """Replace `key: value` at top level, preserving the trailing comment."""
    val = format_value(value)
    pattern = re.compile(
        rf"^(?P<key>{re.escape(key)}[ \t]*:[ \t]*)(?P<val>[^\n#]*?)(?P<tail>[ \t]*(?:#[^\n]*)?)$",
        re.M,
    )
    match = pattern.search(text)
    if match:
        return text[:match.start("val")] + val + text[match.end("val"):]
    # Append to the managed block so re-runs stay idempotent.
    if MANAGED_MARKER not in text:
        text = text.rstrip("\n") + f"\n\n{MANAGED_MARKER}\n"
    return text.rstrip("\n") + f"\n{key}: {val}\n"


def ensure_map_entry(text: str, map_key: str, sub_key: str, value) -> str:
    """Add/update `sub_key: value` inside the `map_key:` block (2-space indent)."""
    lines = text.split("\n")
    header = None
    for i, line in enumerate(lines):
        if re.match(rf"^{re.escape(map_key)}[ \t]*:[ \t]*$", line):
            header = i
            break
    if header is None:
        return text  # map missing: leave the file alone rather than guess
    end = len(lines)
    for j in range(header + 1, len(lines)):
        line = lines[j]
        if line.strip() and not line.startswith((" ", "\t", "#")):
            end = j
            break
    entry_pat = re.compile(rf"^([ \t]+)({re.escape(sub_key)}[ \t]*:[ \t]*)([^\n#]*?)([ \t]*(?:#[^\n]*)?)$")
    insert_at = header + 1
    for j in range(header + 1, end):
        m = entry_pat.match(lines[j])
        if m:
            lines[j] = m.group(1) + m.group(2) + format_value(value) + m.group(4)
            return "\n".join(lines)
        if lines[j].strip() and not lines[j].lstrip().startswith("#"):
            insert_at = j + 1
    lines.insert(insert_at, f"  {sub_key}: {format_value(value)}")
    return "\n".join(lines)


def plan_edits(selection: dict, cfg: dict) -> list[tuple[str, object, object]]:
    """[(key, old, new)] for every config scalar the launcher manages."""
    current_ports = {k: cfg.get(k) for k, _d, _l in PORT_KEYS}
    edits = [
        ("llm_engine", cfg.get("llm_engine"), selection["engine"]),
    ]
    if selection["engine"] == "llama" and selection.get("llm"):
        edits.append(("llama_model", cfg.get("llama_model", ""), str(selection["llm"])))
    if selection.get("comfy"):
        edits.append((
            "comfyui_default_checkpoint",
            cfg.get("comfyui_default_checkpoint", ""),
            selection["comfy"],
        ))
    for key, _default, _label in PORT_KEYS:
        new = selection["ports"].get(key)
        if new is not None:
            edits.append((key, current_ports.get(key), int(new)))
    # keep the dashboard/webchat constants visible in config.yaml too
    return edits


def apply_config(selection: dict, dry_run: bool = False) -> list[str]:
    cfg = load_cfg()
    text, crlf = read_config_text()
    notes: list[str] = []
    for key, old, new in plan_edits(selection, cfg):
        if str(old) == str(new):
            continue
        text = set_scalar(text, key, new)
        notes.append(f"{key}: {old or '(unset)'} → {new}")
    if selection["engine"] == "llama" and selection.get("llm"):
        short = selection.get("llm_short") or ""
        if short:
            before = text
            text = ensure_map_entry(text, "llama_model_map", short, str(selection["llm"]))
            if text != before:
                notes.append(f"llama_model_map.{short} → {selection['llm']}")
    if not dry_run and notes:
        write_config_text(text, crlf)
    return notes


# ── discovery ────────────────────────────────────────────────────────────
def _resolve(p: str) -> Path:
    q = Path(os.path.expandvars(os.path.expanduser(str(p))))
    return q if q.is_absolute() else (ROOT / q)


def _model_profile(cfg: dict, path: Path) -> str:
    name = path.name.lower()
    for prof in cfg.get("model_profiles") or []:
        for kw in prof.get("match") or []:
            if kw and kw.lower() in name:
                return prof.get("name", "")
    return ""


def discover_llm(cfg: dict) -> list[dict]:
    """Every .gguf the config points at, plus the usual model folders."""
    found: dict[str, dict] = {}

    def add(path: Path, short: str = "") -> None:
        try:
            if not path.is_file() or path.suffix.lower() != ".gguf":
                return
            size = path.stat().st_size
        except OSError:
            return
        if size < 50 * 1024 ** 2:  # skip tokenizer/partial shards
            return
        key = str(path)
        if key in found:
            if short and not found[key]["short"]:
                found[key]["short"] = short
            return
        found[key] = {
            "path": path,
            "short": short,
            "size": size,
            "profile": _model_profile(cfg, path),
        }

    for short, raw in (cfg.get("llama_model_map") or {}).items():
        if isinstance(raw, str):
            add(_resolve(raw), short)
    if cfg.get("llama_model"):
        add(_resolve(cfg["llama_model"]))

    dirs = [ROOT / "models", ROOT / "llm"]
    for raw in list((cfg.get("llama_model_map") or {}).values()) + [cfg.get("llama_model", "")]:
        if isinstance(raw, str) and raw.strip():
            try:
                dirs.append(_resolve(raw).parent)
            except OSError:
                pass
    seen_dirs = set()
    for d in dirs:
        try:
            d = d.resolve()
        except OSError:
            continue
        if d in seen_dirs or not d.is_dir():
            continue
        seen_dirs.add(d)
        for p in sorted(d.glob("*.gguf")):
            add(p)

    current = str(_resolve(cfg.get("llama_model", ""))) if cfg.get("llama_model") else ""
    items = sorted(found.values(), key=lambda it: (str(it["path"]) != current, it["path"].name.lower()))
    for it in items:
        it["current"] = str(it["path"]) == current
    return items


def comfy_model_dirs(cfg: dict) -> list[tuple[Path, str]]:
    dirs: list[tuple[Path, str]] = []
    ckpt = cfg.get("comfyui_checkpoints_dir")
    if ckpt:
        dirs.append((_resolve(ckpt), "checkpoint"))
    dm = cfg.get("comfyui_diffusion_models_dir")
    if dm:
        dirs.append((_resolve(dm), "diffusion"))
    root = cfg.get("comfyui_root")
    if root:
        base = _resolve(root)
        dirs.append((base / "models" / "checkpoints", "checkpoint"))
        dirs.append((base / "models" / "diffusion_models", "diffusion"))
    uniq, seen = [], set()
    for d, kind in dirs:
        try:
            d = d.resolve()
        except OSError:
            continue
        if d in seen:
            continue
        seen.add(d)
        uniq.append((d, kind))
    return uniq


def discover_comfy(cfg: dict) -> list[dict]:
    items: dict[str, dict] = {}
    for folder, kind in comfy_model_dirs(cfg):
        if not folder.is_dir():
            continue
        for p in sorted(folder.iterdir()):
            if p.suffix.lower() not in (".safetensors", ".ckpt", ".gguf"):
                continue
            try:
                size = p.stat().st_size
            except OSError:
                continue
            if size < 50 * 1024 ** 2:
                continue
            items.setdefault(str(p), {"path": p, "size": size, "kind": kind})
    current = (cfg.get("comfyui_default_checkpoint") or "").strip()
    out = list(items.values())
    out.sort(key=lambda it: (it["path"].name != current, it["kind"] != "checkpoint", it["path"].name.lower()))
    return out


def sovits_weights_root(cfg: dict) -> Path:
    raw = cfg.get("sovits_weights_dir")
    base = _resolve(raw) if raw else (ROOT / "skills" / "sovits")
    return base / "weights"


def _voice_prefix(name: str) -> str:
    return re.split(r"[-_. ]", Path(name).stem)[0].lower()


def discover_voices(cfg: dict) -> list[dict]:
    folder = sovits_weights_root(cfg)
    if not folder.is_dir():
        return []
    groups: dict[str, dict] = {}
    for p in folder.iterdir():
        suffix = p.suffix.lower()
        if suffix not in (".ckpt", ".pth"):
            continue
        key = _voice_prefix(p.name)
        group = groups.setdefault(key, {"key": key, "ckpt": None, "pth": None})
        slot = "ckpt" if suffix == ".ckpt" else "pth"
        if group[slot] is None or p.stat().st_mtime > group[slot].stat().st_mtime:
            group[slot] = p
    out = [g for g in groups.values() if g["ckpt"] and g["pth"]]
    out.sort(key=lambda g: g["key"])

    current = current_voice(cfg)
    for g in out:
        g["current"] = (
            current is not None
            and current.get("ckpt") == g["ckpt"].name
            and current.get("pth") == g["pth"].name
        )
    return out


def current_voice(cfg: dict) -> dict | None:
    for name in ("weight.json",):
        p = sovits_weights_root(cfg) / name
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return {
                "ckpt": (data.get("GPT") or {}).get("v2", ""),
                "pth": (data.get("SoVITS") or {}).get("v2", ""),
            }
        except (OSError, ValueError):
            return None
    return None


# ── ports / health ───────────────────────────────────────────────────────
def port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def port_busy_any(port: int) -> bool:
    return port_open(port, "127.0.0.1") or (not IS_WIN and port_open(port, "::1"))


def http_ok(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return 200 <= resp.status < 500
    except (urllib.error.URLError, OSError, ValueError):
        return False


def wait_for(check, timeout: int, label: str, interval: float = 1.0) -> bool:
    started = time.time()
    last_dot = started
    while time.time() - started < timeout:
        if check():
            say("")  # terminate the "starting ..." line
            return True
        now = time.time()
        if now - last_dot >= 5:
            last_dot = now
            print(".", end="", flush=True)
        time.sleep(interval)
    say("")
    return False


def spawn(name: str, cmd: list[str], cwd: Path, log: Path, env: dict | None = None):
    log.parent.mkdir(parents=True, exist_ok=True)
    handle = open(log, "ab", buffering=0)
    banner = (
        f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')}  {name} =====\n"
        f"cwd: {cwd}\ncmd: {' '.join(str(c) for c in cmd)}\n"
    )
    handle.write(banner.encode("utf-8", "replace"))
    kwargs = {}
    if IS_WIN:
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    full_env = dict(os.environ)
    full_env.setdefault("PYTHONUTF8", "1")
    full_env.setdefault("PYTHONIOENCODING", "utf-8")
    if env:
        full_env.update(env)
    try:
        return subprocess.Popen(
            [str(c) for c in cmd],
            cwd=str(cwd),
            stdout=handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            env=full_env,
            **kwargs,
        )
    finally:
        handle.close()


# ── menu ─────────────────────────────────────────────────────────────────
def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default != "" else ""
    try:
        raw = input(f"  {prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        say("")
        return default
    return raw or default


def choose(title: str, options: list[dict], current_key: str | None, allow_cancel: bool = True) -> dict | None:
    section(title)
    for idx, opt in enumerate(options, 1):
        mark = paint("*", GREEN) if opt.get("key") == current_key else " "
        label = opt.get("label", opt.get("key", "?"))
        extra = opt.get("detail", "")
        say(f"  {mark} [{idx:>2}] {label}" + (f"   {paint(extra, DIM)}" if extra else ""))
    if allow_cancel:
        say("       [ 0] keep current")
    while True:
        raw = ask("number", "0" if allow_cancel else "1")
        if not raw.isdigit():
            continue
        n = int(raw)
        if n == 0 and allow_cancel:
            return None
        if 1 <= n <= len(options):
            return options[n - 1]


def llm_options(cfg: dict) -> list[dict]:
    options = []
    strata_dir = cfg.get("strata_dir")
    if strata_dir and _resolve(strata_dir).is_dir():
        options.append({
            "key": "strata",
            "label": "Strata engine — Qwen3.8-Flash-Next (external, port "
                     f"{cfg.get('strata_port', 8080)})",
            "detail": "no llama.cpp",
            "engine": "strata",
        })
    for item in discover_llm(cfg):
        short = item["short"] or item["path"].stem
        detail = f"{human_size(item['size'])}"
        if item["profile"]:
            detail += f" · profile {item['profile']}"
        if item["current"]:
            detail += " · current"
        options.append({
            "key": str(item["path"]),
            "label": f"{item['path'].name}",
            "detail": detail,
            "engine": "llama",
            "path": str(item["path"]),
            "short": item["short"] or "",
        })
    return options


def comfy_options(cfg: dict) -> list[dict]:
    options = []
    for item in discover_comfy(cfg):
        detail = human_size(item["size"]) + (" · checkpoint (SDXL pipeline)" if item["kind"] == "checkpoint"
                                            else " · diffusion model (needs a matching workflow)")
        options.append({"key": item["path"].name, "label": item["path"].name, "detail": detail})
    return options


def voice_options(cfg: dict) -> list[dict]:
    return [
        {
            "key": v["key"],
            "label": f"{v['ckpt'].name} + {v['pth'].name}",
            "detail": f"{human_size(v['ckpt'].stat().st_size)} · {v['key']}"
                      + (" · current" if v.get("current") else ""),
        }
        for v in discover_voices(cfg)
    ]


def port_selection(cfg: dict, current: dict, advanced: bool) -> dict:
    section("ports")
    basic = {"llama_port", "strata_port", "comfyui_port", "tts_port"}
    result = dict(current)
    for key, default, label in PORT_KEYS:
        if not advanced and key not in basic:
            continue
        value = current.get(key, cfg.get(key, default))
        say(f"  {label}")
        raw = ask(f"{key}", str(value))
        if not raw.isdigit() or not (1 <= int(raw) <= 65535):
            warn(f"invalid port {raw!r} — keeping {value}")
            result[key] = value
            continue
        result[key] = int(raw)
        if result[key] != int(value) and port_busy_any(result[key]):
            warn(f"port {result[key]} is already in use — pick another if startup fails")
    used = {}
    for key, value in result.items():
        if value in used:
            warn(f"{key} and {used[value]} share port {value}")
        used[value] = key
    return result


# ── selection default / state ────────────────────────────────────────────
def default_selection(cfg: dict) -> dict:
    engine = (cfg.get("llm_engine") or "llama").lower()
    if engine not in ("llama", "strata"):
        engine = "llama"
    voice_key = ""
    saved_voice = current_voice(cfg) or {}
    if saved_voice.get("ckpt"):
        voice_key = _voice_prefix(saved_voice["ckpt"])
    return {
        "engine": engine,
        "llm": str(_resolve(cfg.get("llama_model"))) if cfg.get("llama_model") else "",
        "llm_short": "",
        "comfy": (cfg.get("comfyui_default_checkpoint") or "").strip(),
        "voice": voice_key,
        "ports": {k: int(cfg.get(k, d) or d) for k, d, _ in PORT_KEYS},
    }


def load_state() -> dict:
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(selection: dict) -> None:
    data = dict(selection)
    data["saved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        STATE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        warn(f"could not save {STATE_PATH.name}: {exc}")


def merge_selection(base: dict, state: dict) -> dict:
    merged = json.loads(json.dumps(base))
    for key in ("engine", "llm", "llm_short", "comfy", "voice"):
        if state.get(key):
            merged[key] = state[key]
    ports = state.get("ports") or {}
    for key, value in ports.items():
        try:
            merged["ports"][key] = int(value)
        except (TypeError, ValueError):
            pass
    return merged


# ── voice file ───────────────────────────────────────────────────────────
def apply_voice(cfg: dict, key: str, dry_run: bool = False) -> str | None:
    voices = {v["key"]: v for v in discover_voices(cfg)}
    voice = voices.get(key)
    if not voice:
        return None
    folder = sovits_weights_root(cfg)
    target = folder / "weight.json"
    payload = {"GPT": {"v2": voice["ckpt"].name}, "SoVITS": {"v2": voice["pth"].name}}
    old = None
    if target.is_file():
        try:
            old = json.loads(target.read_text(encoding="utf-8"))
        except ValueError:
            old = None
    if old == payload:
        return None
    if dry_run:
        return f"weight.json: {payload['GPT']['v2']} + {payload['SoVITS']['v2']}"
    if target.is_file():
        stamp = time.strftime("%Y%m%d-%H%M%S")
        target.with_name(f"weight.json.bak-starthere-{stamp}").write_text(
            target.read_text(encoding="utf-8"), encoding="utf-8"
        )
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    overrides = sorted(p.name for p in folder.glob("weight_*.json"))
    if overrides:
        warn(f"{', '.join(overrides)} also exists and takes priority for its character")
    return f"weight.json: {payload['GPT']['v2']} + {payload['SoVITS']['v2']}"


# ── startup pieces ───────────────────────────────────────────────────────
class Result:
    def __init__(self, name: str, ok_: bool, message: str = ""):
        self.name = name
        self.ok = ok_
        self.message = message

    def __str__(self) -> str:
        # the caller prints an OK/FAIL marker in front of this line
        return f"{self.name}: {self.message}" if self.message else self.name


def start_strata(cfg: dict, selection: dict) -> Result:
    port = int(selection["ports"].get("strata_port", cfg.get("strata_port", 8080)))
    if port_open(port):
        return Result("Strata", True, f"already running on {port}")
    strata_dir = _resolve(cfg.get("strata_dir") or "")
    config_name = cfg.get("strata_config") or "strata-iq3_s.json"
    strata_cfg = strata_dir / config_name
    if not strata_dir.is_dir():
        return Result("Strata", False, f"strata_dir not found: {strata_dir}")
    server = strata_dir / "serve" / "server.py"
    venv = strata_dir / ".venv" / ("Scripts/python.exe" if IS_WIN else "bin/python")
    py = str(venv) if venv.is_file() else sys.executable
    if not server.is_file():
        return Result("Strata", False, f"serve/server.py not found under {strata_dir}")
    cmd = [py, str(server), "--engine", "strata", "--config", str(strata_cfg), "--port", str(port)]
    spawn("strata", cmd, strata_dir, LOG_DIR / "strata.log")
    say("  Strata starting (model load can take minutes) ...", end="", flush=True)
    if wait_for(lambda: http_ok(f"http://127.0.0.1:{port}/health"), 240, "Strata"):
        return Result("Strata", True, f"http://127.0.0.1:{port}")
    return Result("Strata", False, f"no /health on {port} — see {LOG_DIR / 'strata.log'}")


def start_daemon(cfg: dict, selection: dict, wait_llm: int, no_services: bool = False) -> list[Result]:
    results: list[Result] = []
    if port_open(DASHBOARD_PORT):
        results.append(Result("daemon", True, f"already running on {DASHBOARD_PORT}"))
    else:
        cmd = [sys.executable, str(ROOT / "shiki_daemon.py")]
        if no_services:
            cmd.append("--no-auto-start")
        elif selection["engine"] == "strata":
            cmd.append("--no-llama")
        proc = spawn("daemon", cmd, ROOT, LOG_DIR / "daemon.log")
        say("  daemon starting (dashboard + webchat + proxy chain) ...", end="", flush=True)
        if not wait_for(lambda: http_ok(f"http://127.0.0.1:{DASHBOARD_PORT}/api/status"), 60, "daemon"):
            code = proc.poll()
            hint = f"exit {code} — see {LOG_DIR / 'daemon.log'}" if code is not None else "timed out"
            say(tail(LOG_DIR / "daemon.log", 12))
            return [Result("daemon", False, hint)]
        results.append(Result("daemon", True, f"http://127.0.0.1:{DASHBOARD_PORT} (pid {proc.pid})"))

    if no_services:
        results.append(Result("services", True, "skipped (--no-services)"))
        return results
    if selection["engine"] == "strata":
        port = int(selection["ports"].get("strata_port", 8080))
        results.append(Result("LLM", port_open(port), f"Strata :{port}"))
    else:
        port = int(selection["ports"].get("llama_port", 9931))
        if wait_llm > 0:
            say("  llama.cpp loading the model ...", end="", flush=True)
            wait_for(lambda: port_open(port), wait_llm, "llama")
        results.append(Result("LLM", port_open(port), f"llama.cpp :{port}"))
    return results


def start_comfy(cfg: dict, selection: dict) -> Result:
    port = int(selection["ports"].get("comfyui_port", cfg.get("comfyui_port", 8188)))
    if http_ok(f"http://127.0.0.1:{port}/system_stats"):
        return Result("ComfyUI", True, f"already running on {port}")
    root = _resolve(cfg.get("comfyui_root") or (ROOT / "deps" / "ComfyUI"))
    py = _resolve(cfg.get("comfyui_python") or sys.executable)
    main = root / "main.py"
    if not main.is_file():
        return Result("ComfyUI", False, f"main.py not found: {main} (config.yaml comfyui_root)")
    if not Path(py).is_file():
        return Result("ComfyUI", False, f"comfyui_python not found: {py}")
    spawn("comfyui", [py, str(main), "--port", str(port)], root, LOG_DIR / "comfyui.log")
    say("  ComfyUI starting (imports torch, slow first time) ...", end="", flush=True)
    if wait_for(lambda: http_ok(f"http://127.0.0.1:{port}/system_stats", 2.5), 240, "ComfyUI"):
        return Result("ComfyUI", True, f"http://127.0.0.1:{port}")
    return Result(
        "ComfyUI", False,
        f"not up on {port} — the resident LLM may be holding VRAM; image generation "
        f"runs through the Task Scheduler handoff anyway (see {LOG_DIR / 'comfyui.log'})",
    )


def start_sovits(cfg: dict, selection: dict) -> Result:
    port = int(selection["ports"].get("tts_port", cfg.get("tts_port", 9880)))
    if port_open(port):
        return Result("SoVITS", True, f"already running on {port}")
    root = _resolve(cfg.get("sovits_weights_dir") or (ROOT / "skills" / "sovits"))
    py = _resolve(cfg.get("sovits_python") or sys.executable)
    api = root / "api_v2.py"
    if not api.is_file():
        return Result("SoVITS", False, f"api_v2.py not found under {root}")
    if not Path(py).is_file():
        return Result("SoVITS", False, f"sovits_python not found: {py}")
    spawn("sovits", [py, str(api), "-a", "127.0.0.1", "-p", str(port)], root, LOG_DIR / "sovits.log")
    say("  GPT-SoVITS API starting ...", end="", flush=True)
    if wait_for(lambda: port_open(port), 240, "SoVITS"):
        return Result("SoVITS", True, f"http://127.0.0.1:{port}/docs (weights load on first synthesis)")
    return Result("SoVITS", False, f"not up on {port} — see {LOG_DIR / 'sovits.log'}")


# ── status / stop ────────────────────────────────────────────────────────
def status_rows(cfg: dict, selection: dict) -> list[tuple[str, str, str, bool]]:
    ports = selection["ports"]
    llm_port = ports.get("strata_port" if selection["engine"] == "strata" else "llama_port")
    rows = [
        ("WebChat", f"http://127.0.0.1:{WEBCHAT_PORT}", "tcp", WEBCHAT_PORT),
        ("Dashboard", f"http://127.0.0.1:{DASHBOARD_PORT}/api/status", "http", DASHBOARD_PORT),
        ("LLM (" + ("Strata" if selection["engine"] == "strata" else "llama.cpp") + ")",
         f"http://127.0.0.1:{llm_port}/health", "http", llm_port),
        ("ComfyUI", f"http://127.0.0.1:{ports.get('comfyui_port')}/system_stats", "http", ports.get("comfyui_port")),
        ("GPT-SoVITS", f"http://127.0.0.1:{ports.get('tts_port')}/docs", "tcp", ports.get("tts_port")),
        ("Embedding", f"http://127.0.0.1:{ports.get('embedding_port')}/health", "http", ports.get("embedding_port")),
        ("Headroom proxy", f"127.0.0.1:{ports.get('headroom_port')}", "tcp", ports.get("headroom_port")),
        ("Live2D bridge", f"127.0.0.1:{ports.get('live2d_port')}", "tcp", ports.get("live2d_port")),
        ("Artemis bridge", f"127.0.0.1:{ports.get('artemis_bridge_port')}", "tcp", ports.get("artemis_bridge_port")),
        ("OpenClaw gateway", f"127.0.0.1:{ports.get('gateway_port')}", "tcp", ports.get("gateway_port")),
        ("Task board", f"127.0.0.1:{ports.get('task_board_port')}", "tcp", ports.get("task_board_port")),
        ("Llama debugger", f"127.0.0.1:{ports.get('llama_debugger_port')}", "tcp", ports.get("llama_debugger_port")),
    ]
    out = []
    for name, target, kind, port in rows:
        alive = http_ok(target, 1.5) if kind == "http" else port_open(port)
        out.append((name, target, kind, alive))
    return out


def print_status(cfg: dict, selection: dict) -> int:
    section("status")
    rows = status_rows(cfg, selection)
    for name, target, _kind, alive in rows:
        mark = paint(" OK ", GREEN) if alive else paint("DOWN", RED)
        say(f"  [{mark}] {name:<22} {paint(target, DIM)}")
    say("")
    say("  selection")
    say(f"    engine : {selection['engine']}")
    if selection["engine"] == "llama":
        say(f"    LLM    : {selection.get('llm') or '(not set)'}")
    say(f"    ComfyUI: {selection.get('comfy') or '(default)'}")
    say(f"    voice  : {selection.get('voice') or '(current weight.json)'}")
    return 0 if any(alive for _n, _t, _k, alive in rows) else 1


def kill_port(port: int, label: str) -> None:
    if not port_open(port):
        return
    info(f"stopping {label} on port {port} ...")
    try:
        if IS_WIN:
            out = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, timeout=15,
                encoding="utf-8", errors="replace",
            ).stdout
            pids = {
                line.split()[-1]
                for line in out.splitlines()
                if f":{port}" in line and "LISTENING" in line.upper() and line.split()
            }
            for pid in pids:
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, timeout=15)
        else:
            for cmd in (["lsof", "-ti", f"tcp:{port}"], ["fuser", f"{port}/tcp"]):
                try:
                    out = subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout
                except FileNotFoundError:
                    continue
                for pid in re.findall(r"\d+", out):
                    subprocess.run(["kill", "-9", pid], capture_output=True, timeout=10)
                break
    except (OSError, subprocess.SubprocessError) as exc:
        warn(f"could not stop {label}: {exc}")


def stop_all(cfg: dict, selection: dict) -> int:
    section("stop")
    shutdown = ROOT / "shutdown_all.py"
    if shutdown.is_file():
        info("running shutdown_all.py ...")
        code = subprocess.call([sys.executable, str(shutdown), "--quiet"], cwd=str(ROOT))
        if code not in (0, None):
            warn(f"shutdown_all.py exited with {code}")
    else:
        warn("shutdown_all.py not found")
    kill_port(int(selection["ports"].get("comfyui_port", 8188)), "ComfyUI")
    kill_port(int(selection["ports"].get("tts_port", 9880)), "GPT-SoVITS")
    if selection["engine"] == "strata":
        kill_port(int(selection["ports"].get("strata_port", 8080)), "Strata")
    say("")
    info("done — re-run START-HERE to bring everything back up.")
    return 0


# ── llm sanity ───────────────────────────────────────────────────────────
def running_llm_path(port: int) -> str:
    """llama.cpp /props reports the loaded model path (empty if unavailable)."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/props", timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        return str(data.get("model_path") or data.get("model") or "")
    except (urllib.error.URLError, OSError, ValueError):
        return ""


def check_llm_mismatch(selection: dict) -> None:
    if selection["engine"] != "llama" or not selection.get("llm"):
        return
    port = int(selection["ports"].get("llama_port", 9931))
    if not port_open(port):
        return
    loaded = running_llm_path(port)
    if loaded and Path(loaded).name != Path(selection["llm"]).name:
        warn("the LLM already running on :%d has a different model loaded:" % port)
        info(f"running : {loaded}")
        info(f"selected: {selection['llm']}")
        info("restart the stack to apply the new model:  START-HERE.bat --stop  then start again")


# ── interactive flow ─────────────────────────────────────────────────────
def interactive(cfg: dict, selection: dict) -> dict:
    while True:
        section("current selection")
        llm_label = (
            "Strata engine (Qwen3.8-Flash-Next)"
            if selection["engine"] == "strata"
            else Path(selection.get("llm") or "?").name
        )
        say(f"  [1] LLM engine/model : {llm_label}")
        say(f"  [2] ComfyUI model    : {selection.get('comfy') or '(config default)'}")
        say(f"  [3] SoVITS voice     : {selection.get('voice') or '(current weight.json)'}")
        say("  [4] ports            : " + " · ".join(
            f"{k.replace('_port', '')} {selection['ports'].get(k)}" for k, _d, _l in PORT_KEYS[:6]
        ))
        say("")
        say("  [Enter] start everything    [s] status    [x] stop all    [q] quit")
        try:
            choice = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            say("")
            return selection
        if choice in ("", "5", "start", "go"):
            return selection
        if choice in ("q", "quit", "exit"):
            raise SystemExit(0)
        if choice in ("s", "status"):
            print_status(cfg, selection)
            continue
        if choice in ("x", "stop"):
            stop_all(cfg, selection)
            continue
        if choice == "1":
            options = llm_options(cfg)
            if not options:
                warn("no .gguf found — check llama_model / llama_model_map in config.yaml")
                continue
            current = "strata" if selection["engine"] == "strata" else selection.get("llm")
            picked = choose("choose the LLM engine / model", options, current)
            if picked:
                selection["engine"] = picked["engine"]
                if picked["engine"] == "llama":
                    selection["llm"] = picked["path"]
                    selection["llm_short"] = picked.get("short", "")
                if picked.get("detail"):
                    info(f"selected: {picked['detail']}")
        elif choice == "2":
            options = comfy_options(cfg)
            if not options:
                warn("no ComfyUI model found — check comfyui_checkpoints_dir / comfyui_root")
                continue
            picked = choose("choose the ComfyUI model", options, selection.get("comfy"))
            if picked:
                selection["comfy"] = picked["key"]
                if "diffusion model" in picked.get("detail", ""):
                    warn("this is a diffusion model: comfyui_call.py currently runs the SDXL pipeline")
        elif choice == "3":
            options = voice_options(cfg)
            if not options:
                warn(f"no SoVITS ckpt/pth pair under {sovits_weights_root(cfg)}")
                continue
            picked = choose("choose the SoVITS voice (ckpt + pth)", options, selection.get("voice"))
            if picked:
                selection["voice"] = picked["key"]
        elif choice == "4":
            advanced = ask("show every service port? (y/N)", "n").lower().startswith("y")
            selection["ports"] = port_selection(cfg, selection["ports"], advanced)
        else:
            warn("unknown choice")


def parse_cli_selection(args, cfg: dict, base: dict) -> dict:
    selection = dict(base)
    if args.engine:
        selection["engine"] = args.engine
    if args.llm:
        if args.llm.lower() == "strata":
            selection["engine"] = "strata"
        else:
            want = args.llm
            match = None
            for item in discover_llm(cfg):
                if want.lower() in (item["path"].name.lower(), item["short"].lower(), str(item["path"]).lower()):
                    match = item
                    break
            if not match:
                candidate = _resolve(want)
                if candidate.is_file():
                    match = {"path": candidate, "short": "", "size": candidate.stat().st_size}
            if not match:
                raise SystemExit(f"--llm: no model matched {want!r} (try --list)")
            selection["engine"] = "llama"
            selection["llm"] = str(match["path"])
            selection["llm_short"] = match.get("short", "")
    if args.comfy:
        names = {o["key"] for o in comfy_options(cfg)}
        if args.comfy not in names:
            raise SystemExit(f"--comfy: {args.comfy!r} not found (try --list)")
        selection["comfy"] = args.comfy
    if args.voice:
        keys = {o["key"] for o in voice_options(cfg)}
        if args.voice not in keys:
            raise SystemExit(f"--voice: {args.voice!r} not found (try --list); available: {', '.join(sorted(keys))}")
        selection["voice"] = args.voice
    for item in args.port or []:
        if "=" not in item:
            raise SystemExit(f"--port expects key=value, got {item!r}")
        key, raw = item.split("=", 1)
        key = key if key.endswith("_port") else key + "_port"
        if key not in {k for k, _d, _l in PORT_KEYS}:
            raise SystemExit(f"--port: unknown key {key!r}")
        if not raw.isdigit() or not (1 <= int(raw) <= 65535):
            raise SystemExit(f"--port: invalid port {raw!r}")
        selection["ports"][key] = int(raw)
    return selection


def warn_port_notes(selection: dict) -> None:
    """Ports other components still assume by default."""
    port = int(selection["ports"].get("tts_port", 9880))
    if port != 9880:
        warn(f"GPT-SoVITS on {port}: the desktop pet / OpenClaw TTS config may still "
             f"point at 9880 — update its api_url if the voice is silent")


def validate_selection(cfg: dict, selection: dict) -> dict:
    """Drop references to files that disappeared since the state was saved."""
    if selection["engine"] == "llama":
        llm = selection.get("llm") or ""
        if not llm or not Path(llm).is_file():
            fallback = cfg.get("llama_model") or ""
            if fallback and _resolve(fallback).is_file():
                warn(f"saved LLM model is gone — falling back to {Path(fallback).name}")
                selection["llm"] = str(_resolve(fallback))
            else:
                warn("no usable .gguf selected — pick one with [1] in the menu")
                selection["llm"] = ""
    if selection.get("comfy"):
        names = {o["key"] for o in comfy_options(cfg)}
        if selection["comfy"] not in names:
            warn(f"ComfyUI model {selection['comfy']!r} not found — keeping the config default")
            selection["comfy"] = ""
    if selection.get("voice"):
        keys = {o["key"] for o in voice_options(cfg)}
        if selection["voice"] not in keys:
            warn(f"SoVITS voice {selection['voice']!r} not found — keeping weight.json as-is")
            selection["voice"] = ""
    for key, default, _label in PORT_KEYS:
        try:
            value = int(selection["ports"].get(key, default))
        except (TypeError, ValueError):
            value = default
        selection["ports"][key] = value if 1 <= value <= 65535 else default
    return selection


def print_listing(cfg: dict) -> int:
    section("LLM models")
    for opt in llm_options(cfg):
        say(f"  {opt['label']:<70} {opt.get('detail', '')}")
    section("ComfyUI models")
    for opt in comfy_options(cfg):
        say(f"  {opt['label']:<70} {opt.get('detail', '')}")
    section("SoVITS voices")
    for opt in voice_options(cfg):
        say(f"  {opt['label']:<70} {opt.get('detail', '')}")
    return 0


# ── main ─────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="START-HERE",
        description="Select LLM / ComfyUI / SoVITS models and ports, then start the whole stack.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  START-HERE.bat                          menu, then start\n"
            "  START-HERE.bat --llm hermes3.6-35b-q4   pick a model and start\n"
            "  START-HERE.bat --engine strata          use the Strata engine only\n"
            "  START-HERE.bat --port comfyui_port=8189 --no-tts\n"
            "  START-HERE.bat --status | --stop | --list\n"
        ),
    )
    parser.add_argument("--llm", help="LLM: .gguf path, short id from llama_model_map, or 'strata'")
    parser.add_argument("--engine", choices=["llama", "strata"], help="LLM backend")
    parser.add_argument("--comfy", help="ComfyUI checkpoint/diffusion model file name")
    parser.add_argument("--voice", help="SoVITS voice prefix (e.g. atori, Sakura)")
    parser.add_argument("--port", action="append", metavar="KEY=PORT",
                        help="override a port, e.g. --port comfyui_port=8189 (repeatable)")
    parser.add_argument("--menu", action="store_true", help="always show the interactive menu")
    parser.add_argument("--yes", "-y", action="store_true", help="non-interactive start")
    parser.add_argument("--dry-run", action="store_true", help="show what would change; start nothing")
    parser.add_argument("--list", action="store_true", help="list available models/voices and exit")
    parser.add_argument("--status", action="store_true", help="show service status and exit")
    parser.add_argument("--stop", action="store_true", help="stop the whole stack")
    parser.add_argument("--reset", action="store_true", help="forget the saved selection")
    parser.add_argument("--no-strata", action="store_true", help="do not start Strata")
    parser.add_argument("--no-comfy", action="store_true", help="do not start ComfyUI")
    parser.add_argument("--no-tts", action="store_true", help="do not start GPT-SoVITS")
    parser.add_argument("--no-services", action="store_true",
                        help="only the dashboard + web-chat (no llama/proxies/ComfyUI/TTS)")
    parser.add_argument("--no-browser", action="store_true", help="do not open the web-chat page")
    parser.add_argument("--wait-llm", type=int, default=240, metavar="SEC",
                        help="how long to wait for llama.cpp to load (default 240)")
    return parser


def main(argv: list[str]) -> int:
    _init_console()
    ensure_yaml()
    args = build_parser().parse_args(argv)
    cfg = load_cfg()

    selection = merge_selection(default_selection(cfg), load_state())

    if args.list:
        return print_listing(cfg)

    if args.reset:
        STATE_PATH.unlink(missing_ok=True)
        info(f"removed {STATE_PATH.name}")

    selection = parse_cli_selection(args, cfg, selection)

    if args.stop:
        save_state(selection)
        return stop_all(cfg, selection)

    if args.status:
        print_status(cfg, selection)
        return 0

    interactive_requested = args.menu or (not args.yes and sys.stdin.isatty()
                                          and not any([args.llm, args.comfy, args.voice, args.engine]))

    say("")
    say(paint("  AI Girlfriend — START HERE", BOLD))
    info(f"repo: {ROOT}")

    if interactive_requested:
        selection = interactive(cfg, selection)

    selection = validate_selection(cfg, selection)
    warn_port_notes(selection)

    # 1. persist the selection
    section("apply selection")
    notes = apply_config(selection, dry_run=args.dry_run)
    if selection.get("voice"):
        voice_note = apply_voice(cfg, selection["voice"], dry_run=args.dry_run)
        if voice_note:
            notes.append(voice_note)
    if notes:
        for note in notes:
            info(note)
        if args.dry_run:
            warn("dry run — config.yaml was not written, nothing was started")
            return 0
        ok(f"config.yaml updated (backup kept next to it)")
    else:
        info("nothing to change")
    save_state(selection)

    # 2. start the stack
    section("start")
    results: list[Result] = []
    only_ui = args.no_services
    if selection["engine"] == "strata" and not args.no_strata and not only_ui:
        results.append(start_strata(cfg, selection))
    results.extend(start_daemon(cfg, selection, args.wait_llm, no_services=only_ui))
    if only_ui:
        info("llama / proxies / ComfyUI / SoVITS skipped (--no-services)")
    elif args.no_comfy:
        info("ComfyUI skipped (--no-comfy)")
    else:
        results.append(start_comfy(cfg, selection))
    if only_ui or args.no_tts:
        if not only_ui:
            info("GPT-SoVITS skipped (--no-tts)")
    else:
        results.append(start_sovits(cfg, selection))

    check_llm_mismatch(selection)

    # 3. report
    print_status(cfg, selection)
    for res in results:
        (ok if res.ok else fail)(str(res))
    if not args.no_browser and not args.dry_run:
        try:
            webbrowser.open(f"http://127.0.0.1:{WEBCHAT_PORT}")
        except Exception:
            pass
    failures = [r for r in results if not r.ok]
    say("")
    if failures:
        info(f"{len(failures)} service(s) not up — logs: {LOG_DIR}")
        return 0 if all(r.name in ("ComfyUI", "GPT-SoVITS", "Strata") for r in failures) else 1
    info("all services are up.  stop with:  START-HERE --stop")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        say("")
        raise SystemExit(130)
