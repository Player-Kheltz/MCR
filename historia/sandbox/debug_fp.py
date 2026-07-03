#!/usr/bin/env python3
"""Debug fingerprints."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRSignature, MCRAssinatura

# Extrai fingerprints de 3 textos
textos = [
    'Ola MCR, aqui e o Kheltz, seu criador',
    'O sistema SPA gerencia a progressao do aventureiro',
    'Para compilar o servidor execute cmake',
]

print('=== FINGERPRINTS (MODO FULL) ===')
for i, txt in enumerate(textos):
    sig = MCRSignature.extrair(txt)
    fp = sig.get('fingerprint', [])
    # Mostra os primeiros 12 valores nao-zero
    nao_zero = [(j, v) for j, v in enumerate(fp) if v > 0.1]
    print(f'  Texto {i+1}: {len(fp)} dims, {len(nao_zero)} nao-zero')
    for j, v in nao_zero[:8]:
        print(f'    [{j}] = {v:.2f}')
    print()

# Calcula similaridade entre eles
for i in range(len(textos)):
    for j in range(i+1, len(textos)):
        fpa = MCRSignature.extrair(textos[i]).get('fingerprint', [])
        fpb = MCRSignature.extrair(textos[j]).get('fingerprint', [])
        dot = sum(a*b for a,b in zip(fpa, fpb))
        na = sum(a*a for a in fpa) ** 0.5
        nb = sum(b*b for b in fpb) ** 0.5
        cos = dot / (na * nb) if na*nb > 0 else 0
        print(f'  Cos(texto{i+1}, texto{j+1}) = {cos:.4f}')
