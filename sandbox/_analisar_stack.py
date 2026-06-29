"""Analisar kernel.py e encontrar try sem except."""
import re
lines = open(r'E:\Projeto MCR\scripts\mcr_devia\kernel.py', 'r', encoding='utf-8').readlines()
stack = []  # (linha, indent, tipo)
for n, l in enumerate(lines, 1):
    s = l.strip()
    if s == 'try:':
        stack.append(('try', n, len(l) - len(l.lstrip())))
    elif s.startswith('except') or s.startswith('finally'):
        if stack and stack[-1][0] == 'try':
            stack.pop()
        elif stack and stack[-1][0] == 'except':
            stack.pop()
        else:
            stack.append(('except/finally', n, len(l) - len(l.lstrip())))

print('Stack restante (nao fechado):')
for t, n, i in stack:
    print(f'  {t} L{n} (indent {i})')
