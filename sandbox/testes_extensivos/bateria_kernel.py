#!/usr/bin/env python3
"""Bateria de testes para o KERNEL (MCR_DevIA-Kernel.py)."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'mcr_devia'))
from kernel import MCRKernel

k = MCRKernel()
k.inicializar()

testes = [
    ("status", [], "Status basico"),
    ("glob", ["*.md", "--max", "2"], "Glob arquivos"),
    ("fast", ["teste rapido"], "Fast classification"),
    ("memoria", ["--stats"], "Memoria stats"),
]

print(f'Testando {len(testes)} comandos no kernel...')
passou = 0
falhou = 0
for cmd, args, nome in testes:
    try:
        t0 = time.time()
        r = k.executar(cmd, args)
        t = time.time() - t0
        if r:
            print(f'  [PASS] {cmd:15s} {nome:30s} ({t:.1f}s)')
            passou += 1
        else:
            print(f'  [FAIL] {cmd:15s} {nome:30s}')
            falhou += 1
    except Exception as e:
        print(f'  [ERRO] {cmd:15s} {nome:30s}: {e}')
        falhou += 1

print(f'\nResultado: {passou}/{len(testes)} passaram, {falhou} falharam')
