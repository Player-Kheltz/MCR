#!/usr/bin/env python3
"""Teste de tempo das correcoes."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRAutoStart

# Forca cache a None
MCRAutoStart._cache_checksum = None

print('1a execucao (deve fazer dedup real)...')
t0 = time.time()
r = MCRAutoStart.iniciar()
t = time.time() - t0
print(f'Tempo: {t:.1f}s')
print(f'Acoes: {r.get("acoes", [])[:3]}')

if t < 30:
    print()
    print('2a execucao (deve ser cache hit)...')
    t0 = time.time()
    r2 = MCRAutoStart.iniciar()
    t2 = time.time() - t0
    print(f'Tempo: {t2:.1f}s')
    print(f'Acoes: {r2.get("acoes", [])[:3]}')
    if 'cache_hit' in r2.get('acoes', []):
        print(f'CACHE FUNCIONOU! Ganho: {t/t2:.0f}x')
    else:
        print('Cache NAO funcionou')
else:
    print('Timeout: >30s')
