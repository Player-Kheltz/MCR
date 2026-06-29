"""Ver resultado do Self-Study apos refatoracao."""
import sys, json
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.kg import KnowledgeGraph

kg = KnowledgeGraph()
licoes = kg._get_licoes()

sk = [l for l in licoes if l.get('ctx') == 'self_knowledge']
sugs = [l for l in licoes if l.get('ctx') == 'sugestao_melhoria']

print('Self-Knowledge lessons:', len(sk))
print('Sugestoes de melhoria:', len(sugs))
print()

if sk:
    s = sk[-1]
    print('=== ULTIMO SCAN ===')
    d = s.get('solucao', '{}')
    try:
        m = json.loads(d) if isinstance(d, str) else d
        print('Arquivos:', m.get('total_arquivos'))
        print('Modulos:', m.get('total_modulos'))
        print('Linhas:', m.get('total_linhas'))
        print('Classes:', m.get('total_classes'))
        print('Funcoes:', m.get('total_funcoes'))
        print('Media linhas/arquivo:', m.get('media_linhas_arquivo'))
        print()
        print('Top 5:')
        for a in m.get('top5_maiores', []):
            print(f'  {a["nome"]}: {a["linhas"]} linhas, {a["funcoes"]} funcoes')
    except:
        print(d[:300])

if sugs:
    s = sugs[-1]
    print()
    print('=== ULTIMA SUGESTAO ===')
    print('Titulo:', s.get('erro', '')[:120])
    print()
    print(s.get('solucao', '')[:1200])
