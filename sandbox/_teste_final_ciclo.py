"""Teste final do ciclo de auto-melhoria.
Executa Self-Study, mostra scan atual, compara com anterior, mostra sugestao.
"""
import sys, json
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.master_agent import MasterAgent
from modulos.kg import KnowledgeGraph
import time

# 1. Executa Self-Study
print('=' * 60)
print('CICLO DE AUTO-MELHORIA - TESTE FINAL')
print('=' * 60)
print()
print('1. Executando Self-Study...')
t0 = time.time()
ma = MasterAgent()
ma.self_study.executar()
print(f'   Concluido em {round(time.time()-t0, 1)}s')
print()

# 2. Le resultados
kg = KnowledgeGraph()
sk = [l for l in kg._get_licoes() if l.get('ctx') == 'self_knowledge']
sugs = [l for l in kg._get_licoes() if l.get('ctx') == 'sugestao_melhoria']

# 3. Mostra scan atual
if sk:
    s = sk[-1]
    m = json.loads(s.get('solucao', '{}')) if isinstance(s.get('solucao'), str) else s.get('solucao', {})
    print('2. Scan atual:')
    print(f'   Arquivos: {m.get("total_arquivos")} | Linhas: {m.get("total_linhas")}')
    print(f'   Top 5 maiores:')
    for a in m.get('top5_maiores', []):
        print(f'     {a["nome"]}: {a["linhas"]} linhas')
    print()

# 4. Mostra comparacao com scan anterior
if len(sk) >= 2:
    s_ant = sk[-2]
    m_ant = json.loads(s_ant.get('solucao', '{}')) if isinstance(s_ant.get('solucao'), str) else s_ant.get('solucao', {})
    melhorias = []
    for a in m.get('top5_maiores', []):
        for b in m_ant.get('top5_maiores', []):
            if a['nome'] == b['nome'] and b['linhas'] > a['linhas'] * 1.05:
                red = int((1 - a['linhas']/b['linhas']) * 100)
                melhorias.append(f'     {a["nome"]}: {b["linhas"]} -> {a["linhas"]} ({red}%)')
    if melhorias:
        print('3. Melhorias detectadas desde ultimo scan:')
        for m in melhorias:
            print(m)
    else:
        print('3. Nenhuma melhoria significativa detectada (arquivos estaveis)')
    print()

# 5. Mostra ultima sugestao
if sugs:
    s = sugs[-1]
    print('4. Ultima sugestao gerada:')
    print(f'   Titulo: {s.get("erro", "")[:120]}')
    print(f'   Causa: {s.get("causa", "")[:150]}')
    print()
    print('   Conteudo:')
    print(s.get('solucao', '')[:1200])
    if len(s.get('solucao', '')) > 1200:
        print(f'   ... (+{len(s.get("solucao",""))-1200} chars)')
else:
    print('4. Nenhuma sugestao gerada')

print()
print('=' * 60)
print('CICLO CONCLUIDO')
print('=' * 60)
