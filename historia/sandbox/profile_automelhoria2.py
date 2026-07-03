#!/usr/bin/env python3
"""Profile cada sub-metodo do MCRAutoMelhoria."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRAutoMelhoria, MCRBridge

bridge = MCRBridge()
bridge.descobrir()
melhoria = MCRAutoMelhoria(kg=None, bridge=bridge)
t_global = time.time()

for nome, fn in [
    ("_p1_gaps", melhoria._p1_gaps),
    ("_p2_lento", melhoria._p2_lento),
    ("_p7_esqueceu", melhoria._p7_esqueceu),
    ("_p3_repetiu", melhoria._p3_repetiu),
    ("_p4_errou", melhoria._p4_errou),
    ("_p5_aprendeu", melhoria._p5_aprendeu),
    ("_p6_precisa", melhoria._p6_precisa),
]:
    t0 = time.time()
    try:
        r = fn()
        n = len(r) if isinstance(r, (list, tuple)) else r
    except Exception as e:
        n = f"ERRO: {e}"
    dt = time.time() - t0
    status = ">> LENTO" if dt > 5 else ""
    print(f'[{time.time()-t_global:.1f}s] {nome:15s} {dt:6.1f}s -> {n} {status}', flush=True)

print(f'\nTotal ciclo(): {time.time()-t_global:.1f}s', flush=True)
