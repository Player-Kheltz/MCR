#!/usr/bin/env python3
"""Teste rapido de estabilizacao — 5 perguntas, metricas basicas."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'devia', 'kernel'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 1. Teste do MarkovDecider + Cache
print('=' * 55)
print('  TESTE DE ESTABILIZACAO — PIPELINE INTEGRADO')
print('=' * 55)
print()

print('[1/3] Testando MarkovDecider...')
from mcr_devia_v2 import MarkovDecider
md = MarkovDecider()
perguntas = [
    "O que significa SPA",
    "crie um npc ferreiro",
    "ola tudo bem",
    "explique entropia de shannon",
]
for p in perguntas:
    classe, conf = md.classificar(p)
    rota = 'CACHE' if conf > 0.3 else 'LLM'
    print(f'  {p:35s} -> {classe:20s} conf={conf:.3f} rota={rota}')

print()
print('[2/3] Testando Cache Hierarquico...')
from mcr.cache_hierarquico import CacheHierarquico
cache = CacheHierarquico()

for p in perguntas:
    t0 = time.time()
    resp = cache.buscar(p)
    t = (time.time() - t0) * 1000
    if resp:
        print(f'  CACHE HIT  ({t:.1f}ms): {p}')
    else:
        print(f'  CACHE MISS ({t:.1f}ms): {p}')

# Cache Hit apos aprender
print('  Aprendendo respostas no cache...')
cache.aprender("O que significa SPA", "SPA e o Sistema de Progressao do Aventureiro.", "explicar_conceito")
cache.aprender("crie um npc ferreiro", "Use Game.createNpcType para criar NPCs.", "criar_npc")
cache.aprender("ola tudo bem", "Ola! Tudo bem sim.", "conversa")

for p in perguntas:
    t0 = time.time()
    resp = cache.buscar(p)
    t = (time.time() - t0) * 1000
    if resp:
        print(f'  CACHE HIT  ({t:.1f}ms): {p}')
    else:
        print(f'  CACHE MISS ({t:.1f}ms): {p}')

print()
print('[3/3] Metricas finais:')
print(f'  Cache: {cache.estatisticas()}')
print()
print('=' * 55)
print('  TESTE CONCLUIDO — Pipeline operacional')
print('=' * 55)
