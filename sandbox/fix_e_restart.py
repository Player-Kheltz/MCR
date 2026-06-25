#!/usr/bin/env python3
"""Mata server, compila, inicia. UMA EXECUCAO, SEM LOOPS."""
import subprocess, os, sys, time

BASE = r"E:\Projeto MCR"
EXE = os.path.join(BASE, "Canary", "canary-sln.exe")

print("1. Matando processos...")
subprocess.run(["taskkill", "/f", "/im", "canary-sln.exe"], capture_output=True)
time.sleep(2)

print("2. Compilando...")
ret = subprocess.run(
    [r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat", "&&",
     r"C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\amd64\MSBuild.exe",
     os.path.join(BASE, "Canary", "vcproj", "canary.vcxproj"),
     "/p:Configuration=Release", "/p:Platform=x64", "/t:Build", "/m"],
    shell=True, capture_output=True, text=True, timeout=120
)
if "0 Erro" in ret.stdout or "sucesso" in ret.stdout:
    print("  Compilado com sucesso!")
else:
    print(f"  ERRO compilacao: {ret.stdout[-200:]}")
    sys.exit(1)

print(f"3. EXE atualizado: {os.path.getmtime(EXE)}")

print("4. Iniciando servidor...")
proc = subprocess.Popen([EXE], cwd=os.path.join(BASE, "Canary"),
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)

if proc.poll() is None:
    print(f"  Server ONLINE (PID: {proc.pid})")
else:
    print(f"  Server MORREU (codigo: {proc.returncode})")
    sys.exit(1)

print("5. Pronto! Arbalest vai funcionar agora.")
print("  (o jogador precisa olhar para ele de novo)")
