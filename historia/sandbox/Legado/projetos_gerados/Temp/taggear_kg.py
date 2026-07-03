"""Taggea lessons do KG: stress_test -> tipo=benchmark."""
import json, sys
from collections import Counter

path = 'E:/Projeto MCR/sandbox/.mcr_devia/knowledge.json'
with open(path, 'r', encoding='utf-8') as f:
    kg = json.load(f)

licoes = kg.get('licoes', [])
print(f'Total de lessons: {len(licoes)}')
ctx_count = Counter(l.get('ctx', 'sem_ctx') for l in licoes)
print(f'Por ctx: {dict(ctx_count)}')

benchmark_count = 0
domain_count = 0
for l in licoes:
    ctx = l.get('ctx', '')
    if ctx == 'stress_test':
        l['tipo'] = 'benchmark'
        benchmark_count += 1
    else:
        l['tipo'] = 'dominio'
        domain_count += 1

print(f'Taggeadas: {benchmark_count} benchmark, {domain_count} dominio')

kg['versoes'] = kg.get('versoes', 0) + 1
with open(path, 'w', encoding='utf-8') as f:
    json.dump(kg, f, ensure_ascii=False, indent=2)

tipo_count = Counter(l.get('tipo') for l in licoes)
print(f'Salvo. Versao: {kg["versoes"]}')
print(f'Por tipo: {dict(tipo_count)}')
