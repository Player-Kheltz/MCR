#!/usr/bin/env python
"""Fix remaining Unicode crashes in edit display lines."""
path = r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix lines 1391, 1406, 1408 - add encoding protection
fixes = {}
for i, line in enumerate(lines):
    if 'print(f' in line and 'linhas[linha_alvo' in line and 'rstrip()' in line and 'encode' not in line:
        # Add encoding protection: .encode('ascii',errors='replace').decode('ascii')
        old = line
        new = line.replace('.rstrip()', ".rstrip().encode('ascii',errors='replace').decode('ascii')")
        if old != new:
            fixes[i] = (old, new)

for idx, (old, new) in fixes.items():
    lines[idx] = new
    print(f'L{idx+1}: fixed')

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

# Verify
try:
    compile(''.join(lines), path, 'exec')
    print(f'OK - {len(fixes)} linhas corrigidas')
except SyntaxError as e:
    print(f'ERRO: {e}')
