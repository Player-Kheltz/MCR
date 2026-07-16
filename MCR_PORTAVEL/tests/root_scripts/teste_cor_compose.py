#!/usr/bin/env python3
"""Teste de geracao de cor com compose_state."""
import sys, os, numpy as np
from PIL import Image
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcr.mcr_sprite_motor import MCRSpriteMotor
from mcr.sprite_corpus import carregar_categoria, extrair_grid_papel

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

OUT = Path(os.path.join(_BASE, 'poc_output', 'pipeline_universal'))
OUT.mkdir(parents=True, exist_ok=True)

motor = MCRSpriteMotor()
sps = carregar_categoria('armors', max_sprites=10)
gp_r, gc_r = extrair_grid_papel(sps[0])
motor.treinar(sps, 'armors')

# Inspecionar tokens de cor no banco
print("Exemplos de transicoes de cor:")
cur = motor.mk_cor.conn.execute("SELECT key, next FROM trans LIMIT 15")
for row in cur.fetchall():
    key = row[0]
    nxt = row[1][:30] if row[1] else 'N/A'
    print("  %s -> %s" % (key, nxt))

print("\nTotal estados de cor:")
cur = motor.mk_cor.conn.execute("SELECT COUNT(*) FROM freq")
print("  %d" % cur.fetchone()[0])

# Ver se o token 'C' existe no banco
cur = motor.mk_cor.conn.execute("SELECT COUNT(*) FROM freq WHERE key = 'cor|C'")
print("Token 'C' existe?: %d" % cur.fetchone()[0])

# Listar alguns tokens que comecam com 'cor|C'
cur = motor.mk_cor.conn.execute("SELECT key FROM freq WHERE key LIKE 'cor|C%' LIMIT 10")
print("\nExemplos de tokens 'C*' no banco:")
for row in cur.fetchall():
    print("  %s" % row[0])

# Gerar com semente real do banco
cur = motor.mk_cor.conn.execute("SELECT key FROM freq WHERE key LIKE 'cor|C%' LIMIT 1")
seed_row = cur.fetchone()
if seed_row:
    seed = seed_row[0]
    print("\nUsando semente: %s" % seed)
    pred, conf = motor.mk_cor.predizer(seed)
    print("Predicao: %s (conf=%.2f)" % (pred[:30] if pred else 'N/A', conf))
else:
    print("\nNenhum token 'C*' encontrado no banco!")
    # Ver o que existe
    cur = motor.mk_cor.conn.execute("SELECT key FROM freq LIMIT 5")
    for row in cur.fetchall():
        print("  key: %s" % row[0])
