#!/usr/bin/env python3
"""Diagnostico final de qualidade."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.kg import KnowledgeGraph
from collections import Counter
from modulos.MCR import _get_doc_index

# 1. DocIndex performance
print('=== MCRDocIndex ===')
idx = _get_doc_index()
t0 = time.time()
n = idx.indexar()
t_idx = time.time() - t0
print(f'Indexou {n} docs em {t_idx:.3f}s')

for termo in ['Eridanus', 'SPA', 'NPC']:
    t0 = time.time()
    res = idx.buscar(termo)
    tb = time.time() - t0
    print(f'  "{termo}": {len(res)} docs em {tb*1000:.1f}ms')
    if res:
        for r in res[:2]:
            print(f'    {r["caminho"]}')

# 2. KG state
print()
print('=== KG ===')
kg = KnowledgeGraph()
licoes = kg._get_licoes()
uteis = [l for l in licoes 
         if l.get('solucao','') and len(l.get('solucao','')) > 50
         and not l.get('solucao','').startswith('{')
         and not l.get('inactive')]
ctxs = Counter(l.get('ctx','?') for l in licoes)
print(f'Total: {len(licoes)}')
print(f'Uteis: {len(uteis)} ({len(uteis)/max(len(licoes),1)*100:.0f}%)')
print()

# Topo ctxs
print('Top 10 ctxs:')
for ctx, count in ctxs.most_common(10):
    print(f'  {ctx:30s}: {count}')

# Fuel e Gap
for prefixo in ['fuel_', 'gap_']:
    total = sum(1 for l in licoes if l.get('ctx','').startswith(prefixo))
    if total > 0:
        print(f'{prefixo}: {total} lessons')

# 3. Resultado real
print()
print('=== MCRMestreV2 ===')
from modulos.MCR import MCRMestreV2, MCRBridge
bridge = MCRBridge()
bridge.descobrir()
mestre = MCRMestreV2(bridge)
t0 = time.time()
res = mestre.processar('Explique o sistema SPA do MCR')
t = time.time() - t0
resp = res['resposta'][:100]
print(f'Resposta: {resp}')
print(f'Nota: {res["nota"]}/10')
print(f'Tempo: {t:.1f}s')

print()
print('=== MCRPergunta ===')
from modulos.MCR import MCRPergunta
mp = MCRPergunta()
t0 = time.time()
res2 = mp.perguntar('O que e Eridanus', max_tokens=30)
t2 = time.time() - t0
print(f'Resposta: {res2["resposta"][:100]}')
print(f'Nota: {res2["nota"]}/10')
print(f'Tempo: {t2:.1f}s')
