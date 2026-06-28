#!/usr/bin/env python3
import sys; sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
from modulos.pipeline import Pipeline
p = Pipeline()
tipo, subtipo = p._classificar('Crie uma historia sobre Eridanus')
print(f'tipo={tipo} subtipo={subtipo}')
pipe = p._definir_pipeline(tipo, subtipo)
print(f'pipe type={type(pipe)}')
etapas = pipe.get('etapas', [])
print(f'etapas type={type(etapas)} len={len(etapas)}')
if etapas:
    print(f'primeira etapa type={type(etapas[0])} value={etapas[0]}')
