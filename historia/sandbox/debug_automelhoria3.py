#!/usr/bin/env python3
"""Debug bridge + init da MCRAutoMelhoria."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print('1: import', flush=True)
from modulos.MCR import MCRBridge

t0 = time.time()
print('2: MCRBridge()', flush=True)
bridge = MCRBridge()
print(f'   init={time.time()-t0:.1f}s', flush=True)

t0 = time.time()
print('3: descobrir()', flush=True)
bridge.descobrir()
print(f'   descobrir={time.time()-t0:.1f}s', flush=True)

t0 = time.time()
print('4: MCRAutoMelhoria(kg=None, bridge=bridge)', flush=True)
from modulos.MCR import MCRAutoMelhoria
melhoria = MCRAutoMelhoria(kg=None, bridge=bridge)
print(f'   init_melhoria={time.time()-t0:.1f}s', flush=True)

t0 = time.time()
print('5: ciclo()', flush=True)
r = melhoria.ciclo()
print(f'   ciclo={time.time()-t0:.1f}s', flush=True)
print(f'   acoes={r["n"]}', flush=True)
