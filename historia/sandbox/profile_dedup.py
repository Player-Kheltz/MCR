#!/usr/bin/env python3
"""Profile do dedup para achar gargalo."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

t0 = time.time()

# 1. Load KG
from modulos.kg import KnowledgeGraph
kg = KnowledgeGraph()
licoes = kg._get_licoes()
print(f'[{time.time()-t0:.1f}s] KG carregado: {len(licoes)} lessons', flush=True)

# 2. Check cache
from modulos.kg import _KG_CACHE
print(f'[{time.time()-t0:.1f}s] _KG_CACHE checksum: {_KG_CACHE.get("checksum", "None")[:16]}...', flush=True)

# 3. Time dedup
from modulos.MCR import MCRKGAuto
auto_kg = MCRKGAuto(kg)

t1 = time.time()
n = auto_kg.dedup()
t2 = time.time() - t1
print(f'[{time.time()-t0:.1f}s] Dedup: {n} removidas em {t2:.1f}s', flush=True)

# 4. Check how many lessons per bucket
sol_counts = 0
for l in licoes:
    if l.get('solucao', '') and len(l.get('solucao', '')) > 30:
        sol_counts += 1
print(f'[{time.time()-t0:.1f}s] Lessons com solucao: {sol_counts}', flush=True)

# 5. Time just the hash bucketing
t1 = time.time()
buckets = {}
for i, l in enumerate(licoes):
    sol = l.get('solucao', '')
    if not sol or len(sol) < 30: continue
    h = hash(sol[:100]) % 50
    buckets.setdefault(h, []).append(i)
t2 = time.time() - t1
print(f'[{time.time()-t0:.1f}s] Hash bucketing: {t2:.2f}s, {len(buckets)} buckets', flush=True)
for h, g in sorted(buckets.items())[:5]:
    print(f'  bucket {h}: {len(g)} lessons')

# 6. Time Jaccard comparisons for largest bucket
import random
largest_h = max(buckets, key=lambda k: len(buckets[k]))
largest_group = buckets[largest_h]
print(f'[{time.time()-t0:.1f}s] Maior bucket: h={largest_h} com {len(largest_group)} lessons', flush=True)
