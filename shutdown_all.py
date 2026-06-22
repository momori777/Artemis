#!/usr/bin/env python3
"""
Artemis Graceful Shutdown
=======================
Closes ALL project processes: llama-server, Live2D bridge, ComfyUI,
OpenClaw Gateway, and runs cleanup_orphans.ps1 to kill stuck child
processes + stale locks.

Usage:
    python shutdown_all.py

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

# Force UTF-8 on Windows to avoid CJK garbled output in console
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


def run_ps1(script_path, args=""):
    """Run a PowerShell script and return (ok, output)."""
    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-NoProfile",
             "-File", script_path] + (args.split() if args else []),
            capture_output=True, text=True, timeout=120
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)


# ---- Kill functions ----

def kill_llama():
    """Stop llama-server on port 8080 with graceful shutdown first."""
    if not port_open("127.0.0.1", 8080):
        print("[shutdown] llama-server: not running")
        return True

    print("[shutdown] llama-server: stopping...")
    # graceful HTTP shutdown
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:8080/shutdown", timeout=3)
        print("[shutdown] llama-server: /shutdown sent")
    except Exception:
        print("[shutdown] llama-server: HTTP shutdown failed, force killing")

    # wait for port release (graceful path)
    for i in range(15):
        time.sleep(0.5)
        if not port_open("127.0.0.1", 8080):
            print(f"[shutdown] llama-server: stopped ({i*0.5:.0f}s)")
            return True

    # force kill
    print("[shutdown] llama-server: force killing...")
    subprocess.run(["taskkill", "/f", "/im", "llama-server.exe"],
                   capture_output=True)
    time.sleep(1)
    ok = not port_open("127.0.0.1", 8080)
    if ok:
        print("[shutdown] llama-server: killed")
    else:
        print("[shutdown] llama-server: STILL RUNNING — manual kill needed")
    return ok


def kill_live2d():
    """Stop Live2D bridge on port 19200."""
    if not port_open("127.0.0.1", 19200):
        print("[shutdown] live2d bridge: not running")
        return True

    print("[shutdown] live2d bridge: stopping...")

    # Gentle: kill the node process serving port 19200
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "$conn = Get-NetTCPConnection -LocalPort 19200 -ErrorAction SilentlyContinue; "
             "if ($conn) { $conn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }"],
            capture_output=True, text=True, timeout=10
        )
    except Exception:
        pass

    for i in range(10):
        time.sleep(0.3)
        if not port_open("127.0.0.1", 19200):
            print(f"[shutdown] live2d bridge: stopped ({i*0.3:.0f}s)")
            return True

    # Fallback: kill node on that port
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-NetTCPConnection -LocalPort 19200 -ErrorAction SilentlyContinue | "
         "ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"],
        capture_output=True
    )
    time.sleep(1)
    ok = not port_open("127.0.0.1", 19200)
    if ok:
        print("[shutdown] live2d bridge: force killed")
    else:
        print("[shutdown] live2d bridge: STILL RUNNING — manual kill needed")
    return ok


def kill_comfyui():
    """Stop ComfyUI if running."""
    if not port_open("127.0.0.1", 8188):
        print("[shutdown] ComfyUI: not running")
        return True

    print("[shutdown] ComfyUI: stopping...")
    # Kill python processes with comfyui in command line
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


def _find_openclaw():
    """Return full path to openclaw CLI, or None."""
    candidates = [
        os.path.expandvars(r"%APPDATA%\npm\openclaw.cmd"),
        os.path.expandvars(r"%ProgramFiles%\nodejs\openclaw.cmd"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    # Try 'where' as last resort
    try:
        r = subprocess.run(["where", "openclaw"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return None


def kill_gateway():
    """Stop OpenClaw Gateway."""
    cli = _find_openclaw()
    if cli:
        try:
            result = subprocess.run(
                [cli, "gateway", "stop"],
                capture_output=True, text=True, timeout=30
            )
            out = (result.stdout.strip() + " " + result.stderr.strip()).strip()
            if out:
                print(f"[shutdown] gateway: {out}")
            else:
                print("[shutdown] gateway: stopped")
            return True
        except subprocess.TimeoutExpired:
            print("[shutdown] gateway: TIMEOUT")
            return False
        except Exception as e:
            print(f"[shutdown] gateway: error: {e}")
            return False
    else:
        print("[shutdown] gateway: CLI not found, trying process kill...")

    # Fallback: kill node openclaw gateway process directly
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process node -ErrorAction SilentlyContinue | "
             "Where-Object { $_.CommandLine -match 'gateway' } | "
             "Stop-Process -Force"],
            capture_output=True, timeout=10
        )
        print("[shutdown] gateway: force killed")
        return True
    except Exception as e:
        print(f"[shutdown] gateway: error: {e}")
        return False


def kill_webchat():
    """Stop webchat server on port 19270."""
    if not port_open("127.0.0.1", 19270):
        print("[shutdown] webchat: not running")
        return True
    print("[shutdown] webchat: stopping...")
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "$conn = Get-NetTCPConnection -LocalPort 19270 -ErrorAction SilentlyContinue; "
             "if ($conn) { $conn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }"],
            capture_output=True, text=True, timeout=10
        )
    except Exception:
        pass
    for i in range(5):
        time.sleep(0.3)
        if not port_open("127.0.0.1", 19270):
            print(f"[shutdown] webchat: stopped ({i*0.3:.0f}s)")
            return True
    print("[shutdown] webchat: STILL RUNNING - manual kill needed")
    return False

def run_cleanup():
    """Run cleanup_orphans.ps1 to kill stuck children and clean locks."""
    ps1 = os.path.join(WORKSPACE, "skills", "cleanup_orphans.ps1")

    if not os.path.exists(ps1):
        print("[shutdown] cleanup_orphans: script not found, skipping")
        return True

    print("[shutdown] cleanup_orphans: running...")
    try:
        # Use UTF-8 to avoid GBK decode errors
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-NoProfile",
             "-File", ps1, "-MaxAgeSeconds", "0"],
            capture_output=True, text=True, timeout=60,
            encoding="utf-8", errors="replace"
        )
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        for line in lines[-6:]:
            print(f"  {line}")
        if result.returncode != 0:
            print(f"[shutdown] cleanup_orphans: exit code {result.returncode}")
        else:
            print("[shutdown] cleanup_orphans: done")
        return True
    except subprocess.TimeoutExpired:
        print("[shutdown] cleanup_orphans: TIMEOUT")
        return False
    except Exception as e:
        print(f"[shutdown] cleanup_orphans: error: {e}")
        return False


# ---- Main ----

def kill_embedding_server():
    """Stop embedding server on port 9999."""
    if not port_open("127.0.0.1", 9999):
        print("[shutdown] embedding server: not running")
        return True

    print("[shutdown] embedding server: stopping...")
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -match 'embedding_server\\.py' } | "
             "Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=10
        )
    except Exception:
        pass

    for i in range(10):
        time.sleep(0.3)
        if not port_open("127.0.0.1", 9999):
            print(f"[shutdown] embedding server: stopped ({i*0.3:.0f}s)")
            return True

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "$conn = Get-NetTCPConnection -LocalPort 9999 -ErrorAction SilentlyContinue; "
             "if ($conn) { $conn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }"],
            capture_output=True, text=True, timeout=10
        )
    except Exception:
        pass
    time.sleep(1)
    ok = not port_open("127.0.0.1", 9999)
    if ok:
        print("[shutdown] embedding server: force killed")
    else:
        print("[shutdown] embedding server: STILL RUNNING — manual kill needed")
    return ok


def kill_sakura():
    """Stop Sakura Desktop Pet (PySide6 GUI)."""
    pidFile = os.path.join(WORKSPACE, "skills", "sakura", ".sakura_pid.txt")
    
    # Method 1: PID file from start.ps1
    if os.path.exists(pidFile):
        try:
            with open(pidFile) as f:
                pid = int(f.read().strip())
            import signal
            os.kill(pid, signal.SIGTERM)
            print(f"[shutdown] Sakura: sent SIGTERM to PID={pid}")
            time.sleep(1)
            # Verify
            try:
                os.kill(pid, 0)
                # Still alive, force kill
                subprocess.run(["taskkill", "/f", "/pid", str(pid)], capture_output=True)
                print(f"[shutdown] Sakura: force killed PID={pid}")
            except OSError:
                print(f"[shutdown] Sakura: stopped")
            os.remove(pidFile)
            return True
        except Exception as e:
            print(f"[shutdown] Sakura: PID file error: {e}")
    
    # Method 2: find by process name (Python with Sakura/skills/sakura in args)
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -match 'sakura|Sakura|main\\.py' } | "
             "Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=10
        )
        pids = [line.strip() for line in result.stdout.splitlines() if line.strip().isdigit()]
        if pids:
            for pid_str in pids:
                subprocess.run(["taskkill", "/f", "/pid", pid_str], capture_output=True)
            print(f"[shutdown] Sakura: killed {len(pids)} process(es)")
            return True
        else:
            print("[shutdown] Sakura: not running")
            return True
    except Exception as e:
        print(f"[shutdown] Sakura: error: {e}")
        return True  # non-fatal


def main():
    parser = argparse.ArgumentParser(description="Artemis Graceful Shutdown")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress non-essential output")
    args = parser.parse_args()

    if not args.quiet:
        print("=" * 50)
        print("  Artemis Shutdown")
        print("=" * 50)
        print()

    results = {}

    results["llama"] = kill_llama()
    results["live2d"] = kill_live2d()
    results["sakura"] = kill_sakura()
    results["webchat"] = kill_webchat()
    results["embedding"] = kill_embedding_server()
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
