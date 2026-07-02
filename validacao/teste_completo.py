#!/usr/bin/env python3
"""TESTE COMPLETO: ferramentas + web + respostas."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import *

# Testa o fluxo completo de cada pergunta
motor = MCRMotor()
cmd = MCRComandos(motor)

# Alimenta conhecimento sobre Brasil (simula arquivo encontrado)
motor.alimentar(
    'Pedro Alvares Cabral descobriu o Brasil em 1500. '
    'Ele era um navegador portugues que liderou uma expedicao.', 'conhecimento_brasil')

testes = [
    ('que dia e hoje',     'ferramenta', 'data'),
    ('que horas sao',      'ferramenta', 'hora'),
    ('quem descobriu o brasil', 'conhecimento', 'Cabral'),
    ('explique o que e SPA', 'gerado', ''),
]

print()
print('= ' * 35)
print('  TESTE COMPLETO DE RESPOSTAS')
print('= ' * 35)
print()

acertos = 0
for pergunta, tipo, palavra_chave in testes:
    resultado = cmd.master(pergunta)
    texto = resultado.get('resposta', str(resultado))
    
    if tipo == 'ferramenta':
        # Verifica se acionou a ferramenta certa
        acertou = palavra_chave in texto.lower() if palavra_chave else len(texto) > 0
    elif tipo == 'conhecimento':
        acertou = palavra_chave in texto if palavra_chave else len(texto) > 0
    else:
        acertou = len(texto) > 10
    
    status = 'PASSOU' if acertou else 'FALHOU'
    if acertou: acertos += 1
    safe = texto[:80].encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
    print(f'  [{status[:1]}] {pergunta:35s} -> {safe}...')

print()
print(f'  RESULTADO: {acertos}/{len(testes)}')
print()
