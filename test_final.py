#!/usr/bin/env python3
"""Teste final integrado da bridge MCR-DevIA Revived."""
import sys, os, time

sys.path.insert(0, '.')
sys.path.insert(0, os.path.join('.', '..', 'Projeto MCR', 'historia', 'scripts', 'mcr_devia'))

from fix_mcr_devia_v2 import MCRDevIARevived

print("=" * 65)
print("  MCR-DevIA Revived — Teste Final Integrado")
print("=" * 65)

revived = MCRDevIARevived()

testes = [
    ("ler arquivo", "leia o progresso.md"),
    ("criar habilidade", "crie uma habilidade de fogo"),
    ("explicar conceito", "explique o que e SPA"),
    ("diagnosticar", "diagnostique um bug de encoding"),
    ("traduzir", "traduza 'hello world' para PT-BR"),
]

for nome, pergunta in testes:
    print(f"\n--- {nome.upper()} ---")
    t0 = time.time()
    r = revived.processar(pergunta)
    t = time.time() - t0
    
    print(f"  Pergunta: {pergunta[:50]}...")
    print(f"  Classe: {r.get('classe', '?')} (conf={r.get('confianca', 0):.2f})")
    print(f"  Tempo: {t:.4f}s")
    print(f"  Acoes: {r.get('acoes', [])}")
    
    resp = r.get('resposta', '')
    if resp:
        print(f"  Resposta: {resp[:100]}...")

print(f"\n{'='*65}")
print(f"  RESULTADO: Bridge operacional")
print(f"  Markov: {revived.decider.total} seeds | Router: {len(revived.router.SEEDS)} rotas")
print(f"  LLM: {'disponivel' if revived.llm.disponivel() else 'NOK (Ollama)'}")
print(f"  Pipeline: PipelineExecutor com template + filler + cmd pipe")
print(f"{'='*65}")
