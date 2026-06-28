#!/usr/bin/env python3
"""Teste via JSON IPC: sem truncamento, sem shell escaping."""
import json, subprocess, sys, os

KERNEL = r"E:\Projeto MCR\scripts\mcr_devia\MCR_DevIA-Kernel.py"
CMD_FILE = r"E:\Projeto MCR\sandbox\.mcr_cmd.json"
RESULT_FILE = r"E:\Projeto MCR\sandbox\.mcr_result.json"

def ipc(cmd, args):
    """Envia comando via JSON IPC e retorna stdout completo."""
    # Prepara JSON
    cmd_data = {"cmd": cmd, "args": args}
    with open(CMD_FILE, "w", encoding="utf-8") as f:
        json.dump(cmd_data, f, ensure_ascii=False)
    
    # Executa
    r = subprocess.run(
        [sys.executable, KERNEL, "--json", CMD_FILE],
        capture_output=True, text=True, timeout=300
    )
    return r.stdout, r.stderr

# Teste: enviar pergunta complexa sem truncamento
pergunta = """Explique o que e uma monad em Rust usando SOMENTE Rust como exemplo. De codigo completo mostrando Option, Result, and_then, map. Faca um exemplo pratico de encadeamento de operacoes."""

print("Enviando pergunta via JSON IPC...")
stdout, stderr = ipc("perguntar", [pergunta])

# Extrai a resposta (ignorando mensagens do kernel)
linhas = stdout.split('\n')
resposta = []
capturar = False
for linha in linhas:
    if '### DEFINICAO' in linha or 'DEFINICAO' in linha or '1. DEFINICAO' in linha:
        capturar = True
    if capturar:
        resposta.append(linha)

print(f"Resposta completa ({len('\\n'.join(resposta))} chars):")
print('\n'.join(resposta)[:500] + '...')
print(f"\nTotal stdout: {len(stdout)} chars")
print(f"Total stderr: {len(stderr)} chars")
