#!/usr/bin/env python3
"""Compara MCR vs Cloud nos 3 testes."""
import os, re

BASE = r'E:\Projeto MCR'

testes = ['lore', 'raciocinio', 'arquitetura']

for teste in testes:
    mcr_file = os.path.join(BASE, 'sandbox', f'_resposta_mcr_{teste}.txt')
    cloud_file = os.path.join(BASE, 'sandbox', f'_resposta_cloud_{teste}.txt')
    
    with open(mcr_file, 'r', encoding='utf-8') as f:
        mcr = f.read()
    with open(cloud_file, 'r', encoding='utf-8') as f:
        cloud = f.read()
    
    # Pega so o corpo (depois do ===)
    mcr_body = mcr.split('='*50)[-1] if '='*50 in mcr else mcr
    cloud_body = cloud
    
    nm = len(set(re.findall(r'\b[A-Z][a-z]{2,}\b', mcr_body)))
    nc = len(set(re.findall(r'\b[A-Z][a-z]{2,}\b', cloud_body)))
    num_mcr = len(re.findall(r'\d+', mcr_body))
    num_cloud = len(re.findall(r'\d+', cloud_body))
    
    print(f'{teste.upper()}:')
    print(f'  MCR:  {len(mcr_body):5d} chars | {nm:2d} nomes | {num_mcr:2d} nums')
    print(f'  Cloud: {len(cloud_body):5d} chars | {nc:2d} nomes | {num_cloud:2d} nums')
    print(f'  Diferenca nomes: {"MCR+" if nm > nc else "Cloud+"}{abs(nm-nc)}')
    print()
