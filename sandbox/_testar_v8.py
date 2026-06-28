#!/usr/bin/env python3
import sys; sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from kernel import MCRKernel
from modulos.conselho import Conselho
k = MCRKernel()
k.inicializar()
c = Conselho(kg=k.contexto.get('kg'), ia=k.contexto.get('ia'))
r = c.deliberar('Crie uma historia detalhada sobre a cidade de Eridanus')
v = str(r.get('veredito',''))
nomes = r.get('nomes_proprios', 0)
print(f'VEREDITO ({len(v)} chars, {nomes} nomes):')
print(v[:600])
