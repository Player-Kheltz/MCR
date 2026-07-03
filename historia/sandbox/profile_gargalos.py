#!/usr/bin/env python3
"""Profiling dos gargalos do autoteste."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

t_global = time.time()

print(f'[{0:.1f}s] Iniciando profile...', flush=True)

# 1. MCRAutoStart
from modulos.MCR import MCRAutoStart
MCRAutoStart._cache_checksum = None
t0 = time.time()
r = MCRAutoStart.iniciar()
t_auto = time.time() - t0
print(f'[{time.time()-t_global:.1f}s] 1. MCRAutoStart: {t_auto:.1f}s', flush=True)
print(f'    Acoes: {r.get("acoes",[])[:5]}', flush=True)

# 2. KG lessons count
from modulos.kg import KnowledgeGraph
t0 = time.time()
kg = KnowledgeGraph()
licoes_all = kg._get_licoes() if hasattr(kg, '_get_licoes') else []
t_kg = time.time() - t0
print(f'[{time.time()-t_global:.1f}s] 2. KG init: {t_kg:.1f}s ({len(licoes_all)} lessons)', flush=True)

# 3. MCRFuel
from modulos.MCR import MCRFuel
t0 = time.time()
fuel = MCRFuel()
n_fuel = fuel.abastecer_se_precisar(min_uteis=200)
t_fuel = time.time() - t0
print(f'[{time.time()-t_global:.1f}s] 3. MCRFuel: {t_fuel:.1f}s (+{n_fuel})', flush=True)

# 4. MCRMetaGap
from modulos.MCR import MCRMetaGap
t0 = time.time()
meta = MCRMetaGap()
gaps = meta.diagnosticar_gaps(min_por_prefixo=2)
t_gap = time.time() - t0
print(f'[{time.time()-t_global:.1f}s] 4. MCRMetaGap: {t_gap:.1f}s ({len(gaps)} gaps)', flush=True)

# 5. MCRWebLearn
from modulos.MCR import MCRWebLearn
t0 = time.time()
web = MCRWebLearn()
n_web = web.estudar_gaps(1)
t_web = time.time() - t0
print(f'[{time.time()-t_global:.1f}s] 5. MCRWebLearn: {t_web:.1f}s ({n_web} estudados)', flush=True)

# Resumo
print(f'\n=== RESUMO DOS GARGALOS ===')
print(f'  1. MCRAutoStart: {t_auto:.1f}s  (O(n²) dedup)')
print(f'  2. KG init:      {t_kg:.1f}s')
print(f'  3. MCRFuel:      {t_fuel:.1f}s  (scan de arquivos)')
print(f'  4. MCRMetaGap:   {t_gap:.1f}s')
print(f'  5. MCRWebLearn:  {t_web:.1f}s  (web request)')
print(f'  TOTAL: {time.time()-t_global:.1f}s')
