#!/usr/bin/env python3
"""Teste rapido MCR-DevIA Revived."""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, os.path.join('.', '..', 'Projeto MCR', 'historia', 'scripts', 'mcr_devia'))

from fix_mcr_devia_v2 import MCRDevIARevived

revived = MCRDevIARevived()
print(f'Decider: {revived.decider.total} seeds')
print(f'Router: {len(revived.router.SEEDS)} rotas')

testes = [
    'crie uma habilidade de gelo',
    'encontre um crash no servidor',
    'explique o que e SPA',
    'leia o progresso.md',
    'traduza essas strings pra PT-BR',
]
for t in testes:
    classe, conf = revived.decider.classificar(t)
    acoes = revived.router.decidir(classe, conf)
    print(f'  "{t[:35]}..." -> {classe} conf={conf:.2f} -> {" -> ".join(acoes)}')
