#!/usr/bin/env python3
"""Teste Conselho V5 - 2 rodadas + Revisor."""
import sys; sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from kernel import MCRKernel
from modulos.conselho import Conselho
import context_crew

k = MCRKernel(); k.inicializar()
ctx_crew = context_crew.ContextCrew()
c = Conselho(kg=k.contexto.get('kg'), ia=k.contexto.get('ia'), ctx_crew=ctx_crew, max_rodadas=2)

print('CONSELHO V5 - 2 RODADAS + REVISOR')
print('='*60)
r = c.deliberar('Crie uma historia completa para cidade de Eridanus em Tibia')
print('='*60)
print()
print('VEREDITO FINAL (coeso):')
v = r.get('veredito', '')
print(v[:500])
tt = r.get('tempo_total', 0)
print(f'\nTempo: {tt}s | Rodadas: {r.get("rodadas", 0)}')
