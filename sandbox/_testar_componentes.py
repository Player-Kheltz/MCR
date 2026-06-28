#!/usr/bin/env python3
"""Teste Conselho com componentes pre-gerados."""
import sys; sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from kernel import MCRKernel
from modulos.conselho import Conselho
k = MCRKernel(); k.inicializar()
c = Conselho(kg=k.contexto.get('kg'), ia=k.contexto.get('ia'))

print('CONSELHO COM COMPONENTES PRE-GERADOS')
print('='*60)
r = c.deliberar('Conte uma historia sobre Eridanus')
print('='*60)
v = r.get('veredito', '')
print('VEREDITO:', v[:500])
print(f'\nTempo: {r.get("tempo_total",0)}s')
