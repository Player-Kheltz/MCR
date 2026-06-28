#!/usr/bin/env python3
"""Teste Conselho V7 - Honorarios CRIADOS sob demanda."""
import sys; sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from kernel import MCRKernel
from modulos.conselho import Conselho

k = MCRKernel(); k.inicializar()
c = Conselho(kg=k.contexto.get('kg'), ia=k.contexto.get('ia'))

print('='*60)
print('CONSELHO V7 - Honorarios CRIADOS sob demanda')
print('='*60)
r = c.deliberar('Crie uma historia para Eridanus')
print('='*60)
v = r.get('veredito', '')
print('VEREDITO:', v[:400])
print(f'Tempo: {r.get("tempo_total",0)}s')
print(f'Honorarios criados: {r.get("honorarios_criados", [])}')
print('='*60)
