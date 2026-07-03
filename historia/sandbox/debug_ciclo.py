#!/usr/bin/env python3
"""Debug cada passo do ciclo com stdout flush."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRBridge, MCRAutoMelhoria

bridge = MCRBridge()
bridge.descobrir()
m = MCRAutoMelhoria(kg=None, bridge=bridge)

for nome in ['_p1_gaps', '_p2_lento', '_p7_esqueceu', '_p3_repetiu', '_p4_errou', '_p5_aprendeu', '_p6_precisa']:
    t0 = time.time()
    print(f'{nome}...', flush=True, end='')
    try:
        fn = getattr(m, nome)
        r = fn()
        dt = time.time() - t0
        print(f' {dt:.1f}s -> {len(r) if isinstance(r,(list,tuple)) else r}', flush=True)
    except Exception as e:
        dt = time.time() - t0
        print(f' {dt:.1f}s ERRO: {e}', flush=True)
