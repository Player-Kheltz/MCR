#!/usr/bin/env python3
"""Remove classes nao utilizadas do MCR.py."""
import os, re

mcr_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia', 'modulos', 'MCR.py'))

with open(mcr_path, 'r', encoding='utf-8') as f:
    content = f.read()

original_size = len(content)

# 1. Remove MCRAutoLoop class
start = content.find('\nclass MCRAutoLoop:')
if start > 0:
    end = content.find('\n\n\nclass ', start + 1)
    if end > start:
        block = content[start:end]
        content = content[:start] + content[end:]
        print(f'Removed MCRAutoLoop: {len(block)} chars', flush=True)

# 2. Remove MCRFerramenta class
start = content.find('\nclass MCRFerramenta:')
if start > 0:
    end = content.find('\n\n\nclass ', start + 1)
    if end > start:
        block = content[start:end]
        content = content[:start] + content[end:]
        print(f'Removed MCRFerramenta: {len(block)} chars', flush=True)

# 3. Remove references in the export list
content = content.replace(
    "'MCRRuido', 'MCRDecisor', 'MCRDiagnostico', 'MCRFerramenta',",
    "'MCRRuido', 'MCRDecisor', 'MCRDiagnostico',"
)

with open(mcr_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Reducao total: {original_size - len(content)} chars', flush=True)
print('OK', flush=True)
