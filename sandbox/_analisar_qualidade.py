#!/usr/bin/env python3
"""Analise QUALITATIVA real das respostas MCR vs Cloud."""
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
    
    mcr_body = mcr.split('='*50)[-1] if '='*50 in mcr else mcr
    cloud_body = cloud
    
    print(f'\n{"="*80}')
    print(f'{teste.upper()} - ANALISE QUALITATIVA')
    print(f'{"="*80}')
    
    # 1. COERENCIA INTERNA
    # Verifica se os nomes mencionados sao consistentes (nao mudam no meio do texto)
    nomes_mcr = re.findall(r'\b[A-Z][a-z]{2,}\b', mcr_body)
    nomes_cloud = re.findall(r'\b[A-Z][a-z]{2,}\b', cloud_body)
    
    nomes_unicos_mcr = set(nomes_mcr)
    nomes_unicos_cloud = set(nomes_cloud)
    
    print(f'\n  Nomes unicos: MCR={len(nomes_unicos_mcr)} Cloud={len(nomes_unicos_cloud)}')
    
    # 2. CONSISTENCIA (nomes repetidos = historia coesa)
    if len(nomes_mcr) > 0:
        ratio_mcr = len(nomes_mcr) / len(nomes_unicos_mcr) if nomes_unicos_mcr else 0
    else:
        ratio_mcr = 0
    if len(nomes_cloud) > 0:
        ratio_cloud = len(nomes_cloud) / len(nomes_unicos_cloud) if nomes_unicos_cloud else 0
    else:
        ratio_cloud = 0
    print(f'  Consistencia nomes (repeticoes): MCR={ratio_mcr:.1f}x Cloud={ratio_cloud:.1f}x')
    
    # 3. PALAVRAS GENERICAS (evitar)
    genericas = ['coisa', 'algo', 'muito', 'bem', 'fazer', 'ter', 'ser', 'ficar']
    gen_mcr = sum(1 for g in genericas if g in mcr_body.lower())
    gen_cloud = sum(1 for g in genericas if g in cloud_body.lower())
    print(f'  Palavras genericas: MCR={gen_mcr} Cloud={gen_cloud}')
    
    # 4. ANALISE SEMANTICA (detecta contradicoes internas)
    # Exemplo: se menciona "Lorentia" e depois "Zephyria" sem relacao, pode ser inconsistente
    # (Heuristica simples: verifica se nomes tem sobreposicao de contexto)
    
    # 5. VERACIDADE (para raciocinio e arquitetura - faz sentido?)
    if teste == 'raciocinio':
        mcr_tem_kant = 'kant' in mcr_body.lower()
        mcr_tem_utilit = 'utilitar' in mcr_body.lower()
        mcr_tem_virt = 'virtu' in mcr_body.lower() or 'aristot' in mcr_body.lower()
        cloud_tem_kant = 'kant' in cloud_body.lower()
        cloud_tem_utilit = 'utilitar' in cloud_body.lower()
        cloud_tem_virt = 'virtu' in cloud_body.lower() or 'aristot' in cloud_body.lower()
        print(f'  Perspectivas eticas:')
        print(f'    Kantiana: MCR={"Sim" if mcr_tem_kant else "Nao"} Cloud={"Sim" if cloud_tem_kant else "Nao"}')
        print(f'    Utilitarista: MCR={"Sim" if mcr_tem_utilit else "Nao"} Cloud={"Sim" if cloud_tem_utilit else "Nao"}')
        print(f'    Virtuista: MCR={"Sim" if mcr_tem_virt else "Nao"} Cloud={"Sim" if cloud_tem_virt else "Nao"}')
    
    if teste == 'arquitetura':
        # Verifica se menciona tecnologias reais
        techs = ['redis', 'kubernetes', 'k8s', 'docker', 'aws', 'gcp', 'azure', 'nginx', 'postgres', 'mongodb']
        tech_mcr = sum(1 for t in techs if t in mcr_body.lower())
        tech_cloud = sum(1 for t in techs if t in cloud_body.lower())
        print(f'  Tecnologias reais mencionadas: MCR={tech_mcr} Cloud={tech_cloud}')
    
    # 6. ESTRUTURA
    mcr_tem_estrutura = bool(re.search(r'\d\)|Cap.tulo|#|\.\n\n', mcr_body))
    cloud_tem_estrutura = bool(re.search(r'\d\)|Cap.tulo|#|\.\n\n', cloud_body))
    print(f'  Estruturado: MCR={"Sim" if mcr_tem_estrutura else "Nao"} Cloud={"Sim" if cloud_tem_estrutura else "Nao"}')
    
    print(f'\n  AMOSTRA MCR: {mcr_body[:150]}...')
    print(f'  AMOSTRA Cloud: {cloud_body[:150]}...')
