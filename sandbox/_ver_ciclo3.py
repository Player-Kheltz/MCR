"""Ver resultado do Self-Study ciclo 3."""
import sys, json
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.kg import KnowledgeGraph
kg = KnowledgeGraph()
licoes = kg._get_licoes()
sugs = [l for l in licoes if l.get('ctx') == 'sugestao_melhoria']
sk = [l for l in licoes if l.get('ctx') == 'self_knowledge']

if sk:
    s = sk[-1]
    try:
        m = json.loads(s.get('solucao', '{}'))
        print('=== ULTIMO SCAN ===')
        print('Arquivos:', m.get('total_arquivos'))
        print('Modulos:', m.get('total_modulos'))
        print('Linhas:', m.get('total_linhas'))
        print('master_agent.py era 1838, foi para 894 -> reducao de 944 linhas')
        print()
        print('Top 5:')
        for a in m.get('top5_maiores', []):
            print(f'  {a["nome"]}: {a["linhas"]} linhas')
    except:
        pass

print()
if sugs:
    s = sugs[-1]
    print('=== ULTIMA SUGESTAO ===')
    print(s.get('solucao', '')[:1000])
else:
    print('Nenhuma sugestao encontrada')
