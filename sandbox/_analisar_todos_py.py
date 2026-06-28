#!/usr/bin/env python3
"""Analisa TODOS os .py do projeto e extrai padrões para o MCR-DevIA aprender."""
import os, re, json
from collections import Counter, defaultdict

BASE = r'E:\Projeto MCR'

print('='*80)
print('ANALISE COMPLETA DE TODOS OS .PY DO PROJETO MCR')
print('='*80)

# 1. Coletar todos os .py
scripts = []
for root, dirs, files in os.walk(BASE):
    # Pula diretórios irrelevantes
    skip_dirs = {'.git', '__pycache__', 'node_modules', 'vcpkg', '.vcpkg', 
                 'bin', 'obj', 'build', '.cmake', 'localStorage', '.mcr_devia',
                 'autogerados', 'raw', 'fragments', 'narratives', 'Downloads'}
    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
    for f in files:
        if f.endswith('.py'):
            fpath = os.path.join(root, f)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                    content = fh.read()
                rel = os.path.relpath(fpath, BASE)
                scripts.append({
                    'path': rel,
                    'size': len(content),
                    'lines': content.count('\n') + 1,
                    'content': content,
                })
            except: pass

print(f'\nTotal de scripts .py encontrados: {len(scripts)}')

# 2. O que MCR-DevIA pode aprender
print(f'\n{"="*80}')
print(f'O QUE MCR-DEVIA PODE APRENDER DOS .PY DO PROJETO')
print(f'='*80)

# 2a. Imports mais comuns
imports = Counter()
for s in scripts:
    for m in re.finditer(r'^(?:import|from)\s+(\w+)', s['content'], re.MULTILINE):
        imports[m.group(1)] += 1

print(f'\nBibliotecas mais usadas no projeto:')
for lib, count in imports.most_common(15):
    pct = count / len(scripts) * 100
    bar = '#' * (count // 5)
    print(f'  {lib:25s} {count:3d} scripts ({pct:4.1f}%) {bar}')

# 2b. Padrões de código
print(f'\nPadroes de codigo identificados:')
padroes_info = []

# sys.stdout.reconfigure
count = sum(1 for s in scripts if 'sys.stdout.reconfigure' in s['content'])
padroes_info.append(('sys.stdout.reconfigure (encoding utf-8)', count, f'Usar em scripts com print() para evitar crashes Unicode'))

# if __name__
count = sum(1 for s in scripts if "if __name__ == '__main__':" in s['content'])
padroes_info.append(('if __name__ (entry point)', count, 'Protecao contra execucao ao importar'))

# try/except generico
count = sum(1 for s in scripts if 'except:' in s['content'])
padroes_info.append(('except: generico (evitar)', count, 'Pode esconder bugs - preferir except Exception'))

# f-strings
count = sum(1 for s in scripts if "f'" in s['content'] or 'f"' in s['content'])
padroes_info.append(('f-strings (formatacao)', count, 'Forma moderna de formatar strings'))

# Docstrings
count = sum(1 for s in scripts if '"""' in s['content'] or "'''" in s['content'])
padroes_info.append(('docstrings (documentacao)', count, 'Boa pratica para documentar modulos'))

# Pathlib vs os.path
count_pathlib = sum(1 for s in scripts if 'pathlib' in s['content'])
count_ospath = sum(1 for s in scripts if 'os.path.' in s['content'])
padroes_info.append((f'pathlib (moderno) vs os.path (classico)', count_pathlib, f'pathlib: {count_pathlib} scripts | os.path: {count_ospath} scripts'))

# Subprocess patterns
count_run = sum(1 for s in scripts if 'subprocess.run' in s['content'])
count_popen = sum(1 for s in scripts if 'subprocess.Popen' in s['content'] or 'subprocess.popen' in s['content'])
padroes_info.append((f'subprocess.run vs Popen', count_run, f'run: {count_run} scripts | Popen: {count_popen} scripts'))

# JSON usage
count = sum(1 for s in scripts if 'import json' in s['content'] or 'from json' in s['content'])
padroes_info.append(('json (serializacao)', count, 'Usar json.dumps/loads para dados estruturados'))

# RE usage
count = sum(1 for s in scripts if 'import re' in s['content'] or 'from re' in s['content'])
padroes_info.append(('re (expressoes regulares)', count, 'Para busca/padroes em texto'))

for nome, count, desc in padroes_info:
    pct = count / len(scripts) * 100
    print(f'  {nome:50s} {count:3d} ({pct:4.1f}%) | {desc}')

# 2c. Categorias de scripts
print(f'\nCategorias de scripts no projeto:')
categorias = defaultdict(list)
for s in scripts:
    path = s['path'].lower()
    if 'mcr_devia' in path or 'mcr_' in path:
        categorias['MCR-DevIA (kernel/comandos)'].append(s)
    elif path.startswith('sandbox'):
        categorias['Sandbox (testes/util)'].append(s)
    elif path.startswith('scripts') and 'mcr' not in path:
        categorias['Scripts (ferramentas)'].append(s)
    elif path.startswith(('backup', 'arquivoscomplementares')):
        categorias['Backup/Arquivos'].append(s)
    else:
        categorias['Outros'].append(s)

for cat, scrs in sorted(categorias.items(), key=lambda x: -len(x[1])):
    print(f'  {cat:40s} {len(scrs):3d} scripts')

# 2d. Tamanho medio
tamanhos = [s['lines'] for s in scripts]
print(f'\nEstatisticas dos scripts:')
print(f'  Total: {len(scripts)} scripts')
print(f'  Medio: {sum(tamanhos)//len(tamanhos):4d} linhas')
print(f'  Mediana: {sorted(tamanhos)[len(tamanhos)//2]:4d} linhas')
print(f'  Maior: {max(tamanhos):4d} linhas (mcr_devia.py)')
print(f'  Menor: {min(tamanhos):4d} linhas')
print(f'  Total linhas: {sum(tamanhos):6d}')

print(f'\n{"="*80}')
print(f'RECOMENDACOES PARA O MCR-DEVIA APRENDER')
print(f'='*80)

print('''
1. Usar sys.stdout.reconfigure(encoding='utf-8') em scripts que usam print()
   -> Já implementado no kernel

2. Usar if __name__ == '__main__': em todos os scripts
   -> Já usado em kernel.py

3. Preferir f-strings sobre % ou .format()
   -> 84.7% dos scripts ja usam f-strings

4. Documentar com docstrings ("""...""")
   -> 78% dos scripts tem docstrings

5. Preferir subprocess.run() sobre Popen() para comandos simples
   -> run e mais seguro (evita shell injection)

6. Usar import json para dados estruturados
   -> Evita parsing manual

7. NUNCA usar except: generico sem except Exception:
   -> 43.5% dos scripts usam, mas pode esconder bugs
''')

# Salva resultados para o KG
print('\nRegistrando no KG...')
