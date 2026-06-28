#!/usr/bin/env python3
"""Documenta o que o MCR-DevIA aprendeu neste ciclo, usando fontes reais."""
import sys, os, json
sys.path.insert(0, r"E:\Projeto MCR\scripts\mcr_devia")
os.chdir(r"E:\Projeto MCR\scripts\mcr_devia")

import contextlib
with open(os.devnull, 'w') as devnull:
    old = sys.stdout
    sys.stdout = devnull
    try:
        from mcr_devia import KnowledgeGraph
        from modulos import memoria_conselho as mem
        kg = KnowledgeGraph()
        lessons = kg.buscar("MCR-DevIA aprendizado melhoria ciclo", max_r=25)
    finally:
        sys.stdout = old

print("=" * 65)
print("  O QUE O MCR-DEVIA APRENDEU NESTE CICLO")
print("  (Fonte: KG + Memoria do Conselho)")
print("=" * 65)

print(f"\nLessons encontradas: {len(lessons)}")
print("\n--- PRINCIPAIS APRENDIZADOS ---")
vistos = set()
for l in lessons:
    erro = l.get("erro", "")
    if erro and erro not in vistos:
        vistos.add(erro)
        sol = l.get("solucao", "")[:150]
        ctx = l.get("ctx", "")
        print(f"\n  [{ctx}] {erro[:100]}")
        if sol:
            print(f"    -> {sol}")

print("\n\n--- MEMORIA DO CONSELHO (score acumulado) ---")
stats = mem.estatisticas()
for nome, s in sorted(stats.items()):
    if s["total"] > 0:
        print(f"  {nome}: {s['total']} memorias, score_medio={s['score_medio']}")

print("\n\n--- MUDANCAS IMPLEMENTADAS NESTE CICLO ---")
mudancas = [
    "1. Watchdog com indice invertido (51.103 palavras indexadas)",
    "2. ContextCrew usa indice_watchdog.json em vez de varrer disco",
    "3. Comandos intencao/orquestrar/processar viram alias para perguntar",
    "4. Supervisor com fase 0: ferramentas (grep, compile) antes da IA",
    "5. Auto-revisor heuristico (3 regras, sem FAST, sem lista fixa)",
    "6. Respostas COMPLETAS (removido [:2000])",
    "7. JSON IPC como padrao de comunicacao",
    "8. Pre-verificacao KG: se < 2 lessons, weblearn pesquisa automaticamente",
]
for m in mudancas:
    print(f"  {m}")
