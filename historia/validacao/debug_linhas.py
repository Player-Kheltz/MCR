#!/usr/bin/env python3
"""Le as linhas especificas do MCR.py."""
with open(r'E:\Projeto MCR\MCR.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
targets = [847, 922, 946, 1131, 1412, 1510, 1654, 1954, 1988, 2211, 2567, 2836, 2932, 2956, 3265, 3324, 3406, 3413, 3513]
for t in targets:
    if t <= len(lines):
        print(f'{t:5d}: {lines[t-1].rstrip()[:100]}')
