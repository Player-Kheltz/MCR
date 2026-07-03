"""Teste de itens no indexador."""
import sys
sys.path.insert(0, 'Scripts/mcr_devia/modulos')
from canary_indexer import CanaryIndexer

idx = CanaryIndexer()
idx.indexar(forcar=True)

# Verificar Al Dee
al_dee = [n for n in idx.npcs if n['nome'] == 'Al Dee']
if al_dee:
    n = al_dee[0]
    print('Al Dee:', n['tipo'])
    print('Itens:', len(n['itens_shop']))
    for i in n['itens_shop'][:5]:
        print('  -', i)
else:
    print('Al Dee nao encontrado')

# Verificar quantos shops têm itens
com_itens = sum(1 for n in idx.npcs if n['tipo'] == 'shop' and n['itens_shop'])
total_shops = sum(1 for n in idx.npcs if n['tipo'] == 'shop')
print('\nShops com itens: %d / %d' % (com_itens, total_shops))

# Testar busca
print('\n--- Busca: "sword axe weapon" ---')
r = idx.buscar('sword axe weapon', 5)
for x in r:
    print('  [%s] %s (%s, %d itens)' % (x['score'], x['nome'], x['tipo'], len(x.get('itens_shop', []))))
