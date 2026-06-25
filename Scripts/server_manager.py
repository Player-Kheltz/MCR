#!/usr/bin/env python3
"""Server Manager — gerencia o servidor Canary sem loops."""
import os, sys, signal, time, subprocess, socket

BASE = r"E:\Projeto MCR"
CANARY_DIR = os.path.join(BASE, "Canary")
EXE = os.path.join(CANARY_DIR, "canary-sln.exe")
LOG = os.path.join(CANARY_DIR, "startup_log.txt")

def kill_all():
    """Mata TODOS os processos canary-sln.exe."""
    killed = 0
    try:
        result = subprocess.run(["taskkill", "/f", "/im", "canary-sln.exe"],
                              capture_output=True, text=True, timeout=10)
        killed = 1
    except:
        pass
    
    # Espera portas liberarem (ate 10s)
    for i in range(10):
        time.sleep(1)
        ports_free = True
        for port in [7171, 7172, 7173]:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            try:
                s.connect(("127.0.0.1", port))
                ports_free = False
                s.close()
            except:
                pass
        if ports_free:
            break
    
    return killed

def start():
    """Inicia o servidor e aguarda ficar online."""
    if not os.path.exists(EXE):
        return False, "Executavel nao encontrado"
    
    # Mata processos antigos primeiro
    kill_all()
    
    # Inicia
    with open(LOG, "w") as f:
        proc = subprocess.Popen([EXE], cwd=CANARY_DIR, stdout=f, stderr=subprocess.STDOUT)
    
    # Aguarda online (ate 30s)
    for i in range(30):
        time.sleep(1)
        if proc.poll() is not None:
            return False, f"Servidor morreu (codigo: {proc.returncode})"
        
        # Verifica se portas abriram
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            s.connect(("127.0.0.1", 7171))
            s.close()
            # Le log para confirmar "online"
            if os.path.exists(LOG):
                with open(LOG) as f:
                    if "MCR online" in f.read():
                        return True, f"Server ONLINE (PID: {proc.pid}) apos {i+1}s"
            return True, f"Server respondendo na porta 7171 (PID: {proc.pid})"
        except:
            pass
    
    return False, "Timeout de 30s aguardando servidor"

def status():
    """Verifica status do servidor."""
    # Verifica processo
    try:
        result = subprocess.run(["tasklist", "/fo", "csv", "/nh"],
                              capture_output=True, text=True, timeout=5)
        running = "canary-sln.exe" in result.stdout
    except:
        running = False
    
    # Verifica portas
    ports = {}
    for port in [7171, 7172, 7173]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            s.connect(("127.0.0.1", port))
            ports[port] = "ABERTA"
            s.close()
        except:
            ports[port] = "FECHADA"
    
    # Le ultimas linhas do log
    last_lines = ""
    if os.path.exists(LOG):
        with open(LOG) as f:
            lines = f.readlines()
            last_lines = "".join(lines[-10:])
    
    return {
        "processo": "RODANDO" if running else "PARADO",
        "portas": ports,
        "ultimo_log": last_lines[:500]
    }

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    
    if cmd == "start":
        ok, msg = start()
        print(f"{'✅' if ok else '❌'} {msg}")
    elif cmd == "kill":
        kill_all()
        print("✅ Processos encerrados")
    elif cmd == "status":
        s = status()
        print(f"Processo: {s['processo']}")
        for p, state in s["portas"].items():
            print(f"  Porta {p}: {state}")
        if s["ultimo_log"]:
            print(f"Ultimo log:\n{s['ultimo_log']}")
    else:
        print(f"Comandos: start, kill, status")
