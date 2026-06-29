"""Ver resultado do Self-Study ciclo 2."""
import sys, json
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.kg import KnowledgeGraph
kg = KnowledgeGraph()
licoes = kg._get_licoes()
sugs = [l for l in licoes if l.get('ctx') == 'sugestao_melhoria']
sk = [l for l in licoes if l.get('ctx') == 'self_knowledge']

print('=== ULTIMO SCAN ===')
if sk:
    s = sk[-1]
    try:
        m = json.loads(s.get('solucao', '{}'))
        print('Arquivos:', m.get('total_arquivos'))
        print('Modulos:', m.get('total_modulos'))
        print('Linhas:', m.get('total_linhas'))
        print('Classes:', m.get('total_classes'))
        print('Funcoes:', m.get('total_funcoes'))
        print()
        print('Top 5:')
        for a in m.get('top5_maiores', []):
            print(f'  {a["nome"]}: {a["linhas"]} linhas')
    except:
        print(s.get('solucao', '')[:200])

print()
print('=== ULTIMA SUGESTAO ===')
if sugs:
    s = sugs[-1]
    print('Titulo:', s.get('erro', '')[:120])
    print()
    print(s.get('solucao', '')[:1500])
