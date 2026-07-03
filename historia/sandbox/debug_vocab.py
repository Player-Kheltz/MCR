#!/usr/bin/env python3
"""Debug do vocab."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRSignature

sig = MCRSignature.extrair_palavras('Ola MCR, aqui e o Kheltz, seu criador')
print('vocab type:', type(sig.get('vocab', None)))
print('vocab len:', len(sig.get('vocab', [])))
print('vocab sample:', list(sig.get('vocab', []))[:5])
print('sequencia len:', len(sig.get('sequencia', [])))
print('n_palavras:', sig.get('n_palavras', 0))
