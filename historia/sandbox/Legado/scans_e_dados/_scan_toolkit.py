#!/usr/bin/env python3
"""Escaneia sandbox/ por scripts que podem ser toolkit perdidos."""
import os, re

BASE = r'E:\Projeto MCR'
SANDBOX = os.path.join(BASE, 'sandbox')
EXISTENTES = set()

# Carrega toolkit atual
with open(os.path.join(BASE, 'scripts', 'mcr_devia', 'modulos', 'toolkit.py'), 'r', encoding='utf-8') as f:
    tk_content = f.read()

# Extrai nomes de comandos ja listados
for m in re.finditer(r'"(\w+)":\s*"', tk_content):
    EXISTENTES.add(m.group(1))

print(f'Comandos ja no toolkit: {len(EXISTENTES)}')
print()

# Escaneia sandbox por scripts .py
print('='*80)
print('SCRIPTS NO SANDBOX (possiveis toolkits perdidos)')
print('='*80)

categorias = {
    'cmd_': 'Comando MCR',
    'mcr_': 'Modulo/Script MCR',
    'auto_': 'Automacao',
    'fix_': 'Correcao',
    'test_': 'Teste',
    'corrida_': 'Corrida/Teste',
    'resolver_': 'Utilitario',
    'thinker_': 'Thinker/IA',
    'gerador_': 'Gerador',
}

found_scripts = []
for f in sorted(os.listdir(SANDBOX)):
    if not f.endswith('.py') or f.startswith('_') or f.startswith('.'):
        continue
    fpath = os.path.join(SANDBOX, f)
    size = os.path.getsize(fpath)
    
    # Le primeiras linhas para identificar
    with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
        header = fh.read(500)
    
    # Classifica
    nome_base = f[:-3]
    if nome_base in EXISTENTES:
        continue
    
    # Verifica se parece um comando/ferramenta vs script auxiliar
    tem_main = 'if __name__' in header
    tem_register = 'def register' in header
    tem_classe = re.search(r'^class\s+\w+', header, re.MULTILINE)
    tem_funcao = re.search(r'^def \w+', header, re.MULTILINE)
    
    relevancia = 0
    if tem_register: relevancia += 3  # Comando MCR
    if tem_main: relevancia += 1
    if tem_classe: relevancia += 1
    if tem_funcao: relevancia += 1
    
    # Determina categoria
    cat = 'Outro'
    for prefixo, nome_cat in categorias.items():
        if f.startswith(prefixo):
            cat = nome_cat
            break
    
    found_scripts.append((f, size, cat, relevancia, tem_register))

# Mostra por relevancia
print(f'\n{"Script":40s} {"Tam":>6s} {"Categoria":20s} {"Relev":>4s} {"Tipo":10s}')
print('-'*80)
relevantes = [s for s in found_scripts if s[3] >= 2]
baixos = [s for s in found_scripts if s[3] < 2]

for f, sz, cat, rel, reg in relevantes:
    tipo = 'COMANDO' if reg else 'MODULO'
    print(f'{f:40s} {sz:6d} {cat:20s} {rel:4d} {tipo:10s}')

if baixos:
    print(f'\n... e {len(baixos)} scripts de baixa relevancia (provavelmente descartaveis)')

# Recomendacoes
print(f'\n{"="*80}')
print('RECOMENDACOES')
print(f'{"="*80}')
for f, sz, cat, rel, reg in relevantes:
    if reg and f.startswith('cmd_'):
        nome = f[4:-3]
        if nome not in EXISTENTES:
            print(f'  ADICIONAR: {nome} ({f}) - comando MCR encontrado mas nao no toolkit')
    elif reg:
        nome = f[:-3]
        if nome not in EXISTENTES:
            print(f'  VERIFICAR: {nome} ({f}) - contem register(), possivel comando')

print(f'\nTotal scripts no sandbox: {len(found_scripts)}')
print(f'Ja no toolkit: {len(EXISTENTES)}')
