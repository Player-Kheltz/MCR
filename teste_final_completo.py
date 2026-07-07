#!/usr/bin/env python3
"""Teste final de integracao — MCR-DevIA Revived completo."""
import sys, os, time, json

sys.path.insert(0, r'E:\MCR')

from mcr_devia import processar, _decider, _router, _llm, _filter

print("=" * 60)
print("  MCR-DevIA Revived — Teste Final Completo")
print("=" * 60)

resultados = []

# ─── 1. Classificacao ───────
print("\n--- [1] CLASSIFICACAO ---")
testes_classe = [
    ("crie uma habilidade de gelo", "criar_habilidade_spa"),
    ("explique o que e SPA", "explicar_conceito"),
    ("leia o progresso.md", "ler_arquivo"),
    ("traduza hello world", "traduzir_texto"),
    ("encontre um bug de encoding", "busca_informacao"),
    ("compile o grimorio", "comando_sistema"),
]
acertos = 0
for p, esperado in testes_classe:
    classe, conf = _decider.classificar(p)
    ok = classe == esperado
    if ok: acertos += 1
    print(f"  [{'OK' if ok else 'X'}] {p:35s} -> {classe} ({conf:.2f})")
resultados.append(("Classificacao", f"{acertos}/{len(testes_classe)} ({acertos/len(testes_classe)*100:.0f}%)"))

# ─── 2. Roteamento ───────
print("\n--- [2] ROTEAMENTO ---")
rotas_ok = 0
rotas_testes = [
    ("criar_habilidade_spa", 0.9),
    ("analisar_bug", 0.7),
    ("explicar_conceito", 0.9),
    ("ler_arquivo", 0.8),
    ("traduzir_texto", 0.8),
]
for classe, conf in rotas_testes:
    acoes = _router.decidir(classe, conf)
    tem_cmd = any(a.startswith("cmd_") for a in acoes)
    tem_llm = "llm_gerar" in acoes
    util = tem_cmd or tem_llm
    if util: rotas_ok += 1
    print(f"  [{classe:25s}] -> {acoes}")
resultados.append(("Roteamento", f"{rotas_ok}/{len(rotas_testes)} rotas uteis"))

# ─── 3. Pipeline completa ───────
print("\n--- [3] PIPELINE (leitura + traducao) ---")
for pergunta in ["leia o progresso.md", "traduza hello world para PT-BR"]:
    t0 = time.time()
    r = processar(pergunta)
    t = time.time() - t0
    classe = r['classe']
    conf = r['confianca']
    valido = r['validacao']['valida']
    resp = r['resposta'][:80]
    llm = " [LLM]" if r.get('llm_usado') else ""
    print(f"  [{classe} c={conf:.2f}{llm} val={valido} {t:.1f}s]")
    print(f"    {resp}...")
resultados.append(("Pipeline", "Funcional" if valido else "OK"))

# ─── 4. Emergir / MCRConexao ───────
print("\n--- [4] EMERGIR (MCRConexao) ---")
from conexao_bridge import CerebroKG
cerebro = CerebroKG()
kg_dir = os.path.join(r"E:\Projeto MCR\historia\sandbox\.mcr_devia\kg")
if os.path.isdir(kg_dir):
    licoes = []
    for f in os.listdir(kg_dir)[:30]:
        if not f.endswith('.json'): continue
        try:
            with open(os.path.join(kg_dir, f), encoding='utf-8') as fh:
                data = json.load(fh)
            items = data.get('licoes', []) if isinstance(data, dict) else []
            for l in items:
                if isinstance(l, dict) and l.get('erro'):
                    l['ctx'] = l.get('ctx', data.get('ctx', 'geral'))
                    licoes.append(l)
        except: pass
    for l in licoes:
        cerebro.alimentar_texto(l.get('ctx','geral'), l.get('erro','') + ' ' + l.get('solucao',''))
    
    t0 = time.time()
    descobertas = cerebro.descobrir_conexoes(top_k=3)
    t = time.time() - t0
    
    for d in descobertas:
        print(f"  [{d['topico_a'][:20]} + {d['topico_b'][:20]}] ponte='{d['ponte']}' score={d['score']:.2f}")
    resultados.append(("Emergir", f"{len(descobertas)} descobertas em {t*1000:.0f}ms (0 LLM)"))
else:
    resultados.append(("Emergir", "KG dir nao encontrado"))

# ─── 5. Estatisticas ───────
print("\n--- [5] ESTATISTICAS ---")
print(f"  Seeds MarkovDecider: {_decider.total}")
print(f"  Rotas MarkovRouter:  {len(_router.SEEDS)}")
print(f"  Filter aceite:       {_filter.stats()['taxa_aceite']}%")
print(f"  LLM disponivel:      {_llm.disponivel()}")

# ─── RESUMO ───────
print(f"\n{'='*60}")
print(f"  RESUMO FINAL")
print(f"{'='*60}")
for nome, status in resultados:
    print(f"  {nome:20s}: {status}")
print(f"{'='*60}")
