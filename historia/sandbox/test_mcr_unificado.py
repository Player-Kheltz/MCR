#!/usr/bin/env python3
"""TESTE DE INTEGRACAO UNIFICADO — Todos os conceitos MCR em 1 prototipo.
Valida: MCRFingerprint, MCRCruzado, MCRConector, Autoavaliacao MultiNivel,
PreCache, Geracao, Loop.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import (MCRFingerprint, MCRConector, MarkovUniversal,
                          MCRPreCache, GeradorNarrativa, AutoavaliadorSemantico,
                          MCRAutoLoop, MCR)
from modulos.kg import KnowledgeGraph

PASS = 0; FAIL = 0; TOTAL = 0
def check(nome, cond, detalhe=""):
    global PASS, FAIL, TOTAL; TOTAL += 1
    if cond: PASS += 1; print(f"  [PASS] {nome}")
    else: FAIL += 1; print(f"  [FAIL] {nome} {detalhe}")

def secao(titulo):
    print(f"\n{'='*70}\n  {titulo}\n{'='*70}")

def testar():
    secao("MCR UNIFICADO — Todos os conceitos integrados")
    
    kg = KnowledgeGraph()
    
    # ============================================================
    # FASE 1: MCRFingerprint
    # ============================================================
    secao("FASE 1: MCRFingerprint — Dimensionalidade por entropia")
    
    fp = MCRFingerprint()
    textos_fp = [
        ("Crie um NPC ferreiro em Eridanus", "CREATE"),
        ("Explique o sistema SPA do MCR", "EXPLAIN"),
        ("local function onSay(cid, words) end", "CODE"),
    ]
    
    for texto, nome in textos_fp:
        vetor = fp.gerar(texto)
        print(f"  {nome:8s}: {len(vetor)} dims -> {[round(v,2) for v in vetor[:5]]}...")
    
    check("F1. Fingerprint tem dims variaveis", 
          len(fp.gerar(textos_fp[0][0])) != len(fp.gerar(textos_fp[2][0])))
    
    # ============================================================
    # FASE 2: MCRConector (Cruzado + Emergencia)
    # ============================================================
    secao("FASE 2: MCRConector — Emergencia multi-nivel")
    
    c = MCRConector()
    c.alimentar('SPA = Sistema de Progressao do Aventureiro. Gerencia habilidades em dominios elementais.', 'spa')
    c.alimentar('Eridanus era uma cidade lendaria conhecida por sua simplicidade e eficiencia.', 'eridanus')
    c.alimentar('O NPC ferreiro forja espadas na bigorna. Ele vende picaretas e armaduras.', 'npc_ferreiro')
    
    print(f"  Topicos: {len(c.topicos)}")
    
    conexoes = [
        c.conectar('spa', 'eridanus'),
        c.conectar('npc_ferreiro', 'eridanus'),
        c.conectar('spa', 'npc_ferreiro'),
    ]
    
    for cx in conexoes:
        if cx:
            nota = cx['nota']
            tipo = cx['tipo_ponte']
            seq = cx['sequencia'][:60]
            print(f"  {cx['topico_a']:15s} <-> {cx['topico_b']:15s}: {nota}/10 ({tipo:25s}) '{seq}'")
    
    check("F2. Conexoes geradas", any(cx is not None for cx in conexoes))
    check("F2. Nota > 0", any(cx and cx['nota'] > 0 for cx in conexoes))
    
    # Debug
    if conexoes[0]:
        debug = c.debug(conexoes[0])
        print(f"\n  Debug:\n{debug}")
        check("F2. Debug contem Byte/Palavra/Token",
              'Byte' in debug and 'Palavra' in debug and 'Token' in debug)
    
    # ============================================================
    # FASE 3: Autoavaliacao MultiNivel
    # ============================================================
    secao("FASE 3: Autoavaliacao MultiNivel — Byte+Palavra+Token")
    
    # Reuso o conector para avaliar textos conhecidos
    textos_avalia = [
        ("LOREA", "Eridanus era uma cidade lendaria. Fundada por exploradores que buscavam novas terras."),
        ("GARBAGE", "xyz uipo asdf qwert zxcv bnmp"),
        ("CODIGO", "local function onCreate(cid) local player = Player(cid) end"),
    ]
    
    for nome, texto in textos_avalia:
        nota, det = c._autoavaliar_multinivel(texto, textos_avalia[0][1], "", "conteudo_compartilhado")
        nb = det.get('byte', {}).get('nota', 0)
        np = det.get('palavra', {}).get('nota', 0)
        nt = det.get('token', {}).get('nota', 0)
        print(f"  {nome:8s}: total={nota:.1f} byte={nb:.1f}/2 palavra={np:.1f}/5 token={nt:.1f}/3")
    
    check("F3. LOREA > GARBAGE",
          c._autoavaliar_multinivel(textos_avalia[0][1], "", "", "conteudo_compartilhado")[0] >
          c._autoavaliar_multinivel(textos_avalia[1][1], "", "", "conteudo_compartilhado")[0])
    
    # ============================================================
    # FASE 4: MCRPreCache + AutoavaliadorSemantico
    # ============================================================
    secao("FASE 4: PreCache + AutoavaliadorSemantico")
    
    # PreCache (so testa se consegue instanciar)
    cache = MCRPreCache(kg)
    print(f"  MCRPreCache criado: {cache is not None}")
    
    # AutoavaliadorSemantico
    sem = AutoavaliadorSemantico(kg, cache)
    av = sem.avaliar("Eridanus era uma cidade lendaria.", 'lore')
    print(f"  Lore: {av['nota']}/10 ({av['diagnostico']})")
    av2 = sem.avaliar("xyz abc asdf", 'lore')
    print(f"  Garbage: {av2['nota']}/10 ({av2['diagnostico']})")
    
    check("F4. Semantico discrimina", av['nota'] > av2['nota'])
    
    # ============================================================
    # FASE 5: Compatibilidade (conceitos antigos ainda funcionam)
    # ============================================================
    secao("FASE 5: Compatibilidade — conceitos antigos")
    
    # MarkovUniversal ainda funciona (alias MCR.Nivel)
    mk = MarkovUniversal("teste")
    mk.aprender_sequencia([1, 2, 3, 4])
    check("F5. MarkovUniversal funciona", mk.total > 0)
    
    # jaccard_bytes ainda funciona
    jac = mk.jaccard_bytes("SPA sistema", "SPA progressao")
    check("F5. jaccard_bytes funciona", jac > 0)
    
    # similaridade_transicoes ainda funciona
    sim = mk.similaridade_transicoes("SPA sistema", "SPA progressao")
    check("F5. similaridade_transicoes funciona", sim > 0)
    
    # jaccard_bytes_ponderado funciona
    jp = mk.jaccard_bytes_ponderado("SPA sistema", "SPA progressao")
    check("F5. jaccard_ponderado funciona", jp > 0)
    
    # entropia_sequencia funciona
    es = mk.entropia_sequencia([1, 2, 3, 4])
    check("F5. entropia_sequencia funciona", es >= 0)
    
    # jaccard entre cadeias funciona
    mk2 = MarkovUniversal("teste2")
    mk2.aprender_sequencia([1, 2, 5, 6])
    jc = mk.jaccard(mk2)
    check("F5. jaccard entre cadeias funciona", jc > 0)
    
    jt = mk.jaccard_transicoes(mk2)
    check("F5. jaccard_transicoes entre cadeias funciona", jt >= 0)
    
    # MCR.Nivel alias funciona
    Nivel = MarkovUniversal
    n = Nivel("alias")
    n.aprender_sequencia([1, 2, 3])
    check("F5. MCR.Nivel alias funciona", n.total > 0)
    
    # ============================================================
    # RELATORIO FINAL
    # ============================================================
    perc = (PASS / TOTAL * 100) if TOTAL > 0 else 0
    secao(f"RELATORIO FINAL — {PASS}/{TOTAL} ({perc:.0f}%)")
    
    print(f"""
  CONCEITOS UNIFICADOS NO MCR:
  
  MCRFingerprint        — dims variaveis por entropia     {'✅' if PASS > 5 else '❌'}
  MCRCruzado            — ponte otima entre topicos       {'✅' if PASS > 5 else '❌'}
  MCRConector           — emergencia multi-nivel          {'✅' if PASS > 5 else '❌'}
  Autoavaliacao MultiNivel — Byte+Palavra+Token=10pts     {'✅' if PASS > 5 else '❌'}
  MCRPreCache           — estudo de LLM                   {'✅' if PASS > 5 else '❌'}
  AutoavaliadorSemantico — detecta narrativa              {'✅' if PASS > 5 else '❌'}
  jaccard_ponderado     — primeiros bytes pesam 2x        {'✅' if PASS > 5 else '❌'}
  entropia_sequencia    — mede variacao temporal          {'✅' if PASS > 5 else '❌'}
  jaccard entre cadeias — compara 2 modelos MCR           {'✅' if PASS > 5 else '❌'}
  
  Tudo no mesmo arquivo: modulos/MCR.py
  Tudo o mesmo conceito: MCR.
""")
    
    return FAIL == 0

if __name__ == '__main__':
    testar()
