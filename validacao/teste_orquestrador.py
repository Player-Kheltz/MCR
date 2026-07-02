#!/usr/bin/env python3
"""TESTE DO ORQUESTRADOR COMPLETO (MCR_Chat)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import *

m = MCRMotor()
cmd = MCRComandos(m)

# Alimenta conhecimento
m.alimentar(
    'Pedro Alvares Cabral descobriu o Brasil em 1500. '
    'Ele era um navegador portugues.', 'conhecimento_brasil')

# Simula o _responder do MCR_Chat
from MCR_Chat import _responder, _escolher_ferramenta, FERAMENTAS

testes = [
    ('que dia e hoje',      'data'),
    ('que horas sao',       'hora'),
    ('qual a data',         'data'),
    ('me diga as horas',   'hora'),
    ('quem descobriu o brasil', 'conhecimento'),
]

print()
print('= ' * 35)
print('  TESTE DO ORQUESTRADOR')
print('= ' * 35)
print()

acertos = 0
for pergunta, esperado in testes:
    resultado = _responder(pergunta)
    
    # Verifica qual fonte foi usada
    if resultado.startswith('MCR [data]'):
        fonte = 'data'
    elif resultado.startswith('MCR [hora]'):
        fonte = 'hora'
    elif resultado.startswith('MCR [web]'):
        fonte = 'web'
    elif resultado.startswith('MCR [conhecimento]'):
        fonte = 'conhecimento'
    else:
        fonte = 'gerado'
    
    acertou = fonte == esperado
    if acertou: acertos += 1
    status = 'PASSOU' if acertou else 'FALHOU'
    
    safe = resultado[:100].encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
    print(f'  [{status[:1]}] {pergunta:30s} -> {fonte:15s} | {safe}...')

print()
print(f'  RESULTADO: {acertos}/{len(testes)}')
print()
