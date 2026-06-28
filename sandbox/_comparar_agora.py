#!/usr/bin/env python3
import os, re

BASE = r'E:\Projeto MCR'

testes = ['lore', 'raciocinio', 'arquitetura']

print('='*70)
print('COMPARACAO ATUAL: MCR-DevIA vs Cloud 70B')
print('='*70)

total_mcr = 0
total_cloud = 0

for teste in testes:
    mcr_file = os.path.join(BASE, 'sandbox', f'_resposta_mcr_{teste}.txt')
    cloud_file = os.path.join(BASE, 'sandbox', f'_resposta_cloud_{teste}.txt')
    
    with open(mcr_file, 'r', encoding='utf-8') as f:
        mcr = f.read()
    with open(cloud_file, 'r', encoding='utf-8') as f:
        cloud = f.read()
    
    # Pega corpo (depois do ===)
    mcr_body = mcr.split('='*50)[-1] if '='*50 in mcr else mcr
    cloud_body = cloud
    
    nm = len(set(re.findall(r'\b[A-Z][a-z]{2,}\b', mcr_body)))
    nc = len(set(re.findall(r'\b[A-Z][a-z]{2,}\b', cloud_body)))
    num_mcr = len(re.findall(r'\d+', mcr_body))
    num_cloud = len(re.findall(r'\d+', cloud_body))
    ch_mcr = len(mcr_body)
    ch_cloud = len(cloud_body)
    
    # Detecta idioma
    en_mcr = len(re.findall(r'\b(the|and|this|that|with|from|which|would|could|should)\b', mcr_body.lower()))
    en_cloud = len(re.findall(r'\b(the|and|this|that|with|from|which|would|could|should)\b', cloud_body.lower()))
    pt_mcr = len(re.findall(r'\b(que|para|com|dos|das|uma|pelos|pela|ser|mais)\b', mcr_body.lower()))
    pt_cloud = len(re.findall(r'\b(que|para|com|dos|das|uma|pelos|pela|ser|mais)\b', cloud_body.lower()))
    
    idioma_mcr = 'INGLES' if en_mcr > pt_mcr else 'PORTUGUES'
    idioma_cloud = 'INGLES' if en_cloud > pt_cloud else 'PORTUGUES'
    
    vencedor_nomes = 'MCR' if nm > nc else 'Cloud'
    vencedor_chars = 'MCR' if ch_mcr > ch_cloud else 'Cloud'
    
    if vencedor_nomes == 'MCR': total_mcr += 1
    else: total_cloud += 1
    if vencedor_chars == 'MCR': total_mcr += 1
    else: total_cloud += 1
    
    print(f'\n{teste.upper()}:')
    print(f'  MCR:    {ch_mcr:5d}c {nm:2d} nomes {num_mcr:2d} nums | Idioma: {idioma_mcr}')
    print(f'  Cloud:  {ch_cloud:5d}c {nc:2d} nomes {num_cloud:2d} nums | Idioma: {idioma_cloud}')
    print(f'  Nomes: {vencedor_nomes} | Tamanho: {vencedor_chars}')

print(f'\n{"="*70}')
print(f'PLACAR: MCR {total_mcr} x {total_cloud} Cloud')
print(f'Problemas detectados:')
print(f'  - MCR respondeu em INGLES em LORE e RACIOCINIO (deveria ser PT-BR)')
print(f'  - MCR ARQUITETURA muito curto (457c) - validador cortou')
print(f'  - Conselho esta caindo em debate_protocol em vez de V8 direto')
print(f'{"="*70}')
