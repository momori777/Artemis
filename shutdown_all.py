#!/usr/bin/env python3
"""
Artemis Graceful Shutdown
========================
Closes ALL project processes: llama-server, Live2D bridge, ComfyUI,
OpenClaw Gateway, Artemis Bridge, Task Board, WebChat, Sakura Desktop Pet,
Embedding Server, and runs cleanup_orphans.ps1.

Usage:
    python shutdown_all.py           # full output
    python shutdown_all.py --quiet   # minimal output

Exit codes:
    0 = all clean
    1 = some processes failed to stop
"""

import sys
import os
import subprocess
import socket
import time
import argparse

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = os.path.dirname(os.path.abspath(__file__))


# ---- Helpers ----

def port_open(host, port, timeout=1):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False
    finally:
        s.close()


def kill_by_port(port, name, wait_sec=3):
    """Kill the process owning a local port via netstat + taskkill (no admin needed)."""
    if not port_open("127.0.0.1", port):
        print(f"[shutdown] {name}: not running")
        return True

    print(f"[shutdown] {name}: stopping (port {port})...")

    # Find PID via netstat (works without admin)
    pid = _get_pid_by_port(port)
    if pid:
        _force_kill_pid(pid, name)
    else:
        # Fallback: taskkill by port
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | "
             "ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"],
            capture_output=True, text=True, timeout=8
        )

    for i in range(wait_sec * 2):
        time.sleep(0.5)
        if not port_open("127.0.0.1", port):
            print(f"[shutdown] {name}: stopped ({(i+1)*0.5:.0f}s)")
            return True

    # Aggressive: try again with taskkill
    pid = _get_pid_by_port(port)
    if pid:
        _force_kill_pid(pid, name, force=True)
        time.sleep(1)
        if not port_open("127.0.0.1", port):
            print(f"[shutdown] {name}: force killed")
            return True

    print(f"[shutdown] {name}: STILL RUNNING — manual kill needed")
    return False


def _get_pid_by_port(port):
    """Get PID listening on port using netstat (no admin required)."""
    try:
        result = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True, timeout=5,
            encoding="utf-8", errors="replace"
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                if pid.isdigit():
                    return int(pid)
    except Exception:
        pass
    return None


def _force_kill_pid(pid, name, force=False):
    # Always use /f — most services don't respond to graceful SIGTERM
    try:
        subprocess.run(
            ["taskkill", "/f", "/pid", str(pid)],
            capture_output=True, timeout=5
        )
    except Exception:
        pass


# ---- Service-specific killers ----

def kill_llama():
    if not port_open("127.0.0.1", 8080):
        print("[shutdown] llama-server: not running")
        return True
    print("[shutdown] llama-server: stopping...")
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:8080/shutdown", timeout=3)
        print("[shutdown] llama-server: /shutdown sent")
    except Exception:
        print("[shutdown] llama-server: HTTP shutdown failed, force killing")

    for i in range(15):
        time.sleep(0.5)
        if not port_open("127.0.0.1", 8080):
            print(f"[shutdown] llama-server: stopped ({i*0.5:.0f}s)")
            return True

    subprocess.run(["taskkill", "/f", "/im", "llama-server.exe"], capture_output=True)
    time.sleep(1)
    ok = not port_open("127.0.0.1", 8080)
    if ok:
        print("[shutdown] llama-server: killed")
    else:
        print("[shutdown] llama-server: STILL RUNNING — manual kill needed")
    return ok


def kill_live2d():
    return kill_by_port(19200, "live2d bridge", wait_sec=3)


def kill_comfyui():
    if not port_open("127.0.0.1", 8188):
        print("[shutdown] ComfyUI: not running")
        return True
    print("[shutdown] ComfyUI: stopping...")
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -match 'comfyui|ComfyUI|main\\.py' } | "
             "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"],
            capture_output=True, text=True, timeout=10
        )
    except Exception:
        pass
    for i in range(15):
        time.sleep(0.5)
        if not port_open("127.0.0.1", 8188):
            print(f"[shutdown] ComfyUI: stopped ({i*0.5:.0f}s)")
            return True
    print("[shutdown] ComfyUI: STILL RUNNING — manual kill needed")
    return False


def kill_gateway():
    cli = _find_openclaw()
    if cli:
        try:
            result = subprocess.run(
                [cli, "gateway", "stop"],
                capture_output=True, text=True, timeout=30
            )
            out = (result.stdout.strip() + " " + result.stderr.strip()).strip()
            print(f"[shutdown] gateway: {out}" if out else "[shutdown] gateway: stopped")
            return True
        except subprocess.TimeoutExpired:
            print("[shutdown] gateway: TIMEOUT")
            return False
        except Exception as e:
            print(f"[shutdown] gateway: error: {e}")
            return False
    else:
        print("[shutdown] gateway: CLI not found, trying process kill...")
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process node -ErrorAction SilentlyContinue | "
             "Where-Object { $_.CommandLine -match 'gateway' } | Stop-Process -Force"],
            capture_output=True, timeout=10
        )
        return True
    except Exception:
        return False


