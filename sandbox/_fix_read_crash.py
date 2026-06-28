#!/usr/bin/env python
"""Fix MCR-DevIA read command crash on emoji files."""
import sys

path = r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 1139 (0-indexed 1138) - was corrupted by previous failed edit
new_line = "                print(f'  L{i+1}: {linhas[i].rstrip()[:160].encode(\"ascii\", errors=\"replace\").decode(\"ascii\")}')\n"
lines[1138] = new_line

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

# Verify syntax
try:
    compile(''.join(lines), path, 'exec')
    print('OK - sintaxe valida')
except SyntaxError as e:
    print(f'ERRO de sintaxe: {e}')
    sys.exit(1)
