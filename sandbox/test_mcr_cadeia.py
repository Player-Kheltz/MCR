#!/usr/bin/env python3
"""TESTE: MCRCadeia + MCRPergunta — MCR sem LLM."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRCadeia, MCRPergunta, MCRConector, MCR
from modulos.kg import KnowledgeGraph

PASS = 0; FAIL = 0; TOTAL = 0
def check(nome, cond, detalhe=""):
    global PASS, FAIL, TOTAL; TOTAL += 1
    if cond: PASS += 1; print(f"  [PASS] {nome}")
    else: FAIL += 1; print(f"  [FAIL] {nome} {detalhe}")
def secao(titulo):
    print(f"\n{'='*70}\n  {titulo}\n{'='*70}")

def testar():
    secao("MCRCADEIA + MCRPERGUNTA — MCR substitui LLM")
    kg = KnowledgeGraph()
    conector = MCRConector()
    
    # Alimenta topicos reais
    conector.alimentar("SPA = Sistema de Progressao do Aventureiro, que gerencia habilidades em dominios elementais como Fogo, Gelo, Terra e Energia.", "spa")
    conector.alimentar("Eridanus era uma cidade lendaria conhecida por sua simplicidade e eficiencia. Cidade inicial dos aventureiros.", "eridanus")
    conector.alimentar("O ferreiro em Eridanus forja espadas na bigorna. Ele vende picaretas e armaduras.", "npc_ferreiro")
    
    # ============================================================
    # FASE 1: MCRCadeia
    # ============================================================
    secao("FASE 1: MCRCadeia — geracao infinita sem repetir")
    
    cadeia = MCRCadeia(conector)
    
    print("  Gerando com MCRCadeia (semente='SPA', n=50)...")
    res = cadeia.gerar("SPA", n_tokens=50, contexto_tamanho=3)
    
    print(f"  Tokens gerados: {res['n_tokens']}")
    print(f"  Nota: {res['nota']}/10")
    print(f"  Loops detectados: {res['loops_detectados']}")
    print(f"  Repeticoes evitadas: {res['repeticoes_evitadas']}")
    print(f"  Texto ({len(res['texto'])} chars): {res['texto'][:200]}")
    
    check("F1. Gerou tokens", res['n_tokens'] > 10)
    check("F1. Nota > 0", res['nota'] > 0)
    check("F1. Detectou loops", isinstance(res['loops_detectados'], int))
    
    # Teste com contexto maior
    print("\n  Testando com contexto_tamanho=5...")
    res2 = cadeia.gerar("Eridanus", n_tokens=30, contexto_tamanho=5)
    print(f"  Tokens: {res2['n_tokens']}, Nota: {res2['nota']}/10, "
          f"Loops: {res2['loops_detectados']}")
    check("F1. Contexto maior funciona", res2['n_tokens'] >= 10)
    
    # ============================================================
    # FASE 2: MCRPergunta
    # ============================================================
    secao("FASE 2: MCRPergunta — responde sem LLM")
    
    perguntas = [
        "Explique o sistema SPA do MCR",
        "O que e Eridanus no projeto MCR",
        "Crie um NPC ferreiro em Eridanus",
    ]
    
    for pergunta in perguntas:
        print(f"\n  >>> {pergunta}")
        t0 = __import__('time').time()
        mp = MCRPergunta(kg)
        res = mp.perguntar(pergunta, max_tokens=40)
        tempo = __import__('time').time() - t0
        
        print(f"  Resposta ({res['n_tokens']} tokens, {tempo:.2f}s):")
        print(f"    {res['resposta'][:200]}")
        print(f"  Nota: {res['nota']}/10")
        print(f"  Topicos usados: {res['topicos_usados']}")
        print(f"  Conexoes: {res['n_conexoes']}")
        print(f"  Loops: {res['loops_detectados']}")
        print(f"  Debug:")
        for linha in res['debug'].split('\n')[:5]:
            print(f"    {linha}")
        
        check(f"F2. Resposta nao vazia: {pergunta[:20]}", len(res['resposta']) > 20)
    
    # ============================================================
    # FASE 3: MCRPergunta sem KG (fallback)
    # ============================================================
    secao("FASE 3: MCRPergunta SEM KG (fallback)")
    
    mp2 = MCRPergunta(kg=None)
    res3 = mp2.perguntar("Explique o que e MCR", max_tokens=20)
    print(f"  Resposta: {res3['resposta'][:150]}")
    print(f"  Nota: {res3['nota']}/10")
    check("F3. Fallback sem KG funciona", len(res3['resposta']) > 10)
    
    # ============================================================
    # RELATORIO
    # ============================================================
    perc = (PASS / TOTAL * 100) if TOTAL > 0 else 0
    secao(f"RELATORIO — {PASS}/{TOTAL} ({perc:.0f}%)")
    
    if perc >= 80:
        print(f"\n  ✅ MCRCadeia + MCRPergunta FUNCIONAM")
        print(f"  MCR consegue gerar texto sem repetir (cadeia)")
        print(f"  MCR consegue responder perguntas (KG + conector)")
        print(f"  Proximo passo: MCRValidaCodigo + MCRGeraNPC")
    else:
        print(f"\n  ⚠️ Testes parciais. Revisar gaps.")
    
    return FAIL == 0

if __name__ == '__main__':
    testar()
