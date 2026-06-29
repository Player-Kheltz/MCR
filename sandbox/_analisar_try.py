"""Analisar pares try/except em kernel.py."""
lines = open(r'E:\Projeto MCR\scripts\mcr_devia\kernel.py', 'r', encoding='utf-8').readlines()
pairs = []
for n, l in enumerate(lines, 1):
    s = l.strip()
    if s == 'try:':
        pairs.append(('try', n, len(l) - len(l.lstrip())))
    if s.startswith('except') or s.startswith('finally'):
        pairs.append(('except/finally', n, len(l) - len(l.lstrip())))

print('Match pairs:')
for t, n, i in pairs:
    print(f'  {t} L{n} (indent {i})')
