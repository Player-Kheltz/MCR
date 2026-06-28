#!/usr/bin/env python3
"""Teste Conselho V3 - Com ContextCrew + WebFetch."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from kernel import MCRKernel
from modulos.conselho import Conselho
import context_crew

k = MCRKernel()
k.inicializar()

# Tenta carregar ContextCrew
ctx_crew = None
try:
    ctx_crew = context_crew.ContextCrew()
    print('[OK] ContextCrew carregado')
except:
    print('[AVISO] ContextCrew nao disponivel')

conselho = Conselho(
    kg=k.contexto.get('kg'),
    ia=k.contexto.get('ia'),
    ctx_crew=ctx_crew
)

print('='*60)
print('CONSELHO V3 - ARQUITETURA + CRIATIVIDADE')
print('='*60)
r = conselho.deliberar('Qual a melhor arquitetura para o MCR-DevIA?')
print('='*60)
print('VEREDITO:', r.get('veredito','?')[:400])
print(f'Tempo: {r.get("tempo_total",0)}s | Pers: {r.get("personalidades",0)}')
print('='*60)
