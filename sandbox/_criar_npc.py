#!/usr/bin/env python3
"""MCR + Cloud criam NPC juntos."""
import sys, os, time
sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from kernel import MCRKernel
from modulos.conselho import Conselho

k = MCRKernel(); k.inicializar()
c = Conselho(kg=k.contexto.get('kg'), ia=k.contexto.get('ia'))

print('1. CRIANDO HISTORIA DO NPC (MCR)...')
t0 = time.time()
r = c.deliberar('Crie a historia completa do NPC Eldrin, Guardiao da Biblioteca Perdida de Eridanus. Inclua: origem, proposito, dialogo de encontro, e missao que ele da aos jogadores.')
historia = r.get('veredito', '')
t_mcr = time.time() - t0
print(f'   Concluido em {t_mcr:.0f}s')
print(historia[:400])
print('...')
