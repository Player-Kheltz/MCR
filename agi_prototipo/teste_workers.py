#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testa cada worker do decathlon individualmente."""
import sys, os, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Worker 1: RL
print("Testando worker_rl (500 eps)...")
t0 = time.time()
from mcr_decathlon import worker_rl
from prototipo_agi_completo import EstadoMundo
e0 = EstadoMundo.criar_simples()
import copy
eg = copy.deepcopy(e0)
eg.get("heroi").props["x"] = 4
eg.get("heroi").props["y"] = 4
mk = worker_rl(0, 500, e0, eg)
print(f"  OK: {mk.total} transicoes em {time.time()-t0:.2f}s")

# Worker 2: Conhecimento
print("Testando worker_conhecimento...")
t0 = time.time()
from mcr_decathlon import worker_conhecimento, coletar_arquivos
base = os.path.dirname(__file__)
arquivos = coletar_arquivos(base, "py", 50)
if arquivos:
    result = worker_conhecimento(arquivos)
    mb, mp, mt, tc, mundo = result
    print(f"  OK: {mb.total} bytes, {mp.total} palavras, {len(tc)} topicos em {time.time()-t0:.2f}s")

# Worker 5: Ambiente
print("Testando worker_ambiente (500 ticks)...")
t0 = time.time()
from mcr_decathlon import worker_ambiente
stats = worker_ambiente(500)
print(f"  OK: {stats['tiles']} tiles, {stats['entidades']} entidades em {time.time()-t0:.2f}s")

# Worker 6: Memoria
print("Testando worker_memoria (500 inserts)...")
t0 = time.time()
from mcr_decathlon import worker_memoria
count = worker_memoria(500, 1)
print(f"  OK: {count} inserts em {time.time()-t0:.2f}s")

# Worker 3: Bridge
print("Testando worker_bridge (3 analogias)...")
t0 = time.time()
from mcr_decathlon import worker_bridge
pares = [("fogo queima", "fogo queima madeira", "gelo congela", "gelo congela agua")]
r = worker_bridge(pares)
print(f"  OK: {len(r)} analogias em {time.time()-t0:.2f}s")

# Worker 4: Genesis
print("Testando worker_genesis...")
t0 = time.time()
from mcr_decathlon import worker_genesis
g = worker_genesis(0)
print(f"  OK: {g['gaps']} gaps em {time.time()-t0:.2f}s")

print("\nTODOS OS WORKERS OK")
