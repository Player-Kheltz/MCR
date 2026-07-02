#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste do MCRAttention: compara geracao com e sem atencao."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import CerebroAGI, MCRByteUtils
from prototipo_mcr_attention import MCRAttention

c = CerebroAGI()

# Carrega topicos do decathlon se disponivel
rel = os.path.join(os.path.dirname(__file__), '..', 'cache', 'decathlon_report.json')
if os.path.exists(rel):
    with open(rel) as f:
        data = json.load(f)
    print(f'Relatorio decathlon: {data.get("total", "?")}s')

# Alimenta conhecimento
c.alimentar('SPA e o sistema de progressao do aventureiro com dominios elementais Fogo Gelo Terra Energia e Sagrado cada dominio tem 25 niveis', 'spa')
c.alimentar('SHC e o sistema de habilidades contextuais com 5 camadas postura nivel sinergia estado e condicao', 'shc')
c.alimentar('Eridanus e a cidade inicial do projeto MCR construida as margens do Lago Cristalino possui porto praca central templo forja e mercado', 'eridanus')

print(f'Topicos: {len(c.topicos)}')
print()

# Geracao SEM atencao
t0 = time.time()
antes = c._gerar_original('SPA', 6)
t_sem = time.time() - t0
j_sem = MCRByteUtils.jaccard_bytes('SPA', antes)

# Geracao COM atencao
t0 = time.time()
depois = MCRAttention.gerar(c, 'SPA', 6, pergunta='explique o que e SPA')
t_com = time.time() - t0
j_com = MCRByteUtils.jaccard_bytes('SPA', depois)

print('COMPARACAO:')
print(f'  Sem atencao:  "{antes}"  (j={j_sem:.3f}, {t_sem:.4f}s)')
print(f'  Com atencao:  "{depois}" (j={j_com:.3f}, {t_com:.4f}s)')
melhora = ((j_com - j_sem) / max(j_sem, 0.001) * 100)
print(f'  Melhora:      {melhora:.0f}%')
print()

# Evolucao de pesos
print('EVOLUINDO PESOS (10 geracoes)...')
t0 = time.time()
ev = MCRAttention.evoluir_pesos(c, geracoes=10)
t_ev = time.time() - t0
print(f'  Fitness final: {ev["fitness_final"]}')
print(f'  Pesos: {ev["pesos_finais"]}')
print(f'  Tempo: {t_ev:.2f}s')

# Teste final apos evolucao
depois2 = MCRAttention.gerar(c, 'SPA', 6, pergunta='explique SPA')
j2 = MCRByteUtils.jaccard_bytes('SPA', depois2)
print(f'  Apos evolucao: "{depois2}" (j={j2:.3f})')
print()

# Bateria de sementes
print('BATERIA DE SEMENTES:')
for semente in ['SPA', 'Eridanus', 'SHC', 'Fogo', 'MCR']:
    r1 = c._gerar_original(semente, 4)
    r2 = MCRAttention.gerar(c, semente, 4, pergunta=semente)
    j1 = MCRByteUtils.jaccard_bytes(semente, r1)
    j2 = MCRByteUtils.jaccard_bytes(semente, r2)
    status = '+' if j2 > j1 else '-'
    print(f'  {status} {semente:10s}: antigo="{r1[:25]:25s}" j={j1:.2f} | novo="{r2[:25]:25s}" j={j2:.2f}')

print()
print('TESTE CONCLUIDO')
