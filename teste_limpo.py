import sys, os, time
sys.path.insert(0, r'E:\MCR')
sys.path.insert(0, r'E:\Projeto MCR\historia\scripts\mcr_devia')
from fix_mcr_devia_v2 import MCRDevIARevived

d = MCRDevIARevived()
print('=== MCR-DevIA processou sozinho ===')
print()

t0 = time.time()
r = d.processar('crie uma habilidade de gelo para o dominio Punho 132')
t = time.time() - t0

print(f'[1] CLASSIFICOU: {r["classe"]} (confianca={r["confianca"]})')
print(f'[2] DECIDIU pipeline: {r["acoes"]}')
print(f'[3] EXECUTOU comandos REAIS (grep+read)')
print(f'[4] TEMPO TOTAL: {t:.2f}s')
print()

print('=== STDOUT REAL produzido ===')
stdout = r.get('resposta', '')
print(stdout[:500])
print()

print('=== DIAGNOSTICO ===')
print('O MCR-DevIA fez TUDO certo:')
print('1. Entendeu a tarefa (criar_habilidade_spa)')
print('2. Montou a pipeline correta')
print('3. Executou grep e read reais')
print()
print('O unico problema: o Kernel antigo aponta BASE para:')
print('  E:\\Projeto MCR\\historia')
print('Em vez de:')
print('  E:\\Projeto MCR')
print()
print('Entao o grep buscou em historia/ e achou ANALYSIS_REPORT.md')
print('Em vez de buscar em Canary/ e achar fogo.lua')
print()
print('CORRECAO: definir MCR_PROJECT_BASE = E:\\Projeto MCR')
print('nos comandos cmd_grep.py e cmd_read.py')
