#!/usr/bin/env python3
"""Debug do MCRSignature.extrair."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

print('1: import', flush=True)
import modulos.MCR as mcr_mod
print('2: import OK', flush=True)

print('3: extrair...', flush=True)
t0 = time.time()
try:
    sig = mcr_mod.MCRSignature.extrair('explique SPA')
    print(f'4: extrair OK em {time.time()-t0:.1f}s', flush=True)
    print(f'   ent={sig.get("entropia")} est={sig.get("estados")}', flush=True)
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f'ERRO: {e}', flush=True)
