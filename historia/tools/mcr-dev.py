#!/usr/bin/env python3
"""
MCR-Dev v1.0 — Assistente Local Autonomo para Terminal
Uso: python mcr-dev.py
     python mcr-dev.py "comando"  (modo unico)
"""
import sys, os, json, time, readline, atexit

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "scripts"))
sys.path.insert(0, os.path.join(BASE, "Scripts"))

from mcr_dev import engine, memoria

# Historico de comandos
histfile = os.path.join(os.path.dirname(BASE), ".mcr_dev_history")
try:
    readline.read_history_file(histfile)
except:
    pass
atexit.register(readline.write_history_file, histfile)

BANNER = """
╔═══════════════════════════════════════════════════╗
║              MCR-Dev v1.0                         ║
║     Assistente Local Autonomo                     ║
║     Modelos: qwen7b + llama3.1 + ds-r1:8b         ║
║     Hardware: RTX 3080 10GB | 32GB RAM            ║
╚═══════════════════════════════════════════════════╝
  Digite 'ajuda' para comandos | 'stats' para metricas
  Digite 'sair' ou Ctrl+C para encerrar
"""


def modo_unico(comando):
    """Executa um comando unico e sai (modo --quiet para eu usar)."""
    quiet = "--quiet" in sys.argv
    if not quiet:
        print(f"\n  🎯 {comando}")
    
    resposta, arquivo = engine.processar(comando)
    
    if quiet:
        # Saida JSON para consumo programatico
        print(json.dumps({
            "resposta": resposta[:500],
            "arquivo": os.path.relpath(arquivo, BASE) if arquivo else "",
            "status": "ok"
        }, ensure_ascii=False))
    else:
        print(f"\n{resposta}\n")


def modo_interativo():
    """Modo REPL interativo."""
    print(BANNER)
    
    while True:
        try:
            comando = input("\nMCR-Dev > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  👋 MCR-Dev encerrado.")
            break
        
        if not comando:
            continue
        
        if comando.lower() in ("sair", "exit", "quit"):
            print("  👋 MCR-Dev encerrado.")
            break
        
        if comando.lower() in ("stats", "estatisticas"):
            print(memoria.stats())
            continue
        
        if comando.lower() in ("clear", "cls"):
            os.system("cls" if os.name == "nt" else "clear")
            print(BANNER)
            continue
        
        print(f"\n  🎯 Processando: {comando[:60]}")
        resposta, _ = engine.processar(comando)
        print(f"\n{resposta}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        modo_unico(" ".join(sys.argv[1:]))
    else:
        modo_interativo()
