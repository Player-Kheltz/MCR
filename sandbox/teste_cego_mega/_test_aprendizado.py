#!/usr/bin/env python3
"""Teste do ciclo de aprendizado do MCR-DevIA.
Executa uma pergunta, verifica scores, re-executa, prova que aprendeu."""
import sys, os, json
sys.path.insert(0, r"E:\Projeto MCR\scripts\mcr_devia")
os.chdir(r"E:\Projeto MCR\scripts\mcr_devia")

from modulos import memoria_conselho as mem
from mcr_devia import KnowledgeGraph
from modulos.ia import IA
from modulos.orquestrador import Orquestrador
from modulos.supervisor import Supervisor
import context_crew as cc

import contextlib
with open(os.devnull, 'w') as devnull:
    old = sys.stdout
    sys.stdout = devnull
    try:
        kg = KnowledgeGraph()
        ia = IA()
        ctx = cc.ContextCrew()
    finally:
        sys.stdout = old

orq = Orquestrador(kg=kg, ia=ia, ctx_crew=ctx)
sup = Supervisor(ia, kg, ctx_crew=ctx, orquestrador=orq, identidade="")

# Limpa cache da Mente para forçar aprendizado real
from modulos.mente import _CACHE_MENTE
_CACHE_MENTE.clear()

print("=" * 70)
print("  TESTE DE APRENDIZADO DO MCR-DevIA")
print("=" * 70)

# --- FASE 1: Estado inicial das memorias ---
print("\n[FASE 1] Estado INICIAL das memorias (antes da pergunta):")
stats_antes = mem.estatisticas()
for nome in ['analista', 'critico', 'revisor_codigo']:
    s = stats_antes.get(nome, {})
    print(f"  {nome}: score_medio={s.get('score_medio', 'N/A')}, total={s.get('total', 0)}")

# --- FASE 2: Primeira execucao ---
print("\n[FASE 2] Executando PRIMEIRA pergunta...")
pergunta1 = "Explique como o ContextCrew busca informacao e sugira 2 melhorias."
resposta1 = sup.perguntar(pergunta1)
tam1 = len(resposta1) if resposta1 else 0
print(f"  Resposta 1: {tam1} chars")

# Verifica scores depois da primeira execucao
stats_meio = mem.estatisticas()
print("\n[FASE 2] Scores APOS primeira execucao:")
for nome in ['analista', 'critico', 'revisor_codigo']:
    antes = stats_antes.get(nome, {}).get('score_medio', 0)
    depois = stats_meio.get(nome, {}).get('score_medio', 0)
    delta = depois - antes
    sinal = "+" if delta > 0 else ""
    print(f"  {nome}: {antes:.1f} -> {depois:.1f} ({sinal}{delta:.1f})")

import time
time.sleep(1)  # Garante timestamp diferente para evitar cache

# Limpa cache novamente para forçar nova geracao
_CACHE_MENTE.clear()

# --- FASE 3: Segunda execucao ---
_CACHE_MENTE.clear()
time.sleep(0.5)
print("\n[FASE 3] Executando SEGUNDA pergunta...")
resposta2 = sup.perguntar(pergunta1)
tam2 = len(resposta2) if resposta2 else 0
print(f"  Resposta 2: {tam2} chars")

# --- FASE 3.5: Terceira execucao ---
_CACHE_MENTE.clear()
time.sleep(0.5)
print("\n[FASE 3.5] Executando TERCEIRA pergunta...")
resposta3 = sup.perguntar(pergunta1)
tam3 = len(resposta3) if resposta3 else 0
print(f"  Resposta 3: {tam3} chars")

# Verifica scores depois da terceira execucao
stats_depois = mem.estatisticas()
print("\n[FASE 3.5] Scores APOS terceira execucao:")
for nome in ['analista', 'critico', 'revisor_codigo']:
    antes = stats_meio.get(nome, {}).get('score_medio', 0)
    depois = stats_depois.get(nome, {}).get('score_medio', 0)
    delta = depois - antes
    sinal = "+" if delta > 0 else ""
    print(f"  {nome}: {antes:.1f} -> {depois:.1f} ({sinal}{delta:.1f})")

# --- FASE 4: Comparacao de qualidade ---
print("\n" + "=" * 70)
print("  COMPARACAO DE QUALIDADE")
print("=" * 70)

# Usa metricas simples para comparar
import re

def metricas(texto):
    if not texto:
        return {"chars": 0, "linhas_codigo": 0, "secoes": 0, "erros": 0}
    blocos = re.findall(r'```(?:python)?\s*\n(.*?)```', texto, re.DOTALL)
    linhas_codigo = sum(len(b.split('\n')) for b in blocos)
    secoes = len(re.findall(r'^[A-Z][A-Z ]+:', texto, re.MULTILINE))
    erros = sum(1 for b in blocos if not compile_wrapper(b))
    return {"chars": len(texto), "linhas_codigo": linhas_codigo, 
            "secoes": secoes, "erros": erros}

def compile_wrapper(codigo):
    try:
        compile(codigo.strip(), '<test>', 'exec')
        return True
    except:
        return False

m1 = metricas(resposta1)
m2 = metricas(resposta2)
m3 = metricas(resposta3)

print(f"\n{'Metrica':<25} {'Resp 1':<12} {'Resp 2':<12} {'Resp 3':<12}")
print("-" * 61)
for k in ['chars', 'linhas_codigo', 'secoes', 'erros']:
    print(f"  {k:<25} {m1[k]:<12} {m2[k]:<12} {m3[k]:<12}")

score1 = m1['chars'] + m1['linhas_codigo'] * 10 - m1['erros'] * 50
score2 = m2['chars'] + m2['linhas_codigo'] * 10 - m2['erros'] * 50
score3 = m3['chars'] + m3['linhas_codigo'] * 10 - m3['erros'] * 50
print(f"\n  Score 1: {score1} | Score 2: {score2} | Score 3: {score3}")

if score3 > score1 and score3 > score2:
    print(f"\n  >>> APRENDIZADO CONFIRMADO! Resposta 3 melhor que 1 e 2")
elif score3 > score1:
    print(f"\n  >>> APRENDIZADO PARCIAL: Resposta 3 melhor que 1")
else:
    print(f"\n  >>> VARIACAO NATURAL (scores estao mudando mas qualidade varia)")

# FASE 5: Verifica se as memorias de alto score foram priorizadas
print("\n" + "=" * 70)
print("  MEMORIAS DE ALTO SCORE (aprendizado acumulado)")
print("=" * 70)
for nome in ['analista', 'critico', 'revisor_codigo']:
    melhores = mem.carregar_melhores(nome, max_entradas=3)
    print(f"\n  {nome.upper()} (top {len(melhores)} de {stats_depois.get(nome, {}).get('total', 0)}):")
    for e in melhores:
        print(f"    score={e.get('score', '?')} | {e.get('observacao', '')[:100]}")

print("\n" + "=" * 70)
print("  TESTE CONCLUIDO")
print("=" * 70)
