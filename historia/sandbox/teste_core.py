#!/usr/bin/env python3
"""Testa a Equacao MCR pura (MCR_core.py)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia', 'modulos'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from MCR_core import MCR

print('EQUACAO MCR (CORE) - 6 testes', flush=True)

ok = 0
total = 6

# 1. BYTES
mcr_b = MCR('byte')
texto = 'Ola MCR!'
tokens = mcr_b.tokenizar(texto)
mcr_b.aprender_sequencia(list(b'Ola MCR!'))
prox, conf = mcr_b.predizer(tokens[0])
print(f'[1] Byte: {tokens[0]} -> {prox} (esperado: {tokens[1]})', flush=True)
if prox == tokens[1]:
    print('  OK'); ok += 1
else:
    print('  FALHA')

# 2. PALAVRAS  
mcr_p = MCR('palavra')
mcr_p.aprender_sequencia('MCR e uma equacao universal que aprende'.split())
gerado = mcr_p.gerar('MCR', 6)
print(f'[2] Palavra: {" ".join(str(s) for s in gerado)}', flush=True)
if len(gerado) >= 3:
    print('  OK'); ok += 1
else:
    print('  FALHA')

# 3. DECISOES
mcr_d = MCR('decisao')
mcr_d.aprender('explicacao_ok', 'buscar_kg')
mcr_d.aprender('buscar_kg_ok', 'conectar')
dec = mcr_d.predizer('explicacao_ok')
print(f'[3] Decisao: explicacao -> {dec[0]}', flush=True)
if dec[0] == 'buscar_kg':
    print('  OK'); ok += 1
else:
    print('  FALHA')

# 4. GERACAO
mcr_s = MCR('palavra')
mcr_s.aprender_sequencia('SPA e o sistema de progressao do aventureiro'.split())
g = mcr_s.gerar('SPA', 8)
print(f'[4] SPA: {len(g)} tokens', flush=True)
if len(g) >= 4:
    print('  OK'); ok += 1
else:
    print('  FALHA')

# 5. JACCARD
sim1 = MCR.jaccard_bytes('MCR e universal', 'MCR e universal')
sim2 = MCR.jaccard_bytes('MCR e universal', 'Python e legal')
print(f'[5] Jaccard: identicos={sim1:.2f} diferentes={sim2:.2f}', flush=True)
if abs(sim1 - 1.0) < 0.01 and sim1 > sim2:
    print('  OK'); ok += 1
else:
    print('  FALHA')

# 6. ENTROPIA
ent = mcr_b.entropia(tokens[0])
print(f'[6] Entropia: {ent:.2f}', flush=True)
if 0 <= ent <= 5:
    print('  OK'); ok += 1
else:
    print('  FALHA')

print(f'\nResultado: {ok}/{total} testes OK', flush=True)
