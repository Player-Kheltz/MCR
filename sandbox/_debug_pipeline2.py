#!/usr/bin/env python3
import sys; sys.path.insert(0, r'E:\Projeto MCR\scripts\mcr_devia')
import modulos.pipeline
import json

# Monkey-patch to debug
original = modulos.pipeline.Pipeline._definir_pipeline
def debug_definir(self, tipo, subtipo):
    result = original(self, tipo, subtipo)
    etapas = result.get('etapas', [])
    print(f'DEBUG tipo={tipo} subtipo={subtipo} len_etapas={len(etapas)}')
    if etapas:
        print(f'DEBUG primeira etapa type={type(etapas[0])}')
    return result
modulos.pipeline.Pipeline._definir_pipeline = debug_definir

p = modulos.pipeline.Pipeline()
p.executar('Crie uma historia sobre Eridanus')
