#!/usr/bin/env python
"""Remove [:N] truncation from rstrip() in print statements."""
import re

path = r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove [:N] truncation from rstrip() in print statements only
# Pattern: rstrip()[:N] where N is digits
old = 'rstrip()[:200]'
new = 'rstrip()'
count = content.count(old)
if count:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'{count} ocorrencias alteradas')
else:
    print('Nenhuma ocorrencia encontrada')
