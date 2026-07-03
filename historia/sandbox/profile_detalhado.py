#!/usr/bin/env python3
"""Profile detalhado do autoteste."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import *
from modulos.kg import KnowledgeGraph

# Warmup
t0 = time.time()
kg = KnowledgeGraph()
l = kg._get_licoes()
auto = MCRKGAuto(kg)
auto.dedup()
print(f'Warmup KG+dedup: {time.time()-t0:.1f}s', flush=True)

# Tests que demoram
tests = []

t0 = time.time()
bridge = MCRBridge()
bridge.descobrir()
tests.append(('Bridge', time.time()-t0))

t0 = time.time()
fb = MCRFeedback(MCRMestreV2(bridge))
r_fb = fb.processar_com_feedback('Explique SPA', 2)
tests.append(('Feedback', time.time()-t0))

t0 = time.time()
am = MCRAutoMelhoria(kg=None, bridge=bridge)
am_c = am.ciclo()
tests.append(('AutoMelhoria', time.time()-t0))

t0 = time.time()
f = MCRFilosofia()
f.aprender_perguntas_fundamentais()
tests.append(('Filosofia', time.time()-t0))

t0 = time.time()
meta = MCRMetaNivel()
meta.alimentar('Explique SPA'.encode())
meta.diagnosticar()
tests.append(('MetaNivel', time.time()-t0))

t0 = time.time()
a = MCRAutoStart.iniciar()
tests.append(('AutoStart', time.time()-t0))

t0 = time.time()
si = MCRSelfIndex()
si.indexar_tudo()
tests.append(('SelfIndex', time.time()-t0))

t0 = time.time()
MCRSelfHeal.verificar()
tests.append(('SelfHeal', time.time()-t0))

t0 = time.time()
MCRSignature.extrair('Explique SPA')
tests.append(('Signature', time.time()-t0))

t0 = time.time()
sess = MCRSession()
tests.append(('Session', time.time()-t0))

t0 = time.time()
banco = MCRAssinatura()
banco.auto_popular()
tests.append(('Assinatura', time.time()-t0))

t0 = time.time()
web = MCRWebLearn()
web.ciclo_auto_estudo()
tests.append(('WebLearn', time.time()-t0))

t0 = time.time()
MCRGeracao().gerar('Explique SPA')
tests.append(('Geracao', time.time()-t0))

print()
for nome, dt in sorted(tests, key=lambda x: -x[1]):
    print(f'  {nome:15s}: {dt:.2f}s')
print(f'  {"TOTAL":15s}: {sum(dt[1] for dt in tests):.1f}s')
