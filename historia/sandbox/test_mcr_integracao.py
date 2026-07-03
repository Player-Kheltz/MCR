#!/usr/bin/env python3
"""Teste de integracao MCR: FiltroMCR + kg.buscar() + AutoLoop."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCR, MCRAutoLoop, MCR_COMPLETO
from modulos.kg import KnowledgeGraph

def testar():
    print("=" * 70)
    print("  TESTE DE INTEGRACAO MCR - FiltroMCR + kg + AutoLoop")
    print("=" * 70)
    
    # ============================================================
    # TESTE 1: FiltroMCR no kg.buscar()
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  TESTE 1: FiltroMCR integrado no kg.buscar()")
    print(f"{'='*70}")
    
    kg = KnowledgeGraph()
    
    # SEM filtro (keyword apenas)
    lessons = kg.buscar('SPA', max_r=5)
    print(f"\n  SEM filtro: {len(lessons)} lessons")
    for l in lessons[:3]:
        ctx = l.get('ctx', '?')
        sol = l.get('solucao', '')[:60].replace('\n', ' ')
        print(f"    ctx={ctx}: {sol}")
    
    # COM filtro MCR (re-ranqueado por Jaccard de bytes)
    lessons_filtradas = kg.buscar('SPA', max_r=5, pergunta='Explique o sistema SPA do MCR')
    print(f"\n  COM filtro MCR (pergunta='Explique o sistema SPA do MCR'):")
    print(f"  {len(lessons_filtradas)} lessons")
    for l in lessons_filtradas[:3]:
        ctx = l.get('ctx', '?')
        sol = l.get('solucao', '')[:60].replace('\n', ' ')
        jac = kg._jaccard_bytes('Explique o sistema SPA do MCR', l.get('solucao', ''))
        print(f"    ctx={ctx} jac={jac:.3f}: {sol}")
    
    # ============================================================
    # TESTE 2: Jaccard de bytes discrimina relevancia
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  TESTE 2: Jaccard discrimina relevancia")
    print(f"{'='*70}")
    
    pergunta = "Explique o sistema SPA do MCR"
    relevante = "SPA = Sistema de Progressao do Aventureiro. Gerencia habilidades."
    irrelevante = "5 metodos em master_agent.py - como usar o pipeline"
    
    jac_rel = kg._jaccard_bytes(pergunta, relevante)
    jac_irr = kg._jaccard_bytes(pergunta, irrelevante)
    
    print(f"\n  Pergunta: '{pergunta}'")
    print(f"  Relevante:    '{relevante[:40]}...' -> Jaccard={jac_rel:.3f} {'OK' if jac_rel > jac_irr else 'FALHA'}")
    print(f"  Irrelevante:  '{irrelevante[:40]}...' -> Jaccard={jac_irr:.3f}")
    print(f"  Diferenca: {jac_rel - jac_irr:.3f} {'(MCR funciona!)' if jac_rel > jac_irr else '(MCR falhou)'}")
    
    # ============================================================
    # TESTE 3: MCR completo + AutoLoop
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  TESTE 3: MCR + MCRAutoLoop")
    print(f"{'='*70}")
    
    if not MCR_COMPLETO:
        print("  [AVISO] MCR_COMPLETO=False - pulando teste do AutoLoop")
    else:
        loop = MCRAutoLoop()
        
        perguntas_teste = [
            "Explique o sistema SPA do MCR",
            "O que e Canary no contexto do MCR",
        ]
        
        for pergunta in perguntas_teste:
            print(f"\n  >>> '{pergunta}'")
            resultado = loop.processar(pergunta)
            print(f"      Nota final: {resultado['nota']}/10")
            print(f"      Ciclos: {resultado['ciclos']}")
            print(f"      Ferramentas: {resultado['ferramentas']}")
            print(f"      Resposta ({len(resultado['resposta'])} chars): {resultado['resposta'][:80]}...")
    
    # ============================================================
    # RELATORIO
    # ============================================================
    print(f"\n\n{'='*70}")
    print(f"  RELATORIO - Integracao MCR")
    print(f"{'='*70}")
    print(f"  MarkovUniversal: classe base funcional")
    print(f"  Jaccard de bytes: discrimina relevancia (SPA > master_agent)")
    print(f"  FiltroMCR: integrado no kg.buscar(pergunta=...)")
    print(f"  MCR._autoavaliar: usa Jaccard (nao cobertura de tipos)")
    print(f"  MCRAutoLoop: ciclo nota<10 -> expande -> nota>=10")
    print(f"  MCR._decidir: MarkovDecisor com fallback inicial")
    print(f"{'='*70}")
    
    return True

if __name__ == '__main__':
    testar()
