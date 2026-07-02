#!/usr/bin/env python3
"""Validacao REAL da qualidade apos evolucao da equacao.
Compara ANTES (soma) vs DEPOIS (produto) nos mesmos pares."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from MCR import *

def testar(motor, pares):
    resultados = []
    for nome, a, b in pares:
        if a in motor.topicos and b in motor.topicos:
            c = motor.conectar(a, b, forcar=True)
            if c:
                resultados.append({
                    'par': nome,
                    'nota': c['nota'],
                    'equacao': c['detalhes'].get('equacao', ''),
                    'formula': c['detalhes'].get('formula', ''),
                })
    return resultados

motor = MCRMotor()
motor.alimentar('SPA e o sistema de progressao do aventureiro com dominios elementais Fogo Gelo Terra Energia e Sagrado cada dominio tem 25 niveis', 'spa')
motor.alimentar('SHC e o sistema de habilidades contextuais com 5 camadas postura nivel sinergia estado e condicao', 'shc')
motor.alimentar('O NPC ferreiro em Eridanus se chama Bruno Ferro Forte ele vende armaduras de ferro e aco na praca central', 'npc')
motor.alimentar('A arvore de Natal do servidor MCR fica na praca central de Eridanus com luzes magicas', 'natal')
motor.alimentar('Eridanus e a cidade inicial do projeto MCR construida as margens do Lago Cristalino', 'eridanus')

pares = [
    ('SPA+SHC', 'spa', 'shc'),
    ('SPA+NPC', 'spa', 'npc'),
    ('SPA+Natal', 'spa', 'natal'),
    ('NPC+Eridanus', 'npc', 'eridanus'),
    ('SPA+Eridanus', 'spa', 'eridanus'),
    ('Natal+Eridanus', 'natal', 'eridanus'),
]

from MCR import _EQUACAO_ATUAL
formula_original = _EQUACAO_ATUAL.get('formula', 'by + pa + tk')

print('')
print('VALIDACAO DA EQUACAO EVOLUIDA')
print('')

for formula_testar, label in [('by + pa + tk', 'SOMA (original)'), ('by * pa + tk', 'PRODUTO (evoluido)')]:
    _EQUACAO_ATUAL['formula'] = formula_testar
    print(f'  Formula: {label} ({formula_testar})')
    print('  ' + '-' * 50)
    resultados = testar(motor, pares)
    for r in resultados:
        nota = r['nota']
        barra = '#' * max(0, min(10, int(nota)))
        barra = barra + '.' * max(0, 10 - len(barra))
        eq = r.get('equacao', '')[:50]
        print(f'    {r["par"]:15s}: [{barra}] {nota:.1f}/10  | {eq}')
    print()

_EQUACAO_ATUAL['formula'] = formula_original
print('')
