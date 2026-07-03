#!/usr/bin/env python3
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

t0 = time.time()
from modulos.MCR import MCRSignature
print(f'[{time.time()-t0:.1f}s] Import', flush=True)

# Test MCRSignature
sig = MCRSignature.extrair('explique SPA')
print(f'[{time.time()-t0:.1f}s] extrair=ent:{sig.get("entropia",0):.2f} est:{sig.get("estados",0)}', flush=True)

sig2 = MCRSignature.extrair('SPA e o sistema de progressao'[:500])
print(f'[{time.time()-t0:.1f}s] extrair2=ent:{sig2.get("entropia",0):.2f} est:{sig2.get("estados",0)}', flush=True)
print('OK', flush=True)
