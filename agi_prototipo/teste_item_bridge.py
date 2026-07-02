#!/usr/bin/env python3
"""Teste do MCRItemBridge — busca em qualquer idioma."""
import sys
sys.path.insert(0, ".")
from mcr_npc_bridge import aprender_todos_npcs
from prototipo_agi_completo import MCRByteUtils

brain, ib = aprender_todos_npcs()

print("=== MCRItemBridge: MULTIPLOS IDIOMAS ===")
testes = [
    ("worm", "ingles"),
    ("verme", "portugues"),
    ("sword", "ingles"),
    ("espada", "portugues"),
    ("shield", "ingles"),
    ("escudo", "portugues"),
    ("potion", "ingles"),
    ("pocao", "portugues"),
    ("armor", "ingles"),
    ("armadura", "portugues"),
    ("giant shrimp", "nome composto"),
]

for termo, idioma in testes:
    r = ib.buscar(termo)
    if r:
        melhor = r[0]
        nomes = ", ".join(melhor["nomes"])
        print(f"  [{idioma:10s}] {termo:15s} -> ID {melhor['clientId']:5d}: {nomes:30s} (conf={melhor['conf']:.2f})")
    else:
        print(f"  [{idioma:10s}] {termo:15s} -> nada encontrado")

print()
print("=== APRENDENDO NOVO SINONIMO ===")
ib.aprender_sinonimo("escudo", "shield")
r2 = ib.buscar("escudo")
if r2:
    nomes = ", ".join(r2[0]["nomes"])
    print(f"  'escudo' agora -> ID {r2[0]['clientId']}: {nomes}")

print()
print("=== BUSCA INTEGRADA ===")
for pergunta in ["quanto custa o worm", "quanto custa a espada"]:
    resp = ib.responder_por_dialogo(pergunta, brain)
    safe = resp.encode("ascii", errors="replace").decode("ascii")
    print(f"  '{pergunta}'")
    print(f"    -> {safe[:150]}")
