#!/usr/bin/env python3
"""Debug: busca no KG e no ContextCrew."""
import sys, os, json
sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from context_crew import ContextCrew

kg_path = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'
with open(kg_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'KG versao: {data.get("versoes")}')
print(f'Total licoes: {len(data.get("licoes",[]))}')

# Busca manual por SPA
termos = ['spa', 'progressao', 'aventureiro']
for l in data.get('licoes', []):
    txt = str(l.get('solucao','') + ' ' + l.get('erro','') + ' ' + l.get('causa','')).lower()
    score = sum(1 for t in termos if t in txt)
    if score > 1:
        print(f'  Score {score}: id={l.get("id")} sol={l.get("solucao","")[:80]}')

# Testa o metodo _buscar_kg do ContextCrew
print('\nTestando ContextCrew._buscar_kg...')
import re
from stop_words import STOP_V12 as _STOP
palavras = set(re.findall(r'\b[a-zA-Z]{4,}\b', 'O que e SPA?'.lower()))
palavras = palavras - _STOP
print(f'Termos extraidos: {palavras}')

c = ContextCrew()
resultados = c._buscar_kg(list(palavras))
print(f'Resultados: {len(resultados)}')
for r in resultados:
    print(f'  {r.get("solucao","")[:100]}')
