"""Teste do CanaryIndexer."""
import sys
sys.path.insert(0, 'Scripts/mcr_devia/modulos')
from canary_indexer import CanaryIndexer

idx = CanaryIndexer()
idx.indexar()

termos = ['vende espadas', 'arma', 'blacksmith', 'ferreiro', 'quest trainer', 'depositar gold']
for termo in termos:
    r = idx.buscar(termo, 3)
    print(f'--- Busca: "{termo}" ---')
    for x in r:
        print(f'  [{x["score"]}] {x["nome"]} ({x["tipo"]}, {x["tamanho_linhas"]} linhas)')
    if not r:
        print('  (nenhum resultado)')
    print()

print('=== ESTATISTICAS ===')
est = idx.obter_estatisticas()
for k, v in est.items():
    print(f'  {k}: {v}')
