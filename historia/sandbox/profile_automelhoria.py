#!/usr/bin/env python3
"""Profile MCRAutoMelhoria — 39 acoes."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print('Testando MCRAutoMelhoria...', flush=True)
t0 = time.time()
from modulos.MCR import MCRAutoMelhoria
t1 = time.time()
print(f'  Import: {t1-t0:.1f}s', flush=True)

melhoria = MCRAutoMelhoria()
t2 = time.time()
print(f'  Init: {t2-t1:.1f}s', flush=True)

resultado = melhoria.executar()
t3 = time.time()
print(f'  Executar: {t3-t2:.1f}s', flush=True)
print(f'  Acoes: {resultado.get("acoes", 0)}', flush=True)
print(f'  Total: {t3-t0:.1f}s', flush=True)
