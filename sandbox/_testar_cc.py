#!/usr/bin/env python3
"""Testa ContextCrew v2."""
import sys, os
sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from context_crew import ContextCrew, KG_PATH
import json

# Verifica KG
print(f'KG: {KG_PATH}')
with open(KG_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
versoes = data.get('versoes', 0)
print(f'Versao KG: {versoes}')

# Busca SPA no KG direto
licoes = data.get('licoes', [])
for l in licoes:
    txt = (l.get('solucao','') + ' ' + l.get('erro','') + ' ' + l.get('causa','')).lower()
    if 'spa' in txt or 'sistema' in txt and 'progressao' in txt:
        print(f'KG tem SPA: {l.get("solucao","")[:100]}')
        break

# ContextCrew
c = ContextCrew()
print(f'ContextCrew versao KG: {c._versao_kg}')
r = c.executar('O que e SPA?')
print(f'Resultado: {r[:200] if r else "(vazio)"}')
