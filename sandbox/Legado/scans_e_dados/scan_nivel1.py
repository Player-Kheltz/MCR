"""Nivel 1: Scanner para training_nivel1"""
import os, re

BASE = r'E:\Projeto MCR\sandbox\training_nivel1'

for f in sorted(os.listdir(BASE)):
    if not f.endswith('.lua'): continue
    with open(os.path.join(BASE, f), 'r') as fp:
        c = fp.read()
    
    erros = []
    if c.count('(') != c.count(')'):
        erros.append('parenteses desbalanceados')
    if re.search(r'setHealth\("[^"]+"\)', c):
        erros.append('HP como string')
    if 'Item(' in c and 'setType' not in c:
        erros.append('item sem setType')
    
    if erros:
        print(f'[!] {f}: {", ".join(erros)}')
    else:
        print(f'[OK] {f}')
