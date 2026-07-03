#!/usr/bin/env python3
"""Diagnostico real de qualidade."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRMestreV2, MCRPesoNota, MCRThreshold, MCRPergunta, MarkovUniversal

print('=== MCRMestreV2 — RESPOSTA REAL ===')
mestre = MCRMestreV2()
res = mestre.processar('Explique o sistema SPA do MCR')
resp = res['resposta'][:200]
print(f'Resposta: {resp}')
print(f'Nota: {res["nota"]}/10')
print(f'Fluxo: {res["fluxo"]}')
print(f'Tempo: {res["tempo"]}s')

print()
print('=== MCRPesoNota — PESOS APRENDIDOS ===')
pn = MCRPesoNota('teste')
pn.aprender({'byte':0.9,'palavra':0.1,'token':0.2}, 2.0)
pn.aprender({'byte':0.8,'palavra':0.15,'token':0.3}, 2.5)
pn.aprender({'byte':0.4,'palavra':0.7,'token':0.8}, 8.0)
pn.aprender({'byte':0.3,'palavra':0.8,'token':0.6}, 7.5)
n1 = pn.calcular(byte_s=8.5, palavra_s=1.5, token_s=2.0)
n2 = pn.calcular(byte_s=4.0, palavra_s=7.5, token_s=7.0)
print(f'JSON (byte alto): {n1:.1f}/10')
print(f'Texto ok: {n2:.1f}/10')
print(f'Diferenca: {n2-n1:.1f} pontos (quanto maior, melhor)')

print()
print('=== MCRThreshold — ADAPTATIVO ===')
t = MCRThreshold()
for v in [0.1, 0.12, 0.08, 0.15, 0.09, 0.11, 0.13]:
    t.observar(v)
print(f'Loop threshold: {t.calcular(0.5):.3f}')

t2 = MCRThreshold()
for v in [0.82, 0.88, 0.85, 0.79, 0.91, 0.84, 0.87]:
    t2.observar(v)
print(f'Dedup threshold: {t2.calcular(1.0):.3f}')

print()
print('=== MCRPergunta — RESPOSTA ===')
mp = MCRPergunta()
res2 = mp.perguntar('O que e Eridanus', max_tokens=30)
print(f'Nota: {res2["nota"]}/10')
print(f'Resposta: {res2["resposta"][:200]}')
