#!/usr/bin/env python3
"""Verifica se _MCR_DATA foi inserido e carrega corretamente."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

mcr_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'scripts', 'mcr_devia', 'modulos', 'MCR.py'))

# 1. Check if _MCR_DATA exists
with open(mcr_path, 'r', encoding='utf-8') as f:
    content = f.read()
has_data = '_MCR_DATA' in content
print(f'1. _MCR_DATA no arquivo: {has_data}')

# 2. Check if it loads
from modulos.MCR import MCRPersistencia
p = MCRPersistencia(mcr_path)
d = p.carregar_dados()
n_licoes = len(d.get('licoes', []))
n_ass = sum(len(v) for v in d.get('assinaturas', {}).values())
print(f'2. Dados carregados: {n_licoes} lessons, {n_ass} assinaturas')

# 3. Check import still works
import modulos.MCR
print(f'3. Import MCR OK')

# 4. Check tail of file
with open(mcr_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f'4. Total de linhas: {len(lines)}')
print(f'   Ultima linha: {lines[-1].strip()[:60]}')
print(f'   Penultima linha: {lines[-2].strip()[:60]}')
