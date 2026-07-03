#!/usr/bin/env python3
"""Teste da integracao MCRSession no kernel."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Cria um comando JSON IPC de teste
cmd_data = {"cmd": "status", "args": []}
with open("sandbox/.mcr_cmd.json", "w", encoding="utf-8") as f:
    json.dump(cmd_data, f, ensure_ascii=False)

print("1. Executando kernel com --json...")
import subprocess
r = subprocess.run(
    ["python", "scripts/mcr_devia/kernel.py", "--json", "sandbox/.mcr_cmd.json"],
    capture_output=True, text=True, timeout=30
)
print(f"  stdout: {r.stdout}")
print(f"  stderr: {r.stderr}")

print("\n2. Verificando se sessao foi salva...")
from modulos.MCR import MCRSession
sessao = MCRSession()
estado = sessao.carregar_estado()
print(f"  Estado carregado: {list(estado.keys()) if estado else 'None'}")
if estado:
    print(f"  Ultima pergunta: {estado.get('ultima_pergunta', 'N/A')}")

print("\n3. Testando carregamento no kernel...")
from kernel import MCRKernel
k = MCRKernel()
n = k.inicializar()
print(f"  Kernel inicializado: {n} comandos")
print(f"  MCRSession: {k._mcr_session is not None}")

print("\nOK - Teste concluido")
