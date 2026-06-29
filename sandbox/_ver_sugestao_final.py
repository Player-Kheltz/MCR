"""Ver resultado Self-Study com comparacao de scans."""
import sys, json
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.kg import KnowledgeGraph
kg = KnowledgeGraph()
sugs = [l for l in kg._get_licoes() if l.get('ctx') == 'sugestao_melhoria']
sk = [l for l in kg._get_licoes() if l.get('ctx') == 'self_knowledge']

print('=== SCAN ATUAL ===')
if sk:
    s = sk[-1]
    m = json.loads(s.get('solucao', '{}')) if isinstance(s.get('solucao'), str) else s.get('solucao', {})
    print('Arquivos:', m.get('total_arquivos'), '| Linhas:', m.get('total_linhas'))
    print('Top5:', [(a['nome'], a['linhas']) for a in m.get('top5_maiores', [])])

# Compara com scan anterior
if len(sk) >= 2:
    s_ant = sk[-2]
    m_ant = json.loads(s_ant.get('solucao', '{}')) if isinstance(s_ant.get('solucao'), str) else s_ant.get('solucao', {})
    print()
    print('=== MELHORIAS DETECTADAS ===')
    for a in m.get('top5_maiores', []):
        for b in m_ant.get('top5_maiores', []):
            if a['nome'] == b['nome'] and b['linhas'] > a['linhas'] * 1.05:
                red = int((1 - a['linhas']/b['linhas']) * 100)
                print(f'  {a["nome"]}: {b["linhas"]} -> {a["linhas"]} ({red}%)')

print()
print('=== ULTIMA SUGESTAO ===')
if sugs:
    s = sugs[-1]
    print('Titulo:', s.get('erro', '')[:120])
    print('Causa:', s.get('causa', '')[:120])
    print()
    print(s.get('solucao', '')[:1000])
