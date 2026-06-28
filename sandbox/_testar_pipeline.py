#!/usr/bin/env python3
import sys; sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from kernel import MCRKernel
from modulos.pipeline import Pipeline
k = MCRKernel(); k.inicializar()
p = Pipeline(kg=k.contexto.get('kg'), ia=k.contexto.get('ia'))
r = p.executar('Crie uma historia sobre a cidade de Eridanus em Tibia')
print(r[:600])
