"""Verificar excepts alterados em kg.py."""
lines = open(r'E:\Projeto MCR\scripts\mcr_devia\modulos\kg.py', 'r', encoding='utf-8').readlines()
for n, l in enumerate(lines, 1):
    if 'except' in l and '(' in l:
        print(f'L{n}: {l.rstrip()}')
        if n < len(lines):
            print(f'L{n+1}: {lines[n].rstrip()}')
        print()
