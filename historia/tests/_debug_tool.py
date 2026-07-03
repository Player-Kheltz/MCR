#!/usr/bin/env python3
"""Debug: testa se o buscar_codigo encontra os termos nos docs/."""
import sys, os, subprocess
sys.path.insert(0, 'scripts/mcr_devia')

BASE = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

print("=== Teste buscar_codigo ===")
print(f"BASE: {BASE}")

# Testa findstr diretamente
termos = ["MCR", "SPA", "SHC", "Eridanus", "Canary"]
for termo in termos:
    cmd = f'findstr /snip /c:"{termo}" /d:"{BASE}" *.md 2>nul'
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=True)
    stdout = r.stdout.strip()
    print(f"\n--- {termo} ---")
    print(f"  CMD: {cmd}")
    print(f"  Return: {r.returncode}, stdout len: {len(stdout)}")
    if stdout:
        print(f"  Result: {stdout[:300]}")
    else:
        print(f"  NADA ENCONTRADO!")
        # Try without /d:
        cmd2 = f'findstr /snip /c:"{termo}" "{BASE}\\docs\\*.md" 2>nul'
        r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30, shell=True)
        print(f"  CMD2: {cmd2}")
        print(f"  Return2: {r2.returncode}, stdout: {r2.stdout[:300]}")

# Testa o tool_orchestrator diretamente
print("\n\n=== Teste ToolOrchestrator ===")
from modulos.tool_orchestrator import ToolOrchestrator
tools = ToolOrchestrator()
for termo in termos:
    r = tools.executar('buscar_codigo', {'padrao': termo, 'incluir': '*.md'})
    print(f"\n--- {termo} ---")
    print(f"  sucesso: {r.get('sucesso')}")
    resultado = r.get('resultado', '')
    if isinstance(resultado, str):
        print(f"  len: {len(resultado)}, first 200: {resultado[:200]}")
    else:
        print(f"  type: {type(resultado)}")
