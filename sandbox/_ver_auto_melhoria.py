"""Ver auto-melhoria."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.kg import KnowledgeGraph
kg = KnowledgeGraph()
l = kg._get_licoes()
am = [x for x in l if x.get('ctx') == 'auto_melhoria']
print('Auto-melhoria lessons:', len(am))
for x in am[-3:]:
    print('  Erro:', str(x.get('erro', ''))[:60])
    print('  Causa:', str(x.get('causa', ''))[:60])
    print('  Solucao:', str(x.get('solucao', ''))[:80])
