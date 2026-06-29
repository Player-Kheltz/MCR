"""Ver sugestao do Self-Study apos limpeza."""
import sys, json
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.kg import KnowledgeGraph
kg = KnowledgeGraph()
l = kg._get_licoes()
su = [x for x in l if x.get('ctx') == 'sugestao_melhoria']
if su:
    s = su[-1]
    print('TITULO:')
    print(s.get('erro')[:120])
    print()
    print('SUGESTAO:')
    print(s.get('solucao')[:1500])
else:
    print('Nenhuma sugestao encontrada')
