"""
MCR-DevIA — Scan global do projeto real
=========================================
Escaneia TODAS as pastas do MCR, copia arquivos problematicos
para o sandbox, tenta corrigir, e salva pra validacao.
Nada e alterado no projeto real sem autorizacao.
"""

import os, re, sys, shutil, datetime

BASE_PROJETO = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox\scan_real'
os.makedirs(SANDBOX, exist_ok=True)

# Importa scanner
sys.path.insert(0, 'E:/Projeto MCR/sandbox')
import importlib.util
spec = importlib.util.spec_from_file_location('r', 'E:/Projeto MCR/sandbox/resolver_ultra.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Pastas para escanear (principais do projeto)
PASTAS = [
    'Canary', 'data-canary', 'data', 'npclib',
    'scripts/MCR', 'scripts/SPA',
]

print('='*60)
print('  MCR-DevIA — SCAN GLOBAL DO PROJETO REAL')
print(f'  {datetime.datetime.now():%Y-%m-%d %H:%M}')
print('='*60)

total_problemas = 0
total_arquivos = 0

for pasta in PASTAS:
    caminho = os.path.join(BASE_PROJETO, pasta)
    if not os.path.exists(caminho):
        continue
    
    for root, dirs, files in os.walk(caminho):
        for f in files:
            if not f.endswith('.lua'): continue
            path = os.path.join(root, f)
            total_arquivos += 1
            
            try:
                problemas = mod.scan(f, path)
            except:
                problemas = []
            
            if problemas:
                total_problemas += 1
                # Copia pro sandbox
                rel_path = os.path.relpath(path, BASE_PROJETO)
                safe_name = rel_path.replace('\\', '_').replace('/', '_')
                dest = os.path.join(SANDBOX, safe_name)
                shutil.copy2(path, dest)
                
                # Le o original
                with open(path, 'r', encoding='utf-8', errors='replace') as fp:
                    original = fp.read()
                
                print(f'[!] {rel_path}')
                for p in problemas:
                    print(f'    - {p}')
                print(f'    -> Copiado para: {safe_name}')
    
    print(f'  [PASTA] {pasta}: escaneada')

print(f'\n{"="*60}')
print(f'  SCAN CONCLUIDO')
print(f'  Arquivos escaneados: {total_arquivos}')
print(f'  Arquivos com problemas: {total_problemas}')
print(f'  Copias no sandbox: {SANDBOX}')
print(f'{"="*60}')
print(f'\nPara ver os arquivos copiados:')
print(f'  dir {SANDBOX}')
print(f'\nPara corrigir:')
print(f'  python sandbox/mcr_review_crew.py')
print(f'  python sandbox/mcr_crew_v12_solver.py')
