#!/usr/bin/env python3
"""PROTÓTIPO: AprendizDePadroes UNIVERSAL (1 método, tokenizar_universal).

NÃO MODIFICA NADA NO MCR. Só importa módulos existentes.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.aprendiz_de_padroes import AprendizDePadroes


def executar():
    print("=" * 80)
    print("  APRENDIZ DE PADRÕES — UNIVERSAL (1 método substitui 6)")
    print("=" * 80)
    
    pe = PatternEngine()
    aprendiz = AprendizDePadroes(pe=pe)
    
    # ============================================================
    # TESTE 1: Dados arbitrários (qualquer formato)
    # ============================================================
    print(f"\n{'─'*80}")
    print("  [TESTE 1] Dados arbitrários — bytes PNG")
    print(f"{'─'*80}")
    
    png_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100 + b'IEND'
    padroes = aprendiz.estudar_dados(png_bytes, 'bytes_teste')
    print(f"  → {len(padroes)} padrões encontrados")
    for p in padroes[:3]:
        print(f"    [{p.get('conf',0):.2f}] {p.get('tipo','?')}: {str(p.get('n_grama',p.get('termos','')))[:60]}")
    
    # ============================================================
    # TESTE 2: string arbitrária
    # ============================================================
    print(f"\n{'─'*80}")
    print("  [TESTE 2] Dados arbitrários — frase")
    print(f"{'─'*80}")
    
    padroes = aprendiz.estudar_dados(
        "Crie um NPC Ferreiro em Eridanus. Explique o sistema SPA do MCR. "
        "Crie uma lore sobre a fundacao de Eridanus.",
        'frase_teste'
    )
    print(f"  → {len(padroes)} padrões encontrados")
    for p in padroes[:5]:
        print(f"    [{p.get('conf',0):.2f}] {p.get('tipo','?')}: {str(p.get('n_grama',p.get('termos','')))[:60]}")
    
    # ============================================================
    # TESTE 3: lista arbitrária
    # ============================================================
    print(f"\n{'─'*80}")
    print("  [TESTE 3] Dados arbitrários — lista de dicts")
    print(f"{'─'*80}")
    
    dados_lista = [
        {"request": "Crie um NPC", "sucesso": True, "nota": 8},
        {"request": "Crie um NPC Ferreiro", "sucesso": False, "nota": 3},
        {"request": "Explique SPA", "sucesso": True, "nota": 9},
        {"request": "Crie um NPC Guia", "sucesso": False, "nota": 4},
        {"request": "Explique SHC", "sucesso": True, "nota": 10},
    ]
    padroes = aprendiz.estudar_dados(dados_lista, 'lista_teste')
    print(f"  → {len(padroes)} padrões encontrados")
    for p in padroes[:5]:
        print(f"    [{p.get('conf',0):.2f}] {p.get('tipo','?')}: {str(p.get('n_grama',p.get('termos','')))[:60]}")
        if p.get('taxa_risco'):
            print(f"      ⚠️ RISCO: {p.get('taxa_risco'):.0%}")
    
    # ============================================================
    # TESTE 4: Fontes REAIS (como antes, mas 1 método)
    # ============================================================
    print(f"\n{'─'*80}")
    print("  [TESTE 4] Fontes REAIS do MCR-DevIA (estudar_tudo)")
    print(f"{'─'*80}")
    
    resultados = aprendiz.estudar_tudo()
    
    if not resultados:
        print("  → Nenhuma fonte encontrada (sandbox vazio?)")
    else:
        for fonte, qtd in sorted(resultados.items()):
            print(f"  {fonte}: {qtd} padrões")
    
    # ============================================================
    # RELATÓRIO FINAL
    # ============================================================
    print(f"\n\n{'='*80}")
    print("  RELATÓRIO FINAL")
    print(f"{'='*80}")
    print(f"\n  Total padrões: {len(aprendiz._padroes_encontrados)}")
    
    por_tipo = {}
    for p in aprendiz._padroes_encontrados:
        t = p.get('tipo', '?')
        por_tipo[t] = por_tipo.get(t, 0) + 1
    
    print(f"\n  --- Por tipo ---")
    for t, n in sorted(por_tipo.items(), key=lambda x: -x[1]):
        print(f"    {t}: {n}")
    
    # Simula IE carregando
    conf_altas = [p for p in aprendiz._padroes_encontrados if p.get('conf', 0) >= 0.7]
    print(f"\n  IE receberia: {len(conf_altas)} padrões com conf >= 0.7")
    print(f"  ({len(aprendiz._padroes_encontrados) - len(conf_altas)} padrões com conf < 0.7 viram candidatos)")
    
    print(f"\n{'='*80}")
    print("  PROTÓTIPO CONCLUÍDO")
    print(f"  1 método universal substitui 6 especializados")
    print(f"  PE.tokenizar_universal() + AprendizDePadroes._estudar_dados()")
    print(f"  Qualquer formato: str, bytes, list, dict")
    print(f"{'='*80}")


if __name__ == '__main__':
    executar()
