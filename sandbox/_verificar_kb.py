#!/usr/bin/env python3
import json, re

with open(r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

licoes = data.get('licoes', [])
conhecimento = [l for l in licoes if l.get('ctx') == 'conhecimento']

print(f'Total lessons: {len(licoes)}')
print(f'ctx=conhecimento: {len(conhecimento)}')
print(f'ctx=conhecimento ativas: {sum(1 for l in conhecimento if not l.get("inactive"))}')
print()

# Amostra das primeiras 10
print('AMOSTRA (10 primeiras):')
for l in conhecimento[:10]:
    print(f'  {l["id"]}: {l["erro"][:80]}')
    print(f'    Fonte: {l["causa"][:80]}')
    print()

# Verifica duplicatas
solucoes = [l.get('solucao','') for l in conhecimento]
print(f'Solucoes unicas: {len(set(solucoes))} de {len(solucoes)}')
print(f'Duplicatas: {len(solucoes) - len(set(solucoes))}')
print()

# Amostra de codigo
print('AMOSTRA CODIGO (5 registros):')
codigo = [l for l in conhecimento if 'Code:' in l.get('causa','')]
for l in codigo[:5]:
    print(f'  {l["erro"][:60]} | {l["causa"][:60]} | {l["solucao"][:80]}')
print()

# Amostra de docs
print('AMOSTRA DOCS (se existir):')
docs = [l for l in conhecimento if 'Doc:' in l.get('erro','')]
for l in docs[:5]:
    print(f'  {l["erro"][:60]} | {l["causa"][:60]}')
    print(f'    {l["solucao"][:100]}')
