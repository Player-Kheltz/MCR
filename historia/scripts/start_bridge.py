#!/usr/bin/env python3
"""Inicia o bridge_auto.py como processo filho e monitora."""
import subprocess, os, sys, time, signal

BASE = r"E:\Projeto MCR"
BRIDGE_SCRIPT = os.path.join(BASE, "Scripts", "bridge_auto.py")
LOG = os.path.join(BASE, "bridge_debug.log")
PID_FILE = os.path.join(BASE, ".bridge_pid")

def start():
    """Inicia o bridge."""
    # Mata bridge anterior se existir
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, signal.SIGTERM)
            print(f"Bridge antigo (PID {old_pid}) encerrado")
        except:
            pass
        os.remove(PID_FILE)
    
    # Limpa logs e arquivos RPC (para evitar IDs antigos poluindo o lastCmdId do servidor)
    for f in [LOG, os.path.join(BASE, "Canary", "data", "logs", "server_cmd.txt"),
              os.path.join(BASE, "Canary", "data", "logs", "server_resp.txt"),
              os.path.join(BASE, "Canary", "data", "logs", "chat_out.txt")]:
        if os.path.exists(f):
            if f.endswith(".log"):
                os.remove(f)
            else:
                open(f, "w").close()  # limpa conteudo mantendo arquivo
    
    # Inicia bridge
    proc = subprocess.Popen(
        [sys.executable, BRIDGE_SCRIPT],
        cwd=BASE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0
    )
    
    # Salva PID
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))
    
    # Aguarda 3s e verifica
    time.sleep(3)
    if proc.poll() is None:
        print(f"Bridge RODANDO (PID: {proc.pid})")
        # Verifica log
        if os.path.exists(LOG):
            with open(LOG) as f:
                lines = f.readlines()
                for line in lines[-5:]:
                    print(f"  {line.strip()[:100]}")
        return True
    else:
        print(f"Bridge MORREU (codigo: {proc.returncode})")
        if os.path.exists(LOG):
            with open(LOG) as f:
                for line in f.readlines()[-10:]:
                    print(f"  {line.strip()[:100]}")
        return False

if __name__ == "__main__":
    success = start()
    sys.exit(0 if success else 1)
