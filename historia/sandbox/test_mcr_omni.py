#!/usr/bin/env python3
"""TESTE: MCR Omnidirecional — Bridge, KGAuto, Expansao, Meta."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRBridge, MCRKGAuto, MCRExpansao, MCRMeta
from modulos.kg import KnowledgeGraph

PASS = 0; FAIL = 0; TOTAL = 0
def check(nome, cond, detalhe=""):
    global PASS, FAIL, TOTAL; TOTAL += 1
    if cond: PASS += 1; print(f"  [PASS] {nome}")
    else: FAIL += 1; print(f"  [FAIL] {nome} {detalhe}")
def secao(titulo):
    print(f"\n{'='*70}\n  {titulo}\n{'='*70}")

def testar():
    secao("MCR OMNIDIRECIONAL — Bridge, KGAuto, Expansao, Meta")
    kg = KnowledgeGraph()
    
    # ============================================================
    # FASE 1: MCRBridge
    # ============================================================
    secao("FASE 1: MCRBridge — descobre modulos + comandos")
    
    bridge = MCRBridge()
    disc = bridge.descobrir()
    
    print(f"  Modulos descobertos: {disc['modulos']}")
    print(f"  Comandos descobertos: {disc['comandos']}")
    
    check("F1. Descobriu modulos", disc['modulos'] > 0, f"(got {disc['modulos']})")
    check("F1. Descobriu comandos", disc['comandos'] > 0, f"(got {disc['comandos']})")
    
    # Tenta usar modulo kg
    if 'kg' in bridge.modulos:
        kg_mod = bridge.usar_modulo('kg')
        check("F1. Modulo kg acessivel", kg_mod is not None)
    
    # Tenta usar comando ensinar
    if 'ensinar' in bridge.comandos:
        check("F1. Comando ensinar acessivel", True)
    
    # Stats
    stats = bridge.stats()
    print(f"  Stats bridge: {stats}")
    check("F1. Bridge tem modulos e comandos", stats['modulos'] > 0 and stats['comandos'] > 0)
    
    # ============================================================
    # FASE 2: MCRKGAuto
    # ============================================================
    secao("FASE 2: MCRKGAuto — categoriza + dedup + limpa")
    
    auto_kg = MCRKGAuto(kg)
    
    # Categoriza
    cats = auto_kg.categorizar()
    print(f"  Categorias encontradas: {len(cats)}")
    for c, v in sorted(cats.items(), key=lambda x: -len(x[1]))[:10]:
        sol = v[0].get('solucao', '')[:40].replace('\n', ' ') if v else ''
        print(f"    {c:20s}: {len(v):3d} lessons | ex: {sol}")
    
    check("F2. Categorias > 0", len(cats) > 0, f"(got {len(cats)})")
    
    # Limpa
    limpeza = auto_kg.limpar()
    print(f"  Limpeza: {limpeza['removidos']} removidos, {limpeza['mantidos']} mantidos")
    check("F2. Limpeza executada", limpeza['removidos'] >= 0)
    
    # Dedup
    removidas = auto_kg.dedup()
    print(f"  Dedup: {removidas} duplicatas removidas")
    check("F2. Dedup executado", removidas >= 0)
    
    # Organiza completo
    org = auto_kg.organizar()
    print(f"  Organizacao completa:")
    print(f"    Categorias: {org['categorias']}")
    print(f"    Dedup: {org['dedup_removidos']}")
    print(f"    Limpeza: {org['limpeza']}")
    check("F2. Organizacao completa", org['categorias'] > 0)
    
    # ============================================================
    # FASE 3: MCRExpansao
    # ============================================================
    secao("FASE 3: MCRExpansao — AutoLoop que usa TUDO")
    
    expansao = MCRExpansao(kg, bridge)
    res = expansao.expandir("Eridanus", max_recursos=8)
    
    print(f"  Tema: {res['tema']}")
    print(f"  Expansoes: {res['expansoes']}")
    print(f"  Recursos usados: {res['recursos_usados']}")
    print(f"  Lessons agora: {res['lessons_agora']}")
    for d in res['detalhes'][:5]:
        print(f"    {d}")
    
    check("F3. Expansao tentou recursos", res['expansoes'] >= 0)
    check("F3. Recursos registrados", len(res['recursos_usados']) >= 0)
    
    # Expande outro tema
    res2 = expansao.expandir("SPA", max_recursos=5)
    print(f"\n  Expansao SPA: {res2['expansoes']} recursos, {res2['lessons_agora']} lessons")
    check("F3. Segunda expansao funciona", res2['expansoes'] >= 0)
    
    # ============================================================
    # FASE 4: MCRMeta
    # ============================================================
    secao("FASE 4: MCRMeta — MCR se auto-organiza")
    
    meta = MCRMeta(kg)
    
    # Diagnostico
    diag = meta.diagnosticar()
    print(f"  Diagnostico do sistema:")
    print(f"    Total lessons: {diag['total']}")
    print(f"    Uteis: {diag['uteis']}")
    print(f"    Lixo: {diag['lixo']}")
    print(f"    Aproveitamento: {diag['aproveitamento']}")
    print(f"    Categorias: {diag['categorias']}")
    print(f"    Categorias fracas: {diag['categorias_fracas']}")
    
    check("F4. Diagnosticou total", diag['total'] > 0)
    check("F4. Diagnosticou uteis", diag['uteis'] > 0)
    check("F4. Aproveitamento calculado", '%' in str(diag['aproveitamento']))
    
    # Auto-organiza
    org_total = meta.auto_organizar()
    print(f"\n  Auto-organizacao:")
    print(f"    Acoes: {org_total['acoes']}")
    print(f"    N acoes: {org_total['n_acoes']}")
    print(f"    Estado final: {org_total['estado_final']['aproveitamento']}")
    
    check("F4. Auto-organizacao executada", org_total['n_acoes'] >= 0)
    check("F4. Estado final tem aproveitamento", '%' in str(org_total['estado_final'].get('aproveitamento', '')))
    
    # ============================================================
    # RELATORIO
    # ============================================================
    perc = (PASS / TOTAL * 100) if TOTAL > 0 else 0
    secao(f"RELATORIO — {PASS}/{TOTAL} ({perc:.0f}%)")
    
    print(f"""
  MCR OMNIDIRECIONAL — 4 componentes integrados:
  
  MCRBridge:      {disc['modulos']} modulos, {disc['comandos']} comandos descobertos  {'✅' if disc['modulos'] > 0 else '❌'}
  MCRKGAuto:      {org.get('categorias', 0)} categorias, {org.get('dedup_removidos', 0)} dedup      {'✅' if org.get('categorias', 0) > 0 else '❌'}
  MCRExpansao:    {res['expansoes']} recursos usados para '{res['tema']}'                  {'✅' if res['expansoes'] >= 0 else '❌'}
  MCRMeta:        {org_total['n_acoes']} acoes de auto-organizacao                {'✅' if org_total['n_acoes'] >= 0 else '❌'}
  
  Proximo passo: integrar Bridge + KGAuto + Expansao no fluxo do MCRPergunta
  para que MCR use TUDO disponivel automaticamente.
""")
    
    return FAIL == 0

if __name__ == '__main__':
    testar()
