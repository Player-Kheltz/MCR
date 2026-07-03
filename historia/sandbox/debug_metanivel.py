#!/usr/bin/env python3
"""Debug do MCRMetaNivel."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRMetaNivel

meta = MCRMetaNivel()
entrada = 'Explique o sistema SPA do MCR'.encode('utf-8')

print('1. CRIACAO')
print(f'  Niveis base: {len(meta.niveis)}')
print(f'  Ordem: {meta._ordem}')

print()
print('2. ALIMENTACAO')
meta.alimentar(entrada)
diag = meta.diagnosticar()
print(f'  Niveis: {diag["n_niveis"]}')
print(f'  Ordem: {diag.get("ordem", [])}')
print(f'  Energia: {diag.get("energia_total", 0)}')

print()
print('3. STATS POR NIVEL')
for nome, stats in diag.get('stats', {}).items():
    print(f'  {nome}:')
    for k, v in stats.items():
        print(f'    {k}: {v}')

print()
print('4. AUTO-EXPANSAO')
for i in range(5):
    n = meta.auto_expandir(max_niveis=10)
    if n == 0:
        print(f'  Ciclo {i+1}: maximo atingido')
        break
    diag2 = meta.diagnosticar()
    print(f'  Ciclo {i+1}: {diag2["n_niveis"]} niveis - {diag2["ordem"]}')

print()
print('5. STATS FINAIS')
diag3 = meta.diagnosticar()
for nome, stats in diag3.get('stats', {}).items():
    print(f'  {nome}: ent={stats["entropia"]} raio={stats["raio"]} trans={stats["estados"]} conexoes={stats["conexoes"]}')
