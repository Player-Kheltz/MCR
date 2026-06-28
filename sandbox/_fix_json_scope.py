#!/usr/bin/env python
"""Fix json scope issue in --json handler by re-importing json locally."""
import sys

path = r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the --json handler and fix the json.load call
for i, line in enumerate(lines):
    if 'cmd_data = json.load(f)' in line:
        lines[i] = line.replace('cmd_data = json.load(f)', 'import json as _json; cmd_data = _json.load(f)')
        print(f'Fix aplicado na L{i+1}')
        break

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

# Verify syntax
try:
    compile(''.join(lines), path, 'exec')
    print('OK - sintaxe valida')
except SyntaxError as e:
    print(f'ERRO: {e}')
    sys.exit(1)
