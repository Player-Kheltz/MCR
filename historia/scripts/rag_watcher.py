#!/usr/bin/env python3
"""
rag_watcher.py — Monitora mudancas nos fontes e reindexa automaticamente.

Uso:
    python scripts/rag_watcher.py                    # Modo monitor (polling a cada 60s)
    python scripts/rag_watcher.py --once             # Verifica uma vez e sai
    python scripts/rag_watcher.py --status           # Mostra status do watcher
"""
import os, sys, time, json, subprocess, threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEXER = os.path.join(BASE_DIR, "scripts", "rag_indexer.py")
PID_FILE = os.path.join(BASE_DIR, ".rag_watcher_pid")
WATCH_LOG = os.path.join(BASE_DIR, "rag_watcher.log")

# Diretorios monitorados (mesmo do rag_indexer.py)
WATCH_DIRS = [
    os.path.join(BASE_DIR, "Canary", "src"),
    os.path.join(BASE_DIR, "Canary", "data-canary", "scripts"),
    os.path.join(BASE_DIR, "OTClient", "src"),
    os.path.join(BASE_DIR, "OTClient", "modules"),
    os.path.join(BASE_DIR, "docs"),
    os.path.join(BASE_DIR, "Scripts"),
]

POLL_INTERVAL = 120  # segundos entre verificacoes
MAX_LOG_SIZE = 1024 * 1024  # 1MB


def log(msg):
    with open(WATCH_LOG, "a", encoding="utf-8") as f:
        f.write(f"{int(time.time())}|WATCH|{msg}\n")


def check_log_size():
    """Rotaciona log se > 1MB."""
    if os.path.exists(WATCH_LOG) and os.path.getsize(WATCH_LOG) > MAX_LOG_SIZE:
        bak = WATCH_LOG + ".1"
        if os.path.exists(bak):
            os.remove(bak)
        os.rename(WATCH_LOG, bak)
        log("Log rotacionado")


def get_mtimes():
    """Retorna dicionario {arquivo: mtime} para todos os arquivos monitorados."""
    mtimes = {}
    for watch_dir in WATCH_DIRS:
        if not os.path.exists(watch_dir):
            continue
        for root, dirs, files in os.walk(watch_dir):
            dirs[:] = [d for d in dirs if not d.startswith((".", "__", "build", "vcpkg", "Backup"))]
            for f in files:
                if f.endswith((".cpp", ".hpp", ".h", ".lua", ".md", ".txt", ".otui")):
                    fpath = os.path.join(root, f)
                    try:
                        mtimes[fpath] = os.path.getmtime(fpath)
                    except OSError:
                        pass
    return mtimes


def scan_for_changes(cache):
    """Compara mtimes atuais com cache. Retorna lista de arquivos alterados."""
    current = get_mtimes()
    changed = []
    for fpath, mtime in current.items():
        cached = cache.get(fpath)
        if cached is None or mtime > cached + 1:
            rel = os.path.relpath(fpath, BASE_DIR)
            changed.append(rel)
    return changed, current


def run_indexer():
    """Executa rag_indexer.py (incremental)."""
    log("Reindexando...")
    result = subprocess.run(
        ["C:\\Python314\\python.exe", INDEXER],
        capture_output=True, text=True, timeout=300
    )
    lines = result.stdout.strip().split("\n")
    last = [l for l in lines if l.strip()][-3:]
    for l in last:
        log(f"  {l.strip()}")


def main():
    if "--status" in sys.argv:
        if os.path.exists(PID_FILE):
            with open(PID_FILE) as f:
                pid = f.read().strip()
            if os.name == "nt":
                r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
                if str(pid) in r.stdout:
                    print(f"Watcher rodando (PID {pid})")
                    return
            print(f"Watcher PID {pid} nao encontrado (processo morto)")
        else:
            print("Watcher nao esta rodando")
        return

    if "--once" in sys.argv:
        log("Verificacao unica")
        cache = get_mtimes()
        changed, _ = scan_for_changes(cache)
        if changed:
            log(f"{len(changed)} arquivos alterados. Reindexando...")
            run_indexer()
        else:
            log("Nenhuma alteracao")
        return

    # Modo monitor
    log(f"Watcher iniciado (polling a cada {POLL_INTERVAL}s)")

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    cache = get_mtimes()
    log(f"Cache inicial: {len(cache)} arquivos")

    while True:
        try:
            check_log_size()
            time.sleep(POLL_INTERVAL)
            changed, cache = scan_for_changes(cache)
            if changed:
                log(f"{len(changed)} arquivos alterados. Reindexando...")
                for c in changed[:5]:
                    log(f"  {c}")
                if len(changed) > 5:
                    log(f"  ... e mais {len(changed)-5}")
                run_indexer()
            else:
                log("Nenhuma alteracao")
        except KeyboardInterrupt:
            log("Watcher encerrado")
            break
        except Exception as e:
            log(f"ERRO: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
