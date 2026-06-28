#!/usr/bin/env python3
"""TESTE REAL CEGO: MCR-DevIA vs Cloud 70B.
Passo 1: MCR delibera e salva _resposta_mcr_*.txt
Passo 2: Cloud escreve _resposta_cloud_*.txt (cego)
Passo 3: Compara.
"""
import sys, os, time, re
sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from kernel import MCRKernel
from modulos.conselho import Conselho
import context_crew

BASE = r'E:\Projeto MCR'

TESTS = [
    ("LORE", "Crie uma historia detalhada sobre a cidade de Eridanus no universo MCR, com origem mitologica, fundacao, era de ouro, declinio, personagens principais e segredos ocultos. Inclua nomes proprios de personagens, lugares e artefatos."),
    ("RACIOCINIO", "Analise o seguinte dilema etico: um pesquisador descobriu uma cura que salva milhares de vidas, mas para obte-la violou o consentimento de 10 pessoas. Analise sob as perspectivas kantiana, utilitarista e virtuista. Conclua com uma recomendacao pratica e especifica."),
    ("ARQUITETURA", "Projete a arquitetura de um sistema de IA distribuido globalmente: 5 data centers em 3 continentes, 10.000 requisicoes por segundo, latencia maxima de 200ms, modelos 7B/13B/70B, tolerancia a falhas, custo otimizado. Cite tecnologias REAIS (Redis, Kubernetes, AWS, GCP, etc)."),
]

k = MCRKernel()
k.inicializar()
ctx_crew = context_crew.ContextCrew()
c = Conselho(kg=k.contexto.get('kg'), ia=k.contexto.get('ia'), ctx_crew=ctx_crew)

print('='*80)
print('TESTE CEGO: MCR-DevIA vs Cloud 70B')
print('='*80)

resultados = []

for nome, pergunta in TESTS:
    print(f'\n--- {nome} ---')
    print(f'Pergunta: {pergunta[:80]}...')
    
    t0 = time.time()
    r = c.deliberar(pergunta)
    t_mcr = time.time() - t0
    resposta_mcr = r.get('veredito', '')
    honorarios = r.get('honorarios_criados', [])
    
    mcr_file = os.path.join(BASE, 'sandbox', f'_resposta_mcr_{nome.lower()}.txt')
    with open(mcr_file, 'w', encoding='utf-8') as f:
        f.write(f'PERGUNTA: {pergunta}\n')
        f.write(f'TEMPO: {t_mcr:.0f}s\n')
        f.write(f'HONORARIOS: {honorarios}\n')
        f.write(f'TOOLKIT: Conselho V8, ContextCrew, Auto-revisao\n')
        f.write(f'{"="*50}\n')
        f.write(resposta_mcr)
    
    # Metricas
    chars = len(resposta_mcr)
    nomes = len(set(re.findall(r'\b[A-Z][a-z]{2,}\b', resposta_mcr)))
    nums = len(re.findall(r'\d+', resposta_mcr))
    
    print(f'  MCR: {chars}c, {nomes} nomes, {nums} nums, {t_mcr:.0f}s')
    print(f'  Honorarios: {honorarios}')
    print(f'  Salvo: {mcr_file}')

print(f'\n{"="*80}')
print('PASSO 2: Escreva _resposta_cloud_*.txt (cego, sem ler os arquivos do MCR)')
print('ARQUIVOS:')
for nome, _ in TESTS:
    print(f'  E:\\Projeto MCR\\sandbox\\_resposta_cloud_{nome.lower()}.txt')
print(f'\nPASSO 3: Execute o comparador manualmente')
print(f'{"="*80}')
