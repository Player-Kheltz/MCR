"""Teste do CanaryIndexer - busca em ingles."""
import sys
sys.path.insert(0, 'Scripts/mcr_devia/modulos')
from canary_indexer import CanaryIndexer

idx = CanaryIndexer()
idx.indexar()

# Testes em ingles (idioma dos NPCs)
termos = ['sword axe weapon', 'blacksmith', 'sell weapon', 'shop items', 'quest reward']
for termo in termos:
    r = idx.buscar(termo, 5)
    print('--- Busca: "%s" ---' % termo)
    for x in r:
        print('  [%s] %s (%s, %d itens)' % (x['score'], x['nome'], x['tipo'], len(x.get('itens_shop', []))))
        # Mostra alguns itens se for shop
        if x['itens_shop']:
            itens_mostrar = [i['nome'] for i in x['itens_shop'][:3]]
            print('       itens: %s' % ', '.join(itens_mostrar))
    if not r:
        print('  (nenhum resultado)')
    print()
