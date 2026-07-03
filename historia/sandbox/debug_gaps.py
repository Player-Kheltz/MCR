#!/usr/bin/env python3
"""Debug _p1_gaps."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print('1: import', flush=True)
from modulos.MCR import MCRMetaGap, _get_kg

print('2: kg', flush=True)
kg = _get_kg()

print('3: MCRMetaGap', flush=True)
meta = MCRMetaGap(kg=kg)

print('4: diagnosticar_gaps', flush=True)
t0 = time.time()
gaps = meta.diagnosticar_gaps(min_por_prefixo=5)
t1 = time.time() - t0
print(f'5: gaps={len(gaps)} em {t1:.1f}s', flush=True)
for g in gaps[:5]:
    print(f'   {g}', flush=True)
