#!/usr/bin/env python3
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

t0 = time.time()
from modulos.MCR import MCRPergunta, AutoavaliadorSemantico, MCRSignature
print(f'[{time.time()-t0:.1f}s] Import OK', flush=True)

# Teste rapido sem KG (perguntar com fallback)
p = MCRPergunta(kg=None)
print(f'[{time.time()-t0:.1f}s] MCRPergunta criada', flush=True)

r = p.perguntar("explique SPA", max_tokens=10)
print(f'[{time.time()-t0:.1f}s] Resposta: {r.get("resposta","")[:50]}', flush=True)
print(f'  Nota: {r.get("nota",0)}', flush=True)
print(f'  Chaves: {list(r.keys())[:5]}', flush=True)
print('OK', flush=True)
