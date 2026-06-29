"""Teste completo: Self-Study com Deep Analysis.
Mostra anti-patterns, revisoes de funcoes e sugestao final."""
import sys, json
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.master_agent import MasterAgent
from modulos.kg import KnowledgeGraph
import time

print('=' * 65)
print('   SELF-STUDY COM DEEP ANALYSIS — TESTE COMPLETO')
print('=' * 65)
print()

# 1. Executa
t0 = time.time()
ma = MasterAgent()
ma.self_study.executar()
t_total = time.time() - t0
print(f'⏱ Tempo total: {round(t_total, 1)}s')
print()

# 2. Le resultados
kg = KnowledgeGraph()
sugs = [l for l in kg._get_licoes() if l.get('ctx') == 'sugestao_melhoria']
sk = [l for l in kg._get_licoes() if l.get('ctx') == 'self_knowledge']

# 3. Scan atual
if sk:
    s = sk[-1]
    m = json.loads(s.get('solucao', '{}')) if isinstance(s.get('solucao'), str) else s.get('solucao', {})
    print('📊 SCAN ATUAL')
    print(f'   Arquivos: {m.get("total_arquivos")} | Linhas: {m.get("total_linhas")}')
    print(f'   Classes: {m.get("total_classes")} | Funções: {m.get("total_funcoes")}')
    print()
    print('   Top 5 maiores:')
    for a in m.get('top5_maiores', []):
        print(f'     {a["nome"]}: {a["linhas"]} linhas, {a["funcoes"]} funções')
    print()

# 4. Comparacao com scan anterior
if len(sk) >= 2:
    s_ant = sk[-2]
    m_ant = json.loads(s_ant.get('solucao', '{}')) if isinstance(s_ant.get('solucao'), str) else s_ant.get('solucao', {})
    print('📈 EVOLUÇÃO DESDE ÚLTIMO SCAN')
    changes = 0
    for a in m.get('top5_maiores', []):
        for b in m_ant.get('top5_maiores', []):
            if a['nome'] == b['nome'] and b['linhas'] != a['linhas']:
                changes += 1
                diff = a['linhas'] - b['linhas']
                sinal = '+' if diff > 0 else ''
                print(f'   {a["nome"]}: {b["linhas"]} → {a["linhas"]} ({sinal}{diff})')
    if changes == 0:
        print('   Nenhuma alteração significativa (arquivos estáveis)')
    print()

# 5. Sugestao final
if sugs:
    s = sugs[-1]
    print('💡 ÚLTIMA SUGESTÃO GERADA')
    print(f'   Título: {s.get("erro", "")[:120]}')
    print(f'   Baseada em: {s.get("causa", "")[:150]}')
    print()
    print(s.get("solucao", "")[:2000])
    print()

print('=' * 65)
print('   TESTE CONCLUÍDO')
print('=' * 65)
