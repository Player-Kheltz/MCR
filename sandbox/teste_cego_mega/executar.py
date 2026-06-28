#!/usr/bin/env python3
"""Executa MCR-DevIA para o MEGA TESTE CEGO.
Chamada direta ao Supervisor com o prompt completo.
"""
import os, sys, json

BASE = os.path.dirname(os.path.abspath(__file__))
MCR_DIR = os.path.join(BASE, "respostas_mcr")
CLOUD_DIR = os.path.join(BASE, "respostas_cloud")
ARQS_DIR = os.path.join(BASE, "arquivos")

MCR_DEVIA = os.path.join(BASE, "..", "..", "scripts", "mcr_devia")
sys.path.insert(0, MCR_DEVIA)

def _construir_prompt():
    """Le o prompt do mega teste + arquivos."""
    with open(os.path.join(BASE, "MEGA_TESTE.json"), 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    prompt = config["teste"]["prompt"]
    
    # Anexa arquivos
    for arq in config["teste"].get("arquivos", []):
        path = os.path.join(ARQS_DIR, arq)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                conteudo = f.read()
            prompt += f"\n\n--- ARQUIVO: {arq} ---\n{conteudo}\n--- FIM ---\n"
    
    return prompt

def _init_mcr():
    from mcr_devia import KnowledgeGraph
    from modulos.ia import IA
    from modulos.orquestrador import Orquestrador
    from modulos.supervisor import Supervisor
    import context_crew as cc
    
    import contextlib
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            kg = KnowledgeGraph()
            ia = IA()
            ctx_crew = cc.ContextCrew()
        finally:
            sys.stdout = old_stdout
    
    orq = Orquestrador(kg=kg, ia=ia, ctx_crew=ctx_crew)
    
    identidade = ""
    id_path = os.path.join(BASE, "..", "..", "docs", "MCR_IDENTITY.md")
    try:
        if os.path.exists(id_path):
            with open(id_path, 'r', encoding='utf-8') as f:
                identidade = f.read()[:500].strip()
    except: pass
    
    sup = Supervisor(ia, kg, ctx_crew=ctx_crew, orquestrador=orq, identidade=identidade)
    return sup

def executar_mcr():
    prompt = _construir_prompt()
    print("Inicializando MCR-DevIA...")
    supervisor = _init_mcr()
    print("Executando Mega Teste...")
    
    resposta = supervisor.perguntar(prompt)
    
    path = os.path.join(MCR_DIR, "mega_1.txt")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(resposta or "")
    print(f"MCR: {len(resposta or '')} chars salvos")
    return resposta

def salvar_cloud(resposta):
    """Salva resposta da Cloud (chamada externa)."""
    path = os.path.join(CLOUD_DIR, "mega_1.txt")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(resposta)
    print(f"Cloud: {len(resposta)} chars salvos")

def _cloud_direto(prompt):
    """Cloud: llama3.1:8b para resposta direta."""
    try:
        d = json.dumps({
            "model": "qwen2.5-coder:7b", "prompt": prompt, "stream": False,
            "options": {"temperature": 0.3, "num_ctx": 8192, "num_predict": 8192}
        }).encode()
        r = urllib.request.Request("http://localhost:11434/api/generate", data=d,
            headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(r, timeout=300).read())
        return resp.get("response", "")
    except Exception as e:
        return f"[ERRO IA: {e}]"

if __name__ == "__main__":
    import urllib.request
    
    if len(sys.argv) > 1 and sys.argv[1] == "cloud":
        prompt = _construir_prompt()
        print("Executando Cloud direto...")
        resposta = _cloud_direto(prompt[:6000])  # Limite de contexto
        salvar_cloud(resposta)
    elif len(sys.argv) > 1 and sys.argv[1] == "mcr":
        executar_mcr()
    else:
        # Executa ambos: Cloud primeiro (cego), MCR depois
        prompt = _construir_prompt()
        
        # 1. Cloud escreve primeiro
        print("=" * 60)
        print("FASE 1: Cloud respondendo (sem ler MCR)...")
        resposta_cloud = _cloud_direto(prompt[:6000])
        salvar_cloud(resposta_cloud)
        
        # 2. MCR escreve depois (sem ler Cloud)
        print("=" * 60)
        print("FASE 2: MCR-DevIA respondendo (sem ler Cloud)...")
        resposta_mcr = executar_mcr()
        
        print("=" * 60)
        print("AMBOS COMPLETOS! Rode o avaliador: python avaliador.py")
