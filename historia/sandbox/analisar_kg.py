#!/usr/bin/env python3
"""Analisa distribuicao de qualidade do KG."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRKGAuto, _get_kg

kg = _get_kg()
licoes = kg._get_licoes()

# Distribuicao de qualidade
import collections as cl
buckets = cl.Counter()
for l in licoes:
    sol = l.get('solucao', '')
    q = MCRKGAuto._classificar_qualidade(sol)
    bucket = int(q * 10) * 10
    buckets[f'{bucket}%'] += 1

print('Distribuicao de qualidade:')
for k in sorted(buckets):
    print(f'  {k}: {buckets[k]}')

# Amostras de cada faixa
print('\nAmostras de qualidade < 0.5:')
for l in licoes:
    sol = l.get('solucao', '')
    q = MCRKGAuto._classificar_qualidade(sol)
    if q < 0.5:
        ctx = l.get('ctx', '?')
        print(f'  q={q:.1f} ctx={ctx} sol={str(sol)[:80]}')
