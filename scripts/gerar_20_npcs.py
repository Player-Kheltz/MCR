#!/usr/bin/env python3
"""Gera 20 NPCs Tier 1 sem LLM — golden templates."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'devia', 'kernel'))

from mcr.mcr_entity_factory import create_entity

npcs = [
    {'type': 'npc', 'name': 'Brunin', 'role': 'ferreiro', 'city': 'Kazordoon'},
    {'type': 'npc', 'name': 'Alita', 'role': 'vendedora', 'city': 'Carlin'},
    {'type': 'npc', 'name': 'Gorn', 'role': 'guarda', 'city': 'Thais'},
    {'type': 'npc', 'name': 'Maris', 'role': 'padeiro', 'city': 'Venore'},
    {'type': 'npc', 'name': 'Rashid', 'role': 'mercador', 'city': 'Svargrond'},
    {'type': 'npc', 'name': 'Xodet', 'role': 'taverneiro', 'city': 'AbDendriel'},
    {'type': 'npc', 'name': 'Teodoro', 'role': 'cavaleiro', 'city': 'Edron'},
    {'type': 'npc', 'name': 'Bucanero', 'role': 'comerciante', 'city': 'Ankh'},
    {'type': 'npc', 'name': 'Eremo', 'role': 'mendigo', 'city': 'Thais'},
    {'type': 'npc', 'name': 'Lily', 'role': 'vendedora', 'city': 'Cormaya'},
    {'type': 'npc', 'name': 'Grizzly', 'role': 'soldado', 'city': 'Darashia'},
    {'type': 'npc', 'name': 'Chondur', 'role': 'tecelao', 'city': 'Svargrond'},
    {'type': 'npc', 'name': 'Nelly', 'role': 'mensageiro', 'city': 'Carlin'},
    {'type': 'npc', 'name': 'Percy', 'role': 'carpinteiro', 'city': 'Kazordoon'},
    {'type': 'npc', 'name': 'Zenobio', 'role': 'artesao', 'city': 'Liberty Bay'},
    {'type': 'npc', 'name': 'Oswald', 'role': 'guarda', 'city': 'Thais'},
    {'type': 'npc', 'name': 'Yaman', 'role': 'guarda costas', 'city': 'Ankh'},
    {'type': 'npc', 'name': 'Humphrey', 'role': 'cocheiro', 'city': 'Edron'},
    {'type': 'npc', 'name': 'Leopold', 'role': 'mercador', 'city': 'Port Hope'},
    {'type': 'npc', 'name': 'TibiaPal', 'role': 'cavaleiro', 'city': 'Venore'},
]

ws = {}
ok = 0
fail = 0
for spec in npcs:
    r = create_entity(spec, ws)
    name = spec['name']
    role = spec['role']
    if r.get('sucesso'):
        ok += 1
        print(f'  OK: {name} ({role})')
    else:
        fail += 1
        print(f'  FAIL: {name}: {r.get("erros", [])}')

print()
print(f'Resultado: {ok} OK, {fail} FAIL, {len(npcs)} total')
