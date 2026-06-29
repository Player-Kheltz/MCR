"""Ver resultado Self-Study com Deep Analysis."""
import sys, json
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.kg import KnowledgeGraph
kg = KnowledgeGraph()
sugs = [l for l in kg._get_licoes() if l.get('ctx') == 'sugestao_melhoria']
print('Total sugestoes:', len(sugs))
if sugs:
    s = sugs[-1]
    print('Titulo:', s.get('erro', '')[:120])
    print('Causa:', s.get('causa', '')[:150])
    print()
    print(s.get('solucao', '')[:1500])