def kill_webchat():
    return kill_by_port(19270, "webchat", wait_sec=3)


def kill_bridge():
    return kill_by_port(19250, "artemis bridge", wait_sec=3)


def kill_taskboard():
    return kill_by_port(19280, "task board", wait_sec=3)


def kill_embedding_server():
    return kill_by_port(9999, "embedding server", wait_sec=3)


def kill_sakura():
    """Stop Sakura Desktop Pet (PySide6 GUI)."""
    pidFile = os.path.join(WORKSPACE, "skills", "sakura", ".sakura_pid.txt")
    if os.path.exists(pidFile):
        try:
            with open(pidFile) as f:
                pid = int(f.read().strip())
            import signal
            os.kill(pid, signal.SIGTERM)
            print(f"[shutdown] Sakura: sent SIGTERM to PID={pid}")
            time.sleep(1)
            try:
                os.kill(pid, 0)
                subprocess.run(["taskkill", "/f", "/pid", str(pid)], capture_output=True)
                print(f"[shutdown] Sakura: force killed")
            except OSError:
                print(f"[shutdown] Sakura: stopped")
            os.remove(pidFile)
            return True
        except Exception as e:
            print(f"[shutdown] Sakura: PID file error: {e}")

    # Method 2: taskkill known python processes with sakura in args (faster)
    try:
        result = subprocess.run(
            ["wmic", "process", "where", "name='python.exe'", "get", "processid,commandline"],
            capture_output=True, text=True, timeout=5,
            encoding="utf-8", errors="replace"
        )
        pids_to_kill = []
        for line in result.stdout.splitlines():
            if "sakura" in line.lower() or "Sakura" in line:
                parts = line.strip().split()
                if parts:
                    maybe_pid = parts[-1]
                    if maybe_pid.isdigit():
                        pids_to_kill.append(maybe_pid)
        if pids_to_kill:
            for p in pids_to_kill:
                subprocess.run(["taskkill", "/f", "/pid", p], capture_output=True)
            print(f"[shutdown] Sakura: killed {len(pids_to_kill)} process(es)")
            return True
    except Exception:
        pass

    print("[shutdown] Sakura: not running")
    return True


def _find_openclaw():
    candidates = [
        os.path.expandvars(r"%APPDATA%\npm\openclaw.cmd"),
        os.path.expandvars(r"%ProgramFiles%\nodejs\openclaw.cmd"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    try:
        r = subprocess.run(["where", "openclaw"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return None


def run_cleanup():
    ps1 = os.path.join(WORKSPACE, "skills", "cleanup_orphans.ps1")
    if not os.path.exists(ps1):
        print("[shutdown] cleanup_orphans: script not found, skipping")
        return True
    print("[shutdown] cleanup_orphans: running...")
    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-NoProfile",
             "-File", ps1, "-MaxAgeSeconds", "0"],
            capture_output=True, text=True, timeout=60,
            encoding="utf-8", errors="replace"
        )
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        for line in lines[-6:]:
            print(f"  {line}")
        print("[shutdown] cleanup_orphans: done")
        return True
    except subprocess.TimeoutExpired:
        print("[shutdown] cleanup_orphans: TIMEOUT")
        return False
    except Exception as e:
        print(f"[shutdown] cleanup_orphans: error: {e}")
        return False


# ---- Main ----

def main():
    parser = argparse.ArgumentParser(description="Artemis Graceful Shutdown")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if not args.quiet:
        print("=" * 50)
        print("  Artemis Shutdown")
        print("=" * 50)
        print()

    results = {}

    # Order: thread-level (daemon-managed) first, then standalone processes
    results["webchat"] = kill_webchat()
    results["taskboard"] = kill_taskboard()
    results["bridge"] = kill_bridge()
    results["sakura"] = kill_sakura()
    results["live2d"] = kill_live2d()
    results["embedding"] = kill_embedding_server()
    results["llama"] = kill_llama()
    results["comfyui"] = kill_comfyui()
    results["gateway"] = kill_gateway()
    results["cleanup"] = run_cleanup()

    print()
    all_ok = all(results.values())

    if all_ok:
        print("[shutdown] All clean. Goodbye!")
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"[shutdown] WARNING: failed to stop: {', '.join(failed)}")
        print("[shutdown] You may need to manually kill remaining processes.")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
