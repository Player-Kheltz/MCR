#!/usr/bin/env python3
"""
auto.py — Central de Comandos do Assistente MCR

Uso:
    python scripts/auto.py compile --client    # Compila OTClient
    python scripts/auto.py compile --server    # Compila Canary
    python scripts/auto.py compile --both      # Ambos
    python scripts/auto.py status              # Git status + diffs + pendências
    python scripts/auto.py verify              # status + doc-sync + pergunta commit
    python scripts/auto.py commit "mensagem"   # git add -A + commit + push
    python scripts/auto.py sync                # Regenera CATALOG.md
    python scripts/auto.py index               # Regenera INDEX.md
    python scripts/auto.py session             # Mostra session.json
    python scripts/auto.py server start        # Abre Canary.exe
    python scripts/auto.py server stop         # Mata Canary
    python scripts/auto.py server restart      # stop + start
    python scripts/auto.py up                  # Sobe tudo (server + bridge + watchdog)
    python scripts/auto.py status              # Saude de todos os sistemas
    python scripts/auto.py doctor              # Diagnostico e sugestoes
    python scripts/auto.py watchdog            # Inicia watchdog
    python scripts/auto.py reindex             # Reindexa RAG em background
    python scripts/auto.py checkpoint           # Mostra estado do checkpoint
    python scripts/auto.py checkpoint save      # Salva checkpoint
    python scripts/auto.py checkpoint clear     # Marca checkpoint como concluído
    python scripts/auto.py checkpoint recover   # Tenta recuperar sessão do checkpoint
"""

import os
import sys
import subprocess
import json
import re
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCR = BASE_DIR

def config():
    return {
        "vs2026": r"C:\Program Files\Microsoft Visual Studio\2026\Community",
        "vs2022": r"C:\Program Files\Microsoft Visual Studio\2022\Community",
        "mcr": MCR,
        "otclient_vcxproj": os.path.join(MCR, "OTClient", "vc17", "otclient.vcxproj"),
        "canary_vcxproj": os.path.join(MCR, "Canary", "vcproj", "canary.vcxproj"),
        "canary_exe": os.path.join(MCR, "Canary", "canary-sln.exe"),
        "session_path": os.path.join(MCR, "docs", "session.json"),
        "pendencias_path": os.path.join(MCR, "docs", "MCR - Instruções", "DevLog", "Pendências.md"),
        "scripts": os.path.join(MCR, "scripts"),
    }


def cmd_vcvars(version):
    cfg = config()
    key = f"vs{version}"
    path = cfg.get(key)
    if not path or not os.path.exists(path):
        print(f"[ERRO] VS{version} nao encontrado em: {path}")
        sys.exit(1)
    bat = os.path.join(path, "VC", "Auxiliary", "Build", "vcvars64.bat")
    if not os.path.exists(bat):
        print(f"[ERRO] vcvars64.bat nao encontrado em: {bat}")
        sys.exit(1)
    return bat


def compile_client():
    cfg = config()
    bat = cmd_vcvars(2022)
    vcxproj = cfg["otclient_vcxproj"]
    cmd = f'""{bat}" && msbuild "{vcxproj}" /p:Configuration=OpenGL /p:Platform=x64 /t:Build /m"'
    print(f"[COMPILE] OTClient OpenGL|x64")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    for line in result.stdout.splitlines() + result.stderr.splitlines():
        if "error" in line.lower() or "succeeded" in line.lower() or "0 Erro" in line:
            print(f"  {line.strip()}")
    if result.returncode != 0:
        print(f"[FALHOU] OTClient com codigo {result.returncode}")
    else:
        print("[OK] OTClient compilado")
    return result.returncode


def compile_server():
    cfg = config()
    bat = cmd_vcvars(2022)
    vcxproj = cfg["canary_vcxproj"]
    canary_dir = os.path.dirname(os.path.dirname(vcxproj))  # Canary/
    cmd = f'call "{bat}" && msbuild "{vcxproj}" /p:Configuration=Release /p:Platform=x64 /t:Build /m"'
    print(f"[COMPILE] Canary Release|x64")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=canary_dir)
    out = (result.stdout or "") + (result.stderr or "")
    for line in out.splitlines():
        l = line.strip()
        if not l:
            continue
        if any(kw in l.lower() for kw in ["error", "fatal", "succeeded", "exito", "aviso", "warning"]):
            print(f"  {l}")
        elif l.startswith("canary.vcxproj ->") or "0 Erro" in l or "0 erro" in l.lower():
            print(f"  {l}")
    if result.returncode != 0 and "Build succeeded" not in out and "Compila" not in out:
        print(f"[FALHOU] Canary com codigo {result.returncode}")
        for l in out.splitlines()[-5:]:
            print(f"  ! {l.strip()}")
    else:
        print("[OK] Canary compilado")
    return result.returncode


