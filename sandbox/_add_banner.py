#!/usr/bin/env python3
"""Adiciona banner inicial com lembretes de regras no kernel."""
import os

kpath = r'E:\Projeto MCR\scripts\mcr_devia\kernel.py'
with open(kpath, 'r', encoding='utf-8') as f:
    content = f.read()

banner = '''
    # Banner inicial: lembrete de ler regras
    try:
        _agents_path = os.path.join(os.path.dirname(__file__), '..', '..', 'AGENTS.md')
        _rules_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'rules')
        _has_agents = os.path.exists(_agents_path)
        _rules_files = [f for f in os.listdir(_rules_dir) if f.endswith('.md')] if os.path.exists(_rules_dir) else []
        if _has_agents or _rules_files:
            print('[Regras] Consulte AGENTS.md e docs/rules/ para as regras da equipe')
            if _rules_files:
                print(f'[Regras] Arquivos: {", ".join(sorted(_rules_files))}')
    except: pass

'''

old = '\n    # Processa --json antes de tudo\n    if main_json():'

if old in content:
    content = content.replace(old, banner + old)
    with open(kpath, 'w', encoding='utf-8') as f:
        f.write(content)
    try:
        compile(content, kpath, 'exec')
        print('OK - banner adicionado')
    except SyntaxError as e:
        print(f'ERRO: {e}')
else:
    print('old not found')
    for i, line in enumerate(open(kpath, encoding='utf-8')):
        if 'Processa --json' in line:
            print(f'L{i+1}: {line.rstrip()}')
