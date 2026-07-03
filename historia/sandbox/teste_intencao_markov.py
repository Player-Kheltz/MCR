#!/usr/bin/env python3
"""TESTE: IntentionEngine + Markov — verificação cruzada (v2 unificada).

Importa o léxico v2 do MCR e testa a validação cruzada.
NÃO MODIFICA NADA NO MCR. Só importa módulos existentes.
"""
import sys, os, re, json
from collections import Counter

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts', 'mcr_devia'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))

# Importa OS MÓDULOS EXISTENTES (agora unificados)
from modulos.intention_engine import IntentionEngine
from modulos.lexico_v2 import tokenizar_v2, resumo_tokens, tipos_unicos, verificar_markov, MARKOV_POR_INTENCAO
from modulos.pattern_engine import PatternEngine


# ============================================================
# COMPARAÇÃO v1 vs v2
# ============================================================

def tokenizar_v1(texto):
    """Tokenização ATUAL do PatternEngine (para comparação)."""
    pe = PatternEngine()
    return pe.tokenizar(texto, 'texto')


def resumo_v1(tokens):
    return dict(Counter(t[0] for t in tokens).most_common(10))


# ============================================================
# VERIFICAÇÃO CRUZADA (usa os módulos unificados)
# ============================================================

def verificar_cruzada(frase, intencoes_ie):
    """Compara IntentionEngine com Markov predito."""
    if not intencoes_ie:
        return {
            "frase": frase,
            "erro": "Nenhuma intenção detectada",
            "confianca_final": 0.0,
        }

    cat, params, conf_ie = intencoes_ie[0]
    tipo = params.get('tipo', 'default')

    # 1. Tokeniza com v2 (do léxico unificado)
    tokens_v2 = tokenizar_v2(frase)
    tipos_unicos_v2 = tipos_unicos(tokens_v2)

    # 2. Markov verifica (do léxico unificado)
    markov = verificar_markov(tokens_v2, cat, tipo)

    conf_markov = markov.get("taxa_markov", 0) * markov.get("peso", 1.0)
    conf_final = (conf_ie * 0.5) + (conf_markov * 0.4) + markov.get("bonus", 0) - markov.get("penalidade", 0)
    conf_final = max(0.0, min(1.0, conf_final))

    if conf_final >= 0.75:
        decisao = "✅ CONFIRMADA"
    elif conf_final >= 0.50:
        decisao = "⚠️ DUVIDOSA"
    else:
        decisao = "❌ REJEITADA"

    return {
        "frase": frase[:60],
        "intencao": f"{cat}/{tipo}",
        "conf_ie": round(conf_ie, 3),
        "tokens_v2": tipos_unicos_v2[:10],
        "taxa_markov": markov["taxa_markov"],
        "peso_markov": markov["peso"],
        "hits": markov["hits"],
        "misses": markov["misses"],
        "penalidade": markov["penalidade"],
        "bonus": markov["bonus"],
        "entropia_sugerida": markov["entropia_sugerida"],
        "confianca_final": round(conf_final, 3),
        "decisao": decisao,
    }


# ============================================================
# TESTES
# ============================================================

ENTRADAS = [
    "Crie um NPC Ferreiro em Eridanus",
    "Explique o sistema SPA do MCR",
    "O que e Canary no contexto do MCR?",
    "Crie uma lore sobre a fundacao de Eridanus",
    "Busque a definicao de SPA no codigo",
    "Adicione 'Eridanus = Cidade Inicial' ao arquivo TESTE.md",
    "Implemente um sistema de combate elemental",
    "Revise o arquivo data/npc/ferreiro.lua",
]


def testar():
    print("=" * 90)
    print("  TESTE: IntentionEngine + Léxico V2 + Markov — Verificação Cruzada")
    print("=" * 90)

    ie = IntentionEngine()
    resultados = []

    for frase in ENTRADAS:
        print(f"\n{'─'*90}")
        print(f"  ENTRADA: {frase}")
        print(f"{'─'*90}")

        # IntentionEngine (AGORA usa léxico v2 internamente)
        intencoes = ie.detectar(frase)
        if not intencoes:
            print("  ❌ Nenhuma intenção detectada")
            resultados.append({"frase": frase[:60], "erro": "Sem intenção"})
            continue

        cat, params, conf = intencoes[0]
        print(f"  IE: {cat}/{params.get('tipo','?')} (conf={conf:.3f})")

        # Comparação v1 vs v2
        tokens_v1 = tokenizar_v1(frase)
        tokens_v2 = tokenizar_v2(frase)
        print(f"  v1 (atual): {resumo_v1(tokens_v1)}")
        print(f"  v2 (unif.): {resumo_tokens(tokens_v2)}")
        print(f"  Sequência v2: {tipos_unicos(tokens_v2)[:10]}")

        # Verificação cruzada
        resultado = verificar_cruzada(frase, intencoes)
        resultados.append(resultado)

        if resultado.get('erro'):
            print(f"  ❌ {resultado['erro']}")
        else:
            print(f"  Markov: taxa={resultado['taxa_markov']:.3f} hits={[h[0] for h in resultado['hits']]}"
                  f" bonus={resultado['bonus']} penal={resultado['penalidade']}")
            print(f"  Confiança final: {resultado['confianca_final']:.3f} → {resultado['decisao']}")

    # Tabela final
    print(f"\n\n{'='*90}")
    print(f"  TABELA COMPARATIVA")
    print(f"{'='*90}")
    print(f"\n  {'Entrada':45s} {'Intenção':22s} {'IE':5s} {'Markov':7s} {'Entrop':7s} {'Final':6s} {'Decisão':15s}")
    print(f"  {'-'*45} {'-'*22} {'-'*5} {'-'*7} {'-'*7} {'-'*6} {'-'*15}")

    for r in resultados:
        if r.get('erro'):
            print(f"  {r['frase'][:45]:45s} {'ERRO':22s} {'?':5s} {'?':7s} {'?':7s} {'?':6s} {'❌':15s}")
        else:
            print(f"  {r['frase'][:45]:45s} {r['intencao'][:22]:22s} "
                  f"{r['conf_ie']:.2f}  {r['taxa_markov']:.3f}  "
                  f"{r['entropia_sugerida']:.3f}  {r['confianca_final']:.3f}  {r['decisao']:15s}")

    print(f"\n{'='*90}")
    print(f"  LEGENDA: confiança final = IE(50%) + Markov(40%) + bônus - penalidade")
    print(f"  Markov = similaridade entre tokens reais e sequência esperada para intenção")
    print(f"  Entropia sugerida = 1.0 - taxa_markov - bonus + penalidade (ideal < 0.3)")
    print(f"  ✅ >= 0.75 | ⚠️ >= 0.50 | ❌ < 0.50")
    print(f"{'='*90}")

    return resultados


if __name__ == '__main__':
    resultados = testar()

    out_path = os.path.join(BASE, 'sandbox', 'test_output', 'resultado_v2_unificado.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"\nResultado salvo: {out_path}")
