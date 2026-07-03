#!/usr/bin/env python3
"""Profile auto_popular em detalhe."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print('MCRAssinatura()...', flush=True)
t0 = time.time()
from modulos.MCR import MCRAssinatura
banco = MCRAssinatura()
print(f'  init={time.time()-t0:.1f}s', flush=True)

print('auto_popular()...', flush=True)
t0 = time.time()
n = banco.auto_popular()
t1 = time.time() - t0
print(f'  auto_popular={t1:.1f}s, novas={n}', flush=True)
print(f'  autores: {len(banco.autores_conhecidos())}', flush=True)

# Testa quicksig
print('rapido extrair...', flush=True)
t0 = time.time()
from modulos.MCR import MCRSignature
for i in range(100):
    MCRSignature.extrair(f'teste {i} rapido', rapido=True)
print(f'  100 rapido em {time.time()-t0:.1f}s', flush=True)

print('full extrair...', flush=True)
t0 = time.time()
for i in range(100):
    MCRSignature.extrair(f'teste {i} full')
print(f'  100 full em {time.time()-t0:.1f}s', flush=True)
