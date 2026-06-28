#!/usr/bin/env python3
"""Adiciona comando --chat no kernel."""
path = r'E:\Projeto MCR\scripts\mcr_devia\kernel.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "if cmd == 'listar':" in line:
        lines.insert(i, "    if cmd == '--chat':\n")
        lines.insert(i+1, "        print('[Chat] Modo chat ativado')\n")
        lines.insert(i+2, "        return\n")
        break

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

try:
    compile(''.join(lines), path, 'exec')
    print('OK')
except SyntaxError as e:
    print('ERRO:', e)
