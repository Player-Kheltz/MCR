#!/usr/bin/env python3
"""Executa MCR-DevIA (Supervisor + Orquestrador) diretamente, sem ruido do kernel.
Uso: python executar_mcr.py all | <id>
"""
import os, sys, json

BASE = os.path.dirname(os.path.abspath(__file__))
MCR_DIR = os.path.join(BASE, "respostas_mcr")
ARQS_DIR = os.path.join(BASE, "arquivos")
BATERIA_PATH = os.path.join(BASE, "bateria.json")

# Adiciona MCR-DevIA ao path
MCR_DEVIA = os.path.join(BASE, "..", "..", "scripts", "mcr_devia")
sys.path.insert(0, MCR_DEVIA)

def _carregar_bateria():
    with open(BATERIA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def _construir_prompt(test):
    """Monta prompt completo com arquivos embutidos."""
    lines = [test['prompt']]
    for arq in test.get("arquivos", []):
        path = os.path.join(ARQS_DIR, arq)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                conteudo = f.read()
            lines.append(f"\n--- ARQUIVO: {arq} ---")
            lines.append(conteudo)
            lines.append(f"--- FIM {arq} ---")
    return "\n".join(lines)

def _init_mcr():
    """Inicializa KG, IA, ContextCrew, Orquestrador e Supervisor."""
    from mcr_devia import KnowledgeGraph
    from modulos.ia import IA
    from modulos.orquestrador import Orquestrador
    from modulos.supervisor import Supervisor
    
    # Silencia saida do MCR-DevIA
    import contextlib
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            kg = KnowledgeGraph()
            ia = IA()
            import context_crew as cc
            ctx_crew = cc.ContextCrew()
        finally:
            sys.stdout = old_stdout
    
    orq = Orquestrador(kg=kg, ia=ia, ctx_crew=ctx_crew)
    
    # Le identidade
    identidade = ""
    id_path = os.path.join(BASE, "..", "..", "docs", "MCR_IDENTITY.md")
    try:
        if os.path.exists(id_path):
            with open(id_path, 'r', encoding='utf-8') as f:
                identidade = f.read()[:500].strip()
    except:
        pass
    
    sup = Supervisor(ia, kg, ctx_crew=ctx_crew, orquestrador=orq, identidade=identidade)
    return sup

def executar_teste(test, supervisor):
    tid = test["id"]
    prompt = _construir_prompt(test)
    
    print(f"\n--- Teste {tid}: {test['titulo']} ({test['categoria']}) ---")
    
    try:
        resposta = supervisor.perguntar(prompt)
    except Exception as e:
        resposta = f"[MCR ERRO: {e}]"
    
    path = os.path.join(MCR_DIR, f"test_{tid}.txt")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(resposta or "")
    print(f"  -> {len(resposta or '')} chars em test_{tid}.txt")

def executar_todos():
    bateria = _carregar_bateria()
    
    print("Inicializando MCR-DevIA (Supervisor + Orquestrador)...")
    supervisor = _init_mcr()
    print("OK. Executando testes...")
    
    for test in bateria["testes"]:
        executar_teste(test, supervisor)
    
    print("\n=== TODOS OS TESTES CONCLUIDOS ===")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        executar_todos()
    elif len(sys.argv) > 1:
        tid = int(sys.argv[1])
        bateria = _carregar_bateria()
        supervisor = _init_mcr()
        for t in bateria["testes"]:
            if t["id"] == tid:
                executar_teste(t, supervisor)
                break
    else:
        print("Uso: python executar_mcr.py all | <id>")
