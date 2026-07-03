#!/usr/bin/env python3
"""Teste rapido da refatoracao — step by step."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

t0 = time.time()
print(f'[{time.time()-t0:.1f}s] Importando...')
from modulos.MCR import (
    MCR, MCRSignature, MCRConector, MCRCadeia, MCRPergunta, MCRDecisor,
    MCRPesoNota, MCRThreshold, MCREntropia, AutoavaliadorSemantico,
    _classificar_token,
    _MCR_THRESHOLD_CONF, _MCR_THRESHOLD_TAMANHO, _MCR_THRESHOLD_REPETICAO,
    _MCR_THRESHOLD_PALAVRA, _MCR_THRESHOLD_CONEXAO, _MCR_THRESHOLD_NOTA,
)
print(f'[{time.time()-t0:.1f}s] Importado')

# Teste 1: Threshold
print(f'[{time.time()-t0:.1f}s] Teste 1: Threshold')
t = _MCR_THRESHOLD_CONF.obter('teste', 0.5)
print(f'  obter = {t}')
_MCR_THRESHOLD_CONF.aprender('teste', 0.8)
_MCR_THRESHOLD_CONF.aprender('teste', 0.9)
t2 = _MCR_THRESHOLD_CONF.obter('teste', 0.5)
print(f'  apos aprender = {t2}')
assert t2 > 0.7, f"Threshold: {t2}"

# Teste 2: Autoavaliador
print(f'[{time.time()-t0:.1f}s] Teste 2: Autoavaliador')
av = AutoavaliadorSemantico()
r = av.avaliar("O aventureiro explora a floresta encantada")
print(f'  nota={r["nota"]} diag={r["diagnostico"]}')
assert r['nota'] > 0

# Teste 3: Conector
print(f'[{time.time()-t0:.1f}s] Teste 3: Conector')
c = MCRConector()
c.alimentar("O aventureiro parte em uma jornada", "a")
c.alimentar("A jornada do heroi em Eridanus", "b")
cx = c.conectar("a", "b")
print(f'  nota={cx.get("nota",0)}')
assert cx.get('nota', 0) > 0

# Teste 4: Cadeia
print(f'[{time.time()-t0:.1f}s] Teste 4: Cadeia')
cadeia = MCRCadeia(c)
r = cadeia.gerar("O", n_tokens=10, top_k=3)
print(f'  texto={r["texto"][:40]} nota={r["nota"]}')
assert r['texto']

# Teste 5: Classificar token
print(f'[{time.time()-t0:.1f}s] Teste 5: Classificar')
for tok in ['<|end|>', 'SPA', '123', 'floresta']:
    d = _classificar_token(tok)
    print(f'  {tok:12s} -> {d}')

print(f'\n[{time.time()-t0:.1f}s] TODOS OK')
