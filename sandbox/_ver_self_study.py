"""Ver resultado do Self-Study."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

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
    print('== ULTIMO SCAN ==')
    print('Titulo:', s.get('erro', '')[:100])
    print('Solucao (metricas):', s.get('solucao', '')[:500])
    print()

if sugs:
    s = sugs[-1]
    print('== ULTIMA SUGESTAO ==')
    print('Titulo:', s.get('erro', '')[:120])
    print()
    texto = s.get('solucao', '')
    print(texto[:1200])
    if len(texto) > 1200:
        print('... (+' + str(len(texto)-1200) + ' chars)')
