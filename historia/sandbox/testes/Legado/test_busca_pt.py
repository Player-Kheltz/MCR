"""Teste de busca em portugues."""
import sys
sys.path.insert(0, 'Scripts/mcr_devia/modulos')
from canary_indexer import CanaryIndexer

idx = CanaryIndexer()
idx.indexar()

termos = [
    'ferreiro que vende armas',
    'vende espadas',
    'treinador de magias',
    'banco depositar gold',
    'vendedor de pocoes',
    'faz missoes',
]
for termo in termos:
    r = idx.buscar(termo, 5)
    print('--- Busca: "%s" ---' % termo)
    for x in r:
        itens = len(x.get('itens_shop', []))
        nome_curto = x['nome'][:25]
        print('  [%s] %s (%s, %d itens)' % (x['score'], nome_curto, x['tipo'], itens))
    if not r:
        print('  (nenhum resultado)')
    print()
