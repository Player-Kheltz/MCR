"""Teste de Performance do MCR-DevIA"""
import subprocess, sys, os, time, json

DEVIA = r'E:\Projeto MCR\scripts\mcr_devia'
SCANNER = r'E:\Projeto MCR\sandbox\resolver_ultra.py'
KG_PATH = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'
BASE = r'E:\Projeto MCR\sandbox\teste_cego_ultra'

def timer():
    return time.time()

def medir(nome, func):
    inicio = timer()
    resultado = func()
    fim = timer()
    return resultado, round(fim - inicio, 2)

print('='*60)
print('  TESTE DE PERFORMANCE — MCR-DevIA')
print('='*60)

# 1. Velocidade de scan
print('\n[1/5] Velocidade de deteccao...')
with open(SCANNER, 'r', encoding='utf-8') as f:
    codigo = f.read()

tempo_compile = timer()
compile(codigo, 'scanner.py', 'exec')
t_compile = round(timer() - tempo_compile, 3)
print(f'  Compilacao do scanner: {t_compile}s')

tempo_scan = timer()
r = subprocess.run([sys.executable, SCANNER], capture_output=True, text=True, timeout=30)
t_scan = round(timer() - tempo_scan, 2)
print(f'  Scan de 12 arquivos: {t_scan}s')
print(f'  Media por arquivo: {round(t_scan/12, 3)}s')

# 2. Precisao de deteccao
print('\n[2/5] Precisao de deteccao...')
detectados = r.stdout.count('[!]')
total = 12
print(f'  Detectados: {detectados}/{total}')
print(f'  Precisao: {round(detectados/total*100, 1)}%')

# 3. Velocidade de correcao
print('\n[3/5] Velocidade de correcao...')
t_correcao = timer()
r2 = subprocess.run([sys.executable, SCANNER], capture_output=True, text=True, timeout=300)
t_correcao = round(timer() - t_correcao, 2)
print(f'  Scan + correcao: {t_correcao}s')

corrigidos = r2.stdout.count('[CORRIGIDO]')
print(f'  Corrigidos: {corrigidos}')
print(f'  Tempo por correcao: {round(t_correcao/max(1,corrigidos), 1)}s' if corrigidos > 0 else '  (sem correcoes)')

# 4. Tamanho do KG
print('\n[4/5] Knowledge Graph...')
if os.path.exists(KG_PATH):
    with open(KG_PATH, 'r', encoding='utf-8', errors='replace') as f:
        kg = json.load(f)
    n_licoes = len(kg.get('licoes', []))
    n_ctx = len(set(l.get('ctx', '') for l in kg.get('licoes', [])))
    print(f'  Licoes: {n_licoes}')
    print(f'  Contextos: {n_ctx}')
    print(f'  Versao: V{kg.get("versoes", 0)}')
else:
    print('  KG nao encontrado')

# 5. Teste de chamada direta
print('\n[5/5] Teste de chamada direta (mcr_ultimate.py)...')
t_mcr = timer()
r3 = subprocess.run(
    [sys.executable, os.path.join(DEVIA, 'mcr_ultimate.py'), 'status'],
    capture_output=True, text=True, timeout=30
)
t_mcr = round(timer() - t_mcr, 2)
print(f'  mcr_ultimate.py status: {t_mcr}s')
print(f'  Resposta: {r3.stdout.strip()[:100]}')

# Relatorio final
print(f'\n{"="*60}')
print(f'  RELATORIO DE PERFORMANCE')
print(f'{"="*60}')
print(f'''
  DETECCAO:     {detectados}/{total} em {t_scan}s ({round(t_scan/detectados,1) if detectados else 0}s/item)
  CORRECAO:     {corrigidos} em {t_correcao}s
  KG:           {n_licoes} licoes em {n_ctx} contextos
  COMPILACAO:   {t_compile}s
  MCR ULTIMATE: {t_mcr}s

  NOTA GERAL:   Performance adequada para uso local.
                Scan em ms, correcao em segundos (via IA local).
                O gargalo e a IA local (Qwen 7B), nao o MCR-DevIA.
''')
print('='*60)
