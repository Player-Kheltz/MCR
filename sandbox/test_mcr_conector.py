#!/usr/bin/env python3
"""Teste rapido do MCRConector."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRConector

c = MCRConector()
c.alimentar('SPA = Sistema de Progressao do Aventureiro. Gerencia habilidades em dominios elementais.', 'spa')
c.alimentar('Eridanus era uma cidade lendaria conhecida por sua simplicidade e eficiencia.', 'eridanus')
c.alimentar('O NPC ferreiro forja espadas na bigorna. Ele vende picaretas e armaduras.', 'npc_ferreiro')

print('Topicos:', len(c.topicos))
for nome, d in c.topicos.items():
    print(f'  {nome}: {d["bytes"]} bytes, {len(d["conteudo"])} palavras')

print()
print('Conectando spa + eridanus...')
cx = c.conectar('spa', 'eridanus')
if cx: print(c.debug(cx))
else: print('Sem conexao')

print()
print('Conectando npc_ferreiro + eridanus...')
cx2 = c.conectar('npc_ferreiro', 'eridanus')
if cx2: print(c.debug(cx2))
else: print('Sem conexao')

print()
print('Explorando todas...')
todas = c.explorar_todos()
print(f'{len(todas)} conexoes')
for cx in todas:
    print(f'  {cx["topico_a"]} <-> {cx["topico_b"]}: nota {cx["nota"]}/10')