def cmd_status():
    cfg = config()
    print("=== Git Status ===")
    result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=MCR)
    print(result.stdout if result.stdout else "(nenhuma alteracao)")
    
    print("\n=== Diff --stat ===")
    result = subprocess.run(["git", "diff", "--stat"], capture_output=True, text=True, cwd=MCR)
    if result.stdout:
        lines = result.stdout.strip().splitlines()
        for l in lines[-5:]:
            print(f"  {l.strip()}")
    else:
        print("  (nenhum diff)")
    
    print("\n=== Ultimas Pendencias ===")
    pendencias = cfg["pendencias_path"]
    if os.path.exists(pendencias):
        with open(pendencias, "r", encoding="utf-8") as f:
            lines = f.readlines()
        pendentes = [l.strip().lstrip("- [ ] ") for l in lines if "- [ ] " in l]
        if pendentes:
            for p in pendentes[:5]:
                print(f"  \u2022 {p}")
        else:
            print("  (nenhuma pendencia marcada)")
    else:
        print("  (Pendencias.md nao encontrado)")


def cmd_verify():
    cfg = config()
    cmd_status()
    
    print("\n=== Sincronizando Documentacao ===")
    doc_sync = os.path.join(cfg["scripts"], "doc-sync.py")
    if os.path.exists(doc_sync):
        subprocess.run([sys.executable, doc_sync, "--catalog"], cwd=MCR)
    
    print("\n=== Verificacao concluida ===")
    answer = input("Commit? [s/N] ").strip().lower()
    if answer in ("s", "sim"):
        msg = input("Mensagem do commit: ").strip()
        if msg:
            cmd_commit(msg)


def cmd_commit(msg):
    if not msg:
        print("[ERRO] Mensagem vazia")
        return
    print(f"[COMMIT] {msg}")
    result = subprocess.run(["git", "add", "-A"], capture_output=True, text=True, cwd=MCR)
    if result.returncode != 0:
        print(f"[ERRO] git add falhou: {result.stderr}")
        return
    result = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True, cwd=MCR)
    for line in (result.stdout + result.stderr).splitlines():
        print(f"  {line.strip()}")
    if result.returncode != 0:
        print("[ERRO] git commit falhou")
        return
    result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, cwd=MCR)
    for line in (result.stdout + result.stderr).splitlines():
        if "error" in line.lower():
            print(f"  {line.strip()}")


def cmd_sync():
    cfg = config()
    doc_sync = os.path.join(cfg["scripts"], "doc-sync.py")
    if os.path.exists(doc_sync):
        subprocess.run([sys.executable, doc_sync], cwd=MCR)
    else:
        print("[ERRO] doc-sync.py nao encontrado")


def cmd_index():
    cfg = config()
    doc_index = os.path.join(cfg["scripts"], "doc-index.py")
    if os.path.exists(doc_index):
        subprocess.run([sys.executable, doc_index], cwd=MCR)
    else:
        print("[INFO] doc-index.py ainda nao implementado. Use 'info.py' quando disponivel.")


def cmd_session():
    cfg = config()
    path = cfg["session_path"]
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("(session.json nao encontrado)")


def cmd_up():
    """Sobe tudo: server + watchdog + bridge."""
    print("[UP] Iniciando todos os sistemas...")

    # 1. Mata processos antigos
    subprocess.run(["taskkill", "/f", "/im", "canary-sln.exe"], capture_output=True, text=True)
    subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True, text=True)
    time.sleep(3)

    # 2. Inicia servidor
    cfg = config()
    exe = cfg["canary_exe"]
    log_path = os.path.join(os.path.dirname(exe), "data", "logs", "server_output.log")
    with open(log_path, "w") as lf:
        subprocess.Popen([exe], cwd=os.path.dirname(exe), stdout=lf, stderr=lf)

    # 3. Aguarda online
    for i in range(45):
        time.sleep(1)
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                if "Projeto MCR online!" in f.read():
                    print(f"[UP] Servidor online ({i+1}s)")
                    break
    else:
        print("[UP] Timeout aguardando servidor")
        return

    # 4. Inicia watchdog (que inicia bridge)
    watchdog_script = os.path.join(MCR, "scripts", "bridge_watchdog.py")
    subprocess.run([sys.executable, watchdog_script, "--once"], timeout=15)
    print("[UP] Watchdog + Bridge: OK")

    print("[UP] Sistema pronto!")


