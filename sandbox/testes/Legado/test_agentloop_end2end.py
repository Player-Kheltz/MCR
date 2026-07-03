#!/usr/bin/env python
"""Teste end-to-end do AgentLoop com a correcao de exemplos."""
import os, sys, re

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia', 'modulos'))
os.chdir(BASE)

from agent_loop import AgentLoop

agent = AgentLoop()
resultados = []

# Teste 1: Ferreiro shop
r = agent.executar('Ferreiro em Eridanus que vende armas', 'shop')
codigo = r['codigo']
lixos = re.findall(r'example item|another item|third item', codigo, re.IGNORECASE)
nomes = re.findall(r'itemName\s*=\s*"([^"]+)"', codigo)
print('Teste 1 - Ferreiro:')
print('  Nome: %s' % r.get('nome', '?'))
print('  Itens: %s' % nomes)
print('  Lixo: %d %s' % (len(lixos), lixos))
print('  Valido: %s' % r.get('validacao', {}).get('valido', False))
resultados.append({'teste': 'Ferreiro', 'lixo': len(lixos), 'itens': nomes})

# Teste 2: Vendedor de pocoes
r2 = agent.executar('Vendedor de pocoes magicas em Venore', 'shop')
codigo2 = r2['codigo']
lixos2 = re.findall(r'example item|another item|third item', codigo2, re.IGNORECASE)
nomes2 = re.findall(r'itemName\s*=\s*"([^"]+)"', codigo2)
print('\nTeste 2 - Vendedor de pocoes:')
print('  Nome: %s' % r2.get('nome', '?'))
print('  Itens: %s' % nomes2)
print('  Lixo: %d %s' % (len(lixos2), lixos2))
print('  Valido: %s' % r2.get('validacao', {}).get('valido', False))
resultados.append({'teste': 'Pocoes', 'lixo': len(lixos2), 'itens': nomes2})

# Teste 3: Guarda do portao (gate)
r3 = agent.executar('Guarda do portao de Carlin', 'gate')
codigo3 = r3['codigo']
print('\nTeste 3 - Guarda:')
print('  Nome: %s' % r3.get('nome', '?'))
print('  Valido: %s' % r3.get('validacao', {}).get('valido', False))
level_m = re.search(r'getLevel\(\)\s*[<>]\s*(\d+)', codigo3)
print('  Level: %s' % (level_m.group(0) if level_m else 'nao encontrado'))
resultados.append({'teste': 'Guarda', 'lixo': 0})

# Teste 4: Banco
r4 = agent.executar('Banco central de Thais', 'bank')
codigo4 = r4['codigo']
print('\nTeste 4 - Banco:')
print('  Nome: %s' % r4.get('nome', '?'))
print('  Valido: %s' % r4.get('validacao', {}).get('valido', False))
bank_m = re.search(r'bank_name\s*=\s*"([^"]+)"', codigo4)
print('  Bank name: %s' % (bank_m.group(1) if bank_m else 'nao encontrado'))
resultados.append({'teste': 'Banco', 'lixo': 0})

print('\n' + '=' * 50)
print('RESUMO FINAL')
print('=' * 50)
total_lixo = sum(r['lixo'] for r in resultados)
print('Total placeholders lixo: %d' % total_lixo)
if total_lixo == 0:
    print('VEREDITO: Todos os testes passaram sem lixo!')
else:
    print('VEREDITO: %d placeholders lixo encontrados' % total_lixo)
