#!/usr/bin/env python
"""Remove truncation from rstrip() in read command display."""
path = r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# L1139: read command display - remove [:160]
content = content.replace(
    "linhas[i].rstrip()[:160].encode('ascii', errors='replace').decode('ascii')",
    "linhas[i].rstrip().encode('ascii', errors='replace').decode('ascii')"
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

# Verify syntax
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
try:
    compile(''.join(lines), path, 'exec')
    print('OK')
except SyntaxError as e:
    print(f'Erro: {e}')
