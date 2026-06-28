#!/usr/bin/env python3
"""Corrige o path do .mcr_conversa.jsonl em kernel.py."""
path = r'E:\Projeto MCR\scripts\mcr_devia\kernel.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = "os.path.join(os.path.dirname(__file__), '..', 'sandbox', '.mcr_conversa.jsonl')"
new = "os.path.join(os.path.dirname(__file__), '..', '..', 'sandbox', '.mcr_conversa.jsonl')"

if old in content:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    try:
        compile(content, path, 'exec')
        print('OK - path corrigido')
    except SyntaxError as e:
        print(f'ERRO: {e}')
else:
    print('Path antigo nao encontrado, verificando...')
    for i, line in enumerate(open(path, encoding='utf-8')):
        if 'mcr_conversa' in line:
            print(f'  L{i+1}: {line.rstrip()}')
