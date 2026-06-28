#!/usr/bin/env python
"""Gera implementacoes REAIS para todos os comandos modulares.
Le os elifs do mcr_devia.py e adapta para cmd_*.py independentes."""
import os, re, sys

BASE = r'E:\Projeto MCR'
DEVIA = os.path.join(BASE, 'scripts', 'mcr_devia', 'mcr_devia.py')
COMANDOS = os.path.join(BASE, 'scripts', 'mcr_devia', 'comandos')
UTIL = 'from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX'

# Comandos que ja tem implementacao real (nao gerar)
PULOS = {'status', 'ensinar', 'grep', 'fast', 'aprender_conceito', 'refresh', 'perguntar', 'read', 'todo', 'glob'}

# Template para cada comando
TEMPLATE = '''"""Comando: {name} - {desc}"""
import os, sys, json, re, subprocess as _sp
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
{utils}

def register():
    return {
        "name": "{name}",
        "desc": "{desc}",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    {code}
    return True
'''

# Le mcr_devia.py e extrai blocos elif
with open(DEVIA, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

i = 0
comandos_extraidos = {}

while i < len(linhas):
    linha = linhas[i]
    # Procura elif cmd == '...' ou if cmd == '...' (primeiro)
    m = re.match(r"    (?:elif|if) cmd == '(\w+)'", linha)
    if m:
        nome = m.group(1)
        if nome in PULOS:
            i += 1
            continue
        
        # Extrai descricao (proximas linhas de docstring)
        bloco = []
        desc = ''
        j = i + 1
        while j < len(linhas):
            # Pega descricao da docstring
            if linhas[j].strip().startswith('"""') and not desc:
                desc_linha = linhas[j].strip().strip('"""').strip()
                if desc_linha:
                    desc = desc_linha
            elif linhas[j].strip().startswith('Uso:') or linhas[j].strip().startswith('Ex:'):
                if not desc:
                    desc = linhas[j].strip()[:80]
            # Para no proximo elif ou else
            if re.match(r"    (?:elif|else|if cmd ==)", linhas[j]) and j > i:
                break
            bloco.append(linhas[j])
            j += 1
        
        if bloco:
            code = ''.join(bloco).strip()
            if code:
                comandos_extraidos[nome] = {
                    'code': code,
                    'desc': desc or nome,
                }
        i = j
    else:
        i += 1

print(f'Extraidos {len(comandos_extraidos)} comandos do mcr_devia.py')

gerados = 0
for nome, info in sorted(comandos_extraidos.items()):
    fpath = os.path.join(COMANDOS, f'cmd_{nome}.py')
    if os.path.exists(fpath):
        with open(fpath, 'r', encoding='utf-8') as f:
            if 'subprocess' in f.read() and 'mcr_devia' in f.read():
                # So substitui se for delegate (subprocess)
                pass
            else:
                print(f'  PULANDO {nome} (nao e delegate)')
                continue
    
    code = info['code']
    # Remove 4 espacos de indentacao (elif tem 8, execute() tem 4)
    lines = code.split('\n')
    dedented = []
    for ln in lines:
        if ln.startswith('    '):
            dedented.append(ln[4:])
        else:
            dedented.append(ln)
    code = '\n'.join(dedented)
    # Adapta referencias
    code = code.replace('print(f\'[MCR-DevIA]', 'print(f\'[' + nome.capitalize() + ']')
    code = code.replace('print(f\'  [MCR-DevIA]', 'print(f\'  [Comando]')
    
    cmd_code = TEMPLATE
    cmd_code = cmd_code.replace('{name}', nome)
    cmd_code = cmd_code.replace('{desc}', info['desc'][:80].replace('"', "'").replace('\n', ' '))
    cmd_code = cmd_code.replace('{utils}', UTIL)
    cmd_code = cmd_code.replace('{code}', code)
    
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(cmd_code)
    gerados += 1
    print(f'  GERADO cmd_{nome}.py (real)')

print(f'\nTotal: {gerados} comandos com implementacao real')
