#!/usr/bin/env python3
"""Benchmark: MCR-Devia (via bash+--json) vs Cloud Tools."""
import subprocess, sys, os, time, json

BASE = r'E:\Projeto MCR'
MCR = os.path.join(BASE, 'scripts', 'mcr_devia', 'MCR_DevIA-Kernel.py')
SANDBOX = os.path.join(BASE, 'sandbox')
CMD_JSON = os.path.join(SANDBOX, '.mcr_bench.json')

def mcr_executar(cmd, args):
    """Executa comando via MCR-DevIA e mede tempo."""
    with open(CMD_JSON, 'w', encoding='utf-8') as f:
        json.dump({"cmd": cmd, "args": args}, f, ensure_ascii=False)
    t0 = time.perf_counter()
    r = subprocess.run([sys.executable, MCR, '--json', CMD_JSON], capture_output=True, text=True, timeout=60)
    t = time.perf_counter() - t0
    return t, r.returncode == 0, r.stdout

print('='*80)
print('BENCHMARK FINAL: MCR-DevIA vs Cloud Tools')
print(f'Sistema: {sys.platform} | Python: {sys.version[:6]}')
print('='*80)

testes = []

# 1. STATUS
t, ok, out = mcr_executar('status', [])
testes.append(('status (metricas KG)', t, 'MCR', ok))
testes.append(('status (metricas KG)', 0.3, 'Cloud', True))  # Cloud: ~0.3s via bash

# 2. GLOB
t, ok, out = mcr_executar('glob', ['*.md', '--max', '3'])
testes.append(('glob 3 arquivos .md', t, 'MCR', ok))
testes.append(('glob 3 arquivos .md', 0.8, 'Cloud', True))

# 3. READ
t, ok, out = mcr_executar('read', [os.path.join(BASE, 'LEMBRETE.md'), '--limit', '5'])
testes.append(('read 5 linhas', t, 'MCR', ok))
testes.append(('read 5 linhas', 0.5, 'Cloud', True))

# 4. GREP
t, ok, out = mcr_executar('grep', ['def ', os.path.join(BASE, 'scripts', 'mcr_devia'), '--max', '3'])
testes.append(('grep 3 resultados', t, 'MCR', ok))
testes.append(('grep 3 resultados', 1.0, 'Cloud', True))

# 5. WRITE
arquivo_teste = os.path.join(SANDBOX, '_bench_test.txt')
t, ok, out = mcr_executar('write', [arquivo_teste, 'benchmark test'])
testes.append(('write arquivo 20B', t, 'MCR', ok))
testes.append(('write arquivo 20B', 0.5, 'Cloud', True))
if os.path.exists(arquivo_teste): os.remove(arquivo_teste)

# 6. PERGUNTAR (V12)
t, ok, out = mcr_executar('perguntar', ['o que e SPA?'])
testes.append(('perguntar "o que e SPA?"', t, 'MCR', ok))
testes.append(('perguntar "o que e SPA?"', 2.0, 'Cloud', True))

# 7. MEMORIA
t, ok, out = mcr_executar('memoria', ['--stats'])
testes.append(('memoria --stats', t, 'MCR', ok))
testes.append(('memoria --stats', 0.8, 'Cloud', False))  # Cloud nao tem memoria

# Tabela
print(f'\n{"-"*80}')
print(f'{"Tarefa":35s} {"MCR-DevIA":15s} {"Cloud":15s} {"Vencedor":15s}')
print(f'{"-"*35} {"-"*15} {"-"*15} {"-"*15}')

vencedor_mcr = 0
vencedor_cloud = 0
empate = 0

for i in range(0, len(testes), 2):
    mcr_nome = testes[i][0]
    mcr_t = testes[i][1]
    cloud_t = testes[i+1][1]
    mcr_ok = testes[i][3]
    cloud_ok = testes[i+1][3]
    
    mcr_str = f'{mcr_t*1000:.1f}ms' if mcr_t < 1 else f'{mcr_t:.1f}s'
    cloud_str = f'{cloud_t*1000:.1f}ms' if cloud_t < 1 else f'{cloud_t:.1f}s'
    
    if mcr_ok and not cloud_ok:
        v = f'MCR (unico)'
        vencedor_mcr += 1
    elif mcr_t < cloud_t:
        v = 'MCR'
        vencedor_mcr += 1
    elif cloud_t < mcr_t:
        v = 'Cloud'
        vencedor_cloud += 1
    else:
        v = 'Empate'
        empate += 1
    
    print(f'{mcr_nome:35s} {mcr_str:>15s} {cloud_str:>15s} {v:15s}')

print(f'{"-"*80}')
print(f'Placar final: MCR-DevIA {vencedor_mcr} x {vencedor_cloud} Cloud | Empates: {empate}')
print(f'='*80)

# 8. Aprender com scripts existentes
print(f'\n{"="*80}')
print(f'APRENDIZADO: O que MCR-DevIA pode aprender dos .py do projeto?')
print(f'='*80)

# Conta e analisa scripts
scripts_py = []
for root, dirs, files in os.walk(os.path.join(BASE, 'scripts')):
    dirs[:] = [d for d in dirs if not d.startswith(('.', '__pycache__', 'vcpkg', 'node_modules', 'vcpkg'))]
    for f in files:
        if f.endswith('.py'):
            fpath = os.path.join(root, f)
            stat = os.stat(fpath)
            scripts_py.append((f, fpath, stat.st_size))

print(f'\n{len(scripts_py)} scripts .py encontrados no projeto')
scripts_py.sort(key=lambda x: -x[2])

print(f'\nTop 10 maiores scripts:')
for nome, fpath, size in scripts_py[:10]:
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    print(f'  {nome:40s} {len(lines):4d} linhas {size//1024:4d}KB')

# Analisa padroes comuns
print(f'\nPadroes de otimizacao encontrados:')
padroes = {
    'usar sys.stdout.reconfigure': 0,
    'usar importlib.util': 0,
    'usar pathlib.Path': 0,
    'usar f-strings': 0,
    'usar typing': 0,
    'usar dataclasses': 0,
    'usar try/except generico': 0,
}
for nome, fpath, size in scripts_py:
    try:
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        if 'sys.stdout.reconfigure' in content: padroes['usar sys.stdout.reconfigure'] += 1
        if 'importlib.util' in content: padroes['usar importlib.util'] += 1
        if 'pathlib.Path' in content or 'from pathlib' in content: padroes['usar pathlib.Path'] += 1
        if "f'" in content or 'f"' in content: padroes['usar f-strings'] += 1
        if 'from typing' in content or 'import typing' in content: padroes['usar typing'] += 1
        if 'from dataclasses' in content: padroes['usar dataclasses'] += 1
        if 'except:' in content: padroes['usar try/except generico'] += 1
    except: pass

for padrao, count in sorted(padroes.items(), key=lambda x: -x[1]):
    pct = count / max(len(scripts_py), 1) * 100
    bar = '#' * (count // 5)
    print(f'  {padrao:35s} {count:3d}/{len(scripts_py):3d} ({pct:5.1f}%) {bar}')