def cmd_status_all():
    """Mostra saude de todos os sistemas."""
    cfg = config()
    print("=== STATUS DO SISTEMA ===\n")

    # Server
    proc = subprocess.run(["tasklist", "/FI", "IMAGENAME eq canary-sln.exe"],
                          capture_output=True, text=True)
    if "canary-sln.exe" in proc.stdout:
        lines = [l for l in proc.stdout.split("\n") if "canary-sln" in l]
        print(f"[SERVER] Rodando ({len(lines)} processo(s))")
    else:
        print("[SERVER] PARADO")

    # Bridge
    pid_file = os.path.join(MCR, ".bridge_pid")
    if os.path.exists(pid_file):
        with open(pid_file) as f:
            pid = f.read().strip()
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
        if str(pid) in r.stdout:
            print(f"[BRIDGE] Rodando (PID {pid})")
        else:
            print("[BRIDGE] MORTO (PID file existe mas processo nao)")
    else:
        print("[BRIDGE] NAO INICIADO")

    # Watchdog
    wd_pid_file = os.path.join(MCR, ".watchdog_pid")
    if os.path.exists(wd_pid_file):
        with open(wd_pid_file) as f:
            pid = f.read().strip()
        print(f"[WATCHDOG] PID {pid}")
    else:
        print("[WATCHDOG] NAO INICIADO")

    # Ollama
    try:
        import urllib.request, json
        resp = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        data = json.loads(resp.read())
        print(f"[OLLAMA] Online ({len(data['models'])} modelos)")
    except Exception:
        print("[OLLAMA] OFFLINE")

    # RAG
    rag_idx = os.path.join(MCR, ".rag_db", "index.json")
    if os.path.exists(rag_idx):
        import json as j
        with open(rag_idx, "r", encoding="utf-8") as f:
            idx = j.load(f)
        print(f"[RAG] {len(idx.get('chunks', []))} chunks")
    else:
        print("[RAG] NAO INDEXADO")


def cmd_doctor():
    """Diagnostico e sugestoes de correcao."""
    print("=== MCR DOCTOR ===\n")
    issues = []
    oks = []

    # Server
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq canary-sln.exe"], capture_output=True, text=True)
    if "canary-sln.exe" in r.stdout:
        oks.append("Servidor rodando")
    else:
        issues.append(("SERVER", "Servidor parado. Execute: python auto.py server start"))

    # Ollama
    try:
        import urllib.request, json
        resp = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        data = json.loads(resp.read())
        models = [m["name"] for m in data["models"]]
        oks.append(f"Ollama online ({len(models)} modelos)")
        if "qwen2.5-coder:7b" not in models:
            issues.append(("OLLAMA", "Modelo qwen2.5-coder:7b nao encontrado. Execute: ollama pull qwen2.5-coder:7b"))
    except Exception:
        issues.append(("OLLAMA", "Ollama offline. Execute: ollama serve"))

    # Bridge
    pid_file = os.path.join(MCR, ".bridge_pid")
    if os.path.exists(pid_file):
        with open(pid_file) as f:
            pid = f.read().strip()
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
        if str(pid) in r.stdout:
            oks.append(f"Bridge rodando (PID {pid})")
        else:
            issues.append(("BRIDGE", "Bridge morto. Execute: python auto.py watchdog"))
    else:
        issues.append(("BRIDGE", "Bridge nao iniciado. Execute: python auto.py watchdog"))

    # Watchdog
    wd_lock = os.path.join(MCR, ".watchdog_pid")
    if os.path.exists(wd_lock):
        with open(wd_lock) as f:
            wpid = f.read().strip()
        r = subprocess.run(["tasklist", "/FI", f"PID eq {wpid}"], capture_output=True, text=True)
        if str(wpid) in r.stdout:
            oks.append(f"Watchdog rodando (PID {wpid})")
        else:
            issues.append(("WATCHDOG", "Watchdog lock existe mas processo morto"))
    else:
        issues.append(("WATCHDOG", "Watchdog nao iniciado"))

    # RAG
    rag_idx = os.path.join(MCR, ".rag_db", "index.json")
    if os.path.exists(rag_idx):
        import json as j2
        with open(rag_idx, "r", encoding="utf-8") as f:
            idx = j2.load(f)
        oks.append(f"RAG indexado ({len(idx.get('chunks', []))} chunks)")
    else:
        issues.append(("RAG", "Indice nao encontrado. Execute: python auto.py reindex"))

    # OC-Dev
    ocdev = os.path.join(MCR, "opencode.local.json")
    sandbox = os.path.join(MCR, "sandbox")
    if os.path.exists(ocdev) and os.path.exists(sandbox):
        oks.append("OC-Dev configurado + sandbox")
    else:
        issues.append(("OC-DEV", "Configuracao incompleta"))

    # Lessons
    lessons_dir = os.path.join(MCR, "docs", "lessons")
    if os.path.exists(lessons_dir):
        n = len([f for f in os.listdir(lessons_dir) if f.endswith(".md")])
        oks.append(f"{n} lessons disponiveis")
    else:
        issues.append(("LESSONS", "Diretorio docs/lessons/ nao encontrado"))

    print("Sistemas OK:")
    for msg in oks:
        print(f"  [OK] {msg}")

    if issues:
        print("\nProblemas encontrados:")
        for component, msg in issues:
            print(f"  [{component}] {msg}")
    else:
        print("\n[OK] Todos os sistemas operacionais!")

    print()
    print("Para iniciar tudo: python auto.py up")
    return len(issues)


