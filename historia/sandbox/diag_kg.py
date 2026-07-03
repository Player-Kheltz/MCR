#!/usr/bin/env python3
"""Diagnostico do KG — por que nao expande?"""
import sys, os, json
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.kg import KnowledgeGraph
kg = KnowledgeGraph()

licoes = kg._get_licoes()
print(f'Total de lessons: {len(licoes)}')

# Distribuicao por ctx
ctxs = Counter(l.get('ctx','sem_ctx') for l in licoes)
print('\n=== DISTRIBUICAO POR CTX (top 25) ===')
for ctx, count in ctxs.most_common(25):
    print(f'  {ctx:35s}: {count}')

# Lessons que sao JSON
json_lessons = [l for l in licoes if l.get('solucao','').strip().startswith('{')]
print(f'\nLessons com JSON: {len(json_lessons)}')
if json_lessons:
    print(f'  Exemplo: {json_lessons[0].get("solucao","")[:120]}')

# Lessons vazias
vazias = [l for l in licoes if len(l.get('solucao','').strip()) < 20]
print(f'Lessons vazias/sem solucao: {len(vazias)}')

# Duplicatas
solucoes = [l.get('solucao','') for l in licoes if l.get('solucao','')]
unicas = len(set(solucoes))
print(f'Solucoes unicas: {unicas}/{len(solucoes)} ({len(solucoes)-unicas} duplicadas)')

# Lessons recentes
recentes = [l for l in licoes if l.get('timestamp', 0) > 0]
recentes.sort(key=lambda x: -x.get('timestamp', 0))
print(f'\n=== ULTIMAS 15 LESSONS CRIADAS ===')
for l in recentes[:15]:
    ts = l.get('timestamp', 0)
    try:
        data = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
    except:
        data = '?'
    erro = l.get('erro','')[:60]
    ctx = l.get('ctx','?')
    sol = l.get('solucao','')[:40].replace('\n',' ')
    print(f'  [{data}] ctx={ctx:25s} erro={erro} | {sol}')

# Topicos que mais tem lessons
print(f'\n=== CTX COM MAIS LESSONS (pool de conhecimento) ===')
for ctx, count in ctxs.most_common(10):
    # Amostra 1 lesson de cada
    exemplo = [l for l in licoes if l.get('ctx') == ctx]
    if exemplo:
        sol = exemplo[0].get('solucao','')[:60].replace('\n',' ')
        print(f'  {ctx:30s} ({count:3d} lessons): {sol}')

# Lessons que poderiam alimentar o MCR
uteis = [l for l in licoes 
         if l.get('solucao','') 
         and len(l.get('solucao','')) > 50
         and not l.get('solucao','').strip().startswith('{')
         and not l.get('inactive')]
print(f'\n=== LESSONS UTEIS (solucao > 50 chars, sem JSON) ===')
print(f'  Total: {len(uteis)} de {len(licoes)}')
