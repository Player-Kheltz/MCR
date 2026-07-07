#!/usr/bin/env python3
"""Debug NPC extraction."""
import os, re

raiz = r'E:\Projeto MCR\Canary\data-otservbr-global\npc'
total = 0
match = 0
for r, d, fs in os.walk(raiz):
    for f in fs:
        if not f.endswith('.lua'): continue
        total += 1
        fp = os.path.join(r, f)
        with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
            texto = fh.read()
        if re.search(r'Game\.createNpcType\(', texto):
            match += 1
print(f'{total} total, {match} have createNpcType')
