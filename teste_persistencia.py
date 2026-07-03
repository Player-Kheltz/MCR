#!/usr/bin/env python3
"""Teste de persistencia do cerebro."""
import os, sys
sys.path.insert(0, r'E:\MCR')
os.chdir(r'E:\MCR')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from MCR_AGI import MCRCuriosidade, CerebroAGI, CACHE_DIR

c = CerebroAGI()
c_path = os.path.join(CACHE_DIR, 'cerebro.json')
if os.path.exists(c_path):
    os.remove(c_path)
    print('Cache limpo')

cur = MCRCuriosidade(c)
r = cur.ciclo()
print(f'Explorou: {r["descobertas"]} descobertas')
c.salvar(c_path)
print(f'Salvo em: {c_path}')

c2 = CerebroAGI()
c2.carregar(c_path)
print(f'Carregado: {len(c2.topicos)} topicos')
assert len(c2.topicos) == len(c.topicos), f'Topicos diferentes: {len(c2.topicos)} vs {len(c.topicos)}'
print('OK: CEREBRO PERSISTIDO')
