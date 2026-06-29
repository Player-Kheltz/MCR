"""Testar Self-Study com filtro de repeticoes."""
import sys, time
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.master_agent import MasterAgent
ma = MasterAgent()
print('Iniciando...')
t0 = time.time()
ma.self_study.executar()
print('OK em', round(time.time()-t0, 1), 's')

# Ver resultado
from modulos.kg import KnowledgeGraph
kg = KnowledgeGraph()
sugs = [l for l in kg._get_licoes() if l.get('ctx') == 'sugestao_melhoria']
print('Total sugestoes:', len(sugs))
if sugs:
    s = sugs[-1]
    print('Titulo:', s.get('erro', '')[:120])
    print()
    print(s.get('solucao', '')[:1200])
