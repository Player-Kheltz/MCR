#!/usr/bin/env python
"""Gera TODOS os cmd_*.py a partir dos elifs do mcr_devia.py.
Cria arquivos delegados que chamam de volta o mcr_devia.py.
Isso permite migracao completa sem risco de quebrar nada."""
import os, re, sys

BASE = r'E:\Projeto MCR'
DEVIA_PATH = os.path.join(BASE, 'scripts', 'mcr_devia', 'mcr_devia.py')
COMANDOS_DIR = os.path.join(BASE, 'scripts', 'mcr_devia', 'comandos')

with open(DEVIA_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Mapeia nome do comando -> (linha_inicio, linha_fim, codigo)
comandos = {}
atual = None
for i, line in enumerate(lines):
    m = re.search(r"elif cmd == '(\w+)'", line)
    if m:
        if atual:
            comandos[atual['nome']] = atual
        atual = {'nome': m.group(1), 'inicio': i, 'linhas': [line]}
    elif atual and not line.startswith('elif ') and not line.startswith('if cmd =='):
        atual['linhas'].append(line)
    elif line.startswith('elif ') and not re.search(r"elif cmd == '", line):
        if atual:
            atual['linhas'].append(line)

if atual:
    comandos[atual['nome']] = atual

# Remove comandos especiais
for skip in ['status', 'ensinar']:  # ja existem
    comandos.pop(skip, None)

print(f'Encontrados {len(comandos)} comandos para gerar')

# Template para cada comando delegado
TEMPLATE = '''"""Comando: {nome} - (delegado para mcr_devia.py)"""
import sys, os

_DEVIA = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mcr_devia.py')

def register():
    return {{
        "name": "{nome}",
        "desc": "Delegado para mcr_devia.py",
        "handler": execute,
        "args": [],
        "categoria": "delegado",
    }}

def execute(kg, ia, args, ctx_crew=None):
    """Delega execucao para o mcr_devia.py original."""
    import subprocess
    cmd = [sys.executable, _DEVIA, "{nome}"] + args
    r = subprocess.run(cmd, capture_output=False)
    return r.returncode == 0
'''

gerados = 0
for nome, info in sorted(comandos.items()):
    fpath = os.path.join(COMANDOS_DIR, f'cmd_{nome}.py')
    if os.path.exists(fpath):
        print(f'  PULANDO {nome} (ja existe)')
        continue
    codigo = TEMPLATE.format(nome=nome)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(codigo)
    gerados += 1
    print(f'  GERADO cmd_{nome}.py')

print(f'\nTotal: {gerados} comandos gerados')
print(f'Diretorio: {COMANDOS_DIR}')
