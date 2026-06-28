#!/usr/bin/env python3
"""Corrige indentacao do banner no kernel.py."""
path = r'E:\Projeto MCR\scripts\mcr_devia\kernel.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixes = {
    309: 16,  # if os.path.exists
    310: 20,  # with open
    311: 24,  # _lines = 
    312: 20,  # import json
    313: 20,  # for _l
    314: 24,  # if _l.strip
    315: 28,  # _d = json.loads
    316: 28,  # if _d.get
    317: 32,  # _ctx_ultimo =
    318: 32,  # break
}

for idx, spaces in fixes.items():
    if idx < len(lines):
        lines[idx] = ' ' * spaces + lines[idx].strip() + '\n'

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

try:
    compile(''.join(lines), path, 'exec')
    print('OK')
except SyntaxError as e:
    print('ERRO:', e)