def cmd_server(action):
    cfg = config()
    exe = cfg["canary_exe"]
    if action == "start":
        if not os.path.exists(exe):
            print(f"[ERRO] Canary.exe nao encontrado em: {exe}")
            return
        log_path = os.path.join(os.path.dirname(exe), "data", "logs", "server_output.log")
        with open(log_path, "w") as lf:
            subprocess.Popen([exe], cwd=os.path.dirname(exe), stdout=lf, stderr=lf)
        print("[SERVER] Canary iniciado (output em data/logs/server_output.log)")
    elif action == "stop":
        result = subprocess.run(["taskkill", "/f", "/im", "canary-sln.exe"], capture_output=True, text=True)
        if result.returncode == 0:
            print("[SERVER] Canary encerrado")
        else:
            print("[SERVER] Canary nao estava rodando")
    elif action == "restart":
        cmd_server("stop")
        cmd_server("start")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "compile":
        target = sys.argv[2] if len(sys.argv) > 2 else "--client"
        if target == "--client":
            compile_client()
        elif target == "--server":
            compile_server()
        elif target == "--both":
            compile_client()
            compile_server()
        else:
            print(f"[ERRO] Alvo desconhecido: {target}")
    elif command == "status":
        cmd_status()
    elif command == "verify":
        cmd_verify()
    elif command == "commit":
        msg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        cmd_commit(msg)
    elif command == "sync":
        cmd_sync()
    elif command == "index":
        cmd_index()
    elif command == "session":
        cmd_session()
    elif command == "server":
        action = sys.argv[2] if len(sys.argv) > 2 else "status"
        cmd_server(action)
    elif command == "test":
        subprocess.run([sys.executable, os.path.join(MCR, "scripts", "test_runner.py")] + sys.argv[2:])
    elif command == "test-suite":
        suite = sys.argv[2] if len(sys.argv) > 2 else "basico"
        suite_path = os.path.join(MCR, "scripts", "tests", suite if suite.endswith(".txt") else suite + ".txt")
        subprocess.run([sys.executable, os.path.join(MCR, "scripts", "test_runner.py"), "--suite", suite_path])
    elif command == "watchdog":
        subprocess.Popen([sys.executable, os.path.join(MCR, "scripts", "bridge_watchdog.py")])
        print("[WATCHDOG] Iniciado")
    elif command == "reindex":
        if len(sys.argv) > 2 and sys.argv[2] == "--watch":
            subprocess.Popen([sys.executable, os.path.join(MCR, "scripts", "rag_watcher.py")])
            print("[REINDEX] Watcher iniciado em background")
        else:
            subprocess.Popen([sys.executable, os.path.join(MCR, "scripts", "rag_indexer.py")])
            print("[REINDEX] Iniciado em background")
    elif command == "up":
        cmd_up()
    elif command == "checkpoint":
        checkpoint_script = os.path.join(BASE_DIR, "scripts", "checkpoint.py")
        subprocess.run([sys.executable, checkpoint_script] + sys.argv[2:])
    elif command == "doctor":
        cmd_doctor()
    elif command == "status" and len(sys.argv) == 2:
        cmd_status_all()
    else:
        print(f"[ERRO] Comando desconhecido: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
