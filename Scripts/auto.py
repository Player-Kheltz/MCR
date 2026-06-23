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
        "canary_exe": os.path.join(MCR, "Canary", "vcproj", "x64", "Release", "canary.exe"),
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
    bat = cmd_vcvars(2026)
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
    cmd = f'""{bat}" && msbuild "{vcxproj}" /p:Configuration=Release /p:Platform=x64 /t:Build /m"'
    print(f"[COMPILE] Canary Release|x64")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    for line in result.stdout.splitlines() + result.stderr.splitlines():
        if "error" in line.lower() or "succeeded" in line.lower() or "0 Erro" in line:
            print(f"  {line.strip()}")
    if result.returncode != 0:
        print(f"[FALHOU] Canary com codigo {result.returncode}")
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


def cmd_server(action):
    cfg = config()
    exe = cfg["canary_exe"]
    if action == "start":
        if not os.path.exists(exe):
            print(f"[ERRO] Canary.exe nao encontrado em: {exe}")
            return
        subprocess.Popen([exe], cwd=os.path.dirname(exe))
        print("[SERVER] Canary iniciado")
    elif action == "stop":
        result = subprocess.run(["taskkill", "/f", "/im", "canary.exe"], capture_output=True, text=True)
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
    else:
        print(f"[ERRO] Comando desconhecido: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
