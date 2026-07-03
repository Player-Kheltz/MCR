#!/usr/bin/env python3
"""Teste de tempo do Mestre apos otimizacao."""
import sys, time, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRMestreV2, MCRBridge

bridge = MCRBridge()
bridge.descobrir()

t0 = time.time()
mestre = MCRMestreV2(bridge)
res = mestre.processar('Explique o sistema SPA do MCR')
t = time.time() - t0

print(f'Tempo: {t:.1f}s (antes era 23.3s)')
print(f'Nota: {res["nota"]}')
print(f'Ciclos: {res["ciclos"]}')
print(f'Resposta: {res["resposta"][:80]}')
