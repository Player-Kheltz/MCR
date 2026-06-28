#!/usr/bin/env python3
"""Teste Conselho V6 - Fixas + Honorarias + Psicologo."""
import sys; sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from kernel import MCRKernel
from modulos.conselho import Conselho

k = MCRKernel(); k.inicializar()
c = Conselho(kg=k.contexto.get('kg'), ia=k.contexto.get('ia'))

print('='*60)
print('CONSELHO V6 - LORE (com Contador de Historias honorary)')
print('='*60)
r = c.deliberar('Crie uma historia para cidade de Eridanus em Tibia')
print('='*60)
print('VEREDITO:', str(r.get('veredito',''))[:400])
print(f'Tempo: {r.get("tempo_total",0)}s')
print(f'Honorarias: {r.get("honorarias",[])}')
print('='*60)
