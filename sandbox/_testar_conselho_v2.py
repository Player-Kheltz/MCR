#!/usr/bin/env python3
"""Teste do Conselho V2 com ferramentas reais."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from kernel import MCRKernel
from modulos.conselho import Conselho

k = MCRKernel()
k.inicializar()
conselho = Conselho(kg=k.contexto.get('kg'), ia=k.contexto.get('ia'))

print('='*60)
print('CONSELHO V2 - Pergunta de ARQUITETURA')
print('='*60)
r = conselho.deliberar('Qual a melhor arquitetura para o MCR-DevIA?')
print('='*60)
print('VEREDITO FINAL:')
print(r.get('veredito', 'sem veredito')[:400])
print(f'\nTempo total: {r.get("tempo_total", 0)}s')
print(f'Personalidades: {r.get("personalidades", 0)}')
print('='*60)
