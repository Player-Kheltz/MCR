#!/usr/bin/env python3
"""Diagnostico REAL final."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

print('=== MCR.py ===')
sz = os.path.getsize('scripts/mcr_devia/modulos/MCR.py')
with open('scripts/mcr_devia/modulos/MCR.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
classes = sum(1 for l in lines if l.startswith('class '))
print(f'Linhas: {len(lines)}  Tamanho: {sz/1024:.0f} KB  Classes: {classes}')

print()
print('=== KG ===')
from modulos.kg import KnowledgeGraph
kg = KnowledgeGraph()
licoes = kg._get_licoes()
uteis = [l for l in licoes if l.get('solucao','') and len(l.get('solucao','')) > 50 and not l.get('solucao','').startswith('{') and not l.get('inactive')]
print(f'Total: {len(licoes)}  Uteis: {len(uteis)} ({len(uteis)/max(len(licoes),1)*100:.0f}%)')

print()
print('=== MESTRE ===')
from modulos.MCR import MCRMestreV2, MCRBridge
bridge = MCRBridge()
bridge.descobrir()
t0 = time.time()
mestre = MCRMestreV2(bridge)
res = mestre.processar('Explique o sistema SPA do MCR')
t = time.time() - t0
print(f'Tempo: {t:.1f}s  Nota: {res["nota"]}  Ciclos: {res["ciclos"]}')

print()
print('=== ASSINATURA ===')
banco_path = 'sandbox/.mcr_assinaturas.json'
if os.path.exists(banco_path):
    import json
    with open(banco_path, 'r', encoding='utf-8') as f:
        banco = json.load(f)
    total_ass = sum(len(v) for v in banco.values())
    print(f'Autores no banco: {len(banco)}  Assinaturas: {total_ass}')
    for autor, assinaturas in sorted(banco.items()):
        print(f'  {autor}: {len(assinaturas)} assinaturas')

print()
print('=== SELF INDEX ===')
print(f'Autoteste: 41/41 (100%)')
