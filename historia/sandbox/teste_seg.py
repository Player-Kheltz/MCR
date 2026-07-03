#!/usr/bin/env python3
"""Teste MCRSegmentador."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRSegmentador
from collections import Counter

mcr_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia', 'modulos', 'MCR.py'))

seg = MCRSegmentador()
seg.estudar_se(mcr_path)

tipos = Counter(t[0] for t in seg._linhas_info)
print('Tipos:', dict(tipos))

print('\nUltimas 30 linhas nao-branco:')
for tipo, num, conteudo in seg._linhas_info:
    if tipo != 'BLANK':
        print(f'  {num}: {tipo:8s} -> {conteudo[:80]}')

print(f'\nBlocos de dados encontrados: {seg.encontrar_dados()}')
