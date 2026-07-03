#!/usr/bin/env python3
"""bridge_watchdog.py — Monitora bridge e reinicia se morrer (PID file)."""
import os, sys, time, subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE_SCRIPT = os.path.join(BASE_DIR, "scripts", "bridge_auto.py")
PID_FILE = os.path.join(BASE_DIR, ".bridge_pid")
WATCHDOG_LOG = os.path.join(BASE_DIR, "bridge_watchdog.log")


def log(msg):
    with open(WATCHDOG_LOG, "a", encoding="utf-8") as f:
        f.write(f"{int(time.time())}|WATCHDOG|{msg}\n")
    print(f"[WATCHDOG] {msg}")


def pid_exists(pid):
    """Verifica se um PID existe (cross-platform)."""
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        SYNCHRONIZE = 0x00100000
        handle = kernel32.OpenProcess(SYNCHRONIZE, 0, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    except Exception:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def get_bridge_pid():
    if not os.path.exists(PID_FILE):
        return None
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        if pid_exists(pid):
            return pid
    except (ValueError, OSError):
        pass
    return None


def is_running():
    return get_bridge_pid() is not None


def start_bridge():
    log("Iniciando bridge...")
    proc = subprocess.Popen(
        ['C:\\Python314\\python.exe', BRIDGE_SCRIPT],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))
    log(f"Bridge iniciado (PID {proc.pid})")


LOCK_FILE = os.path.join(os.path.dirname(PID_FILE), ".watchdog_pid")

def acquire_lock():
    """Garante que so uma instancia do watchdog rode."""
    try:
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, "r") as f:
                old_pid = int(f.read().strip())
            if pid_exists(old_pid):
                log(f"Watchdog ja rodando (PID {old_pid}). Ignorando.")
                return False
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        return True
    except Exception:
        return True  # Se falhar, deixa rodar


def main():
    if "--once" in sys.argv:
        if not is_running():
            log("Bridge NAO esta rodando")
            start_bridge()
        else:
            log(f"Bridge OK (PID {get_bridge_pid()})")
        return

    if not acquire_lock():
        return

    log("Watchdog iniciado")
    if not is_running():
        start_bridge()

    while True:
        try:
            if not is_running():
                log("Bridge MORTO! Reiniciando...")
                start_bridge()
            time.sleep(15)
        except KeyboardInterrupt:
            log("Encerrado")
            break
        except Exception as e:
            log(f"ERRO: {e}")
            time.sleep(30)


if __name__ == "__main__":
    main()
