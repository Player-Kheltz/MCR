#!/usr/bin/env python3
"""Teste _p1_gaps minimo."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print('Criando kg...', flush=True)
from modulos.kg import KnowledgeGraph
kg = KnowledgeGraph()
licoes = kg._get_licoes()
print(f'  Licoes: {len(licoes)}', flush=True)

print('Criando MCRMetaGap...', flush=True)
from modulos.MCR import MCRMetaGap
meta = MCRMetaGap(kg=kg)

print('diagnosticar_gaps...', flush=True)
t0 = time.time()
gaps = meta.diagnosticar_gaps(min_por_prefixo=5)
print(f'  Feito em {time.time()-t0:.1f}s, gaps={len(gaps)}', flush=True)

# Agora cria MCRAutoMelhoria
print('Criando MCRAutoMelhoria...', flush=True)
from modulos.MCR import MCRAutoMelhoria, MCRBridge
bridge = MCRBridge()
print('  bridge.descobrir...', flush=True)
bridge.descobrir()
print('  MCRAutoMelhoria(kg=kg, bridge=bridge)...', flush=True)
t0 = time.time()
am = MCRAutoMelhoria(kg=kg, bridge=bridge)
print(f'  Init em {time.time()-t0:.1f}s', flush=True)
print(f'  am.meta.kg._all_loaded: {am.meta.kg._all_loaded}', flush=True)

print('am._p1_gaps()...', flush=True)
t0 = time.time()
r = am._p1_gaps()
print(f'  Feito em {time.time()-t0:.1f}s, acoes={len(r)}', flush=True)
