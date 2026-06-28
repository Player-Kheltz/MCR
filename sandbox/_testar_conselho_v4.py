#!/usr/bin/env python3
"""Teste Conselho V4 - Personalidades em paralelo."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from kernel import MCRKernel
from modulos.conselho import Conselho
import context_crew

k = MCRKernel()
k.inicializar()
ctx_crew = None
try:
    ctx_crew = context_crew.ContextCrew()
    print('[OK] ContextCrew')
except: print('[AVISO] Sem ContextCrew')

c = Conselho(kg=k.contexto.get('kg'), ia=k.contexto.get('ia'), ctx_crew=ctx_crew)

print('='*60)
print('CONSELHO V4 - PARALELO')
print('='*60)
t0 = time.time()
r = c.deliberar('Qual a melhor arquitetura para o MCR-DevIA?')
total = time.time() - t0

print('='*60)
print(f'Tempo REAL: {total:.1f}s (vs 38.5s do V3 sequencial)')
print(f'Tempo do conselho: {r.get("tempo_total",0)}s')
tt = r.get('tempo_total', 1)
print(f'Ganho: {(38.5/tt)*100:.0f}% mais rapido')
v = str(r.get('veredito', ''))
print(f'Veredito: {v[:300]}')
print('='*60)
