#!/usr/bin/env python3
"""Fase 0 — Teste de registro e execucao basica do PipelineUniversal."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcr.pipeline_universal import PipelineUniversal

pipe = PipelineUniversal()

# Registrar dominios
from mcr.dominios.texto import DOMINIO as dom_texto
from mcr.dominios.codigo import DOMINIO as dom_codigo
from mcr.dominios.sprite import DOMINIO as dom_sprite
from mcr.dominios.api import DOMINIO as dom_api

pipe.registrar('texto', dom_texto)
pipe.registrar('codigo', dom_codigo)
pipe.registrar('sprite', dom_sprite)
pipe.registrar('api', dom_api)

print('=' * 60)
print('FASE 0 - Teste de registro de dominios')
print('=' * 60)
print('Dominios registrados: ' + str(list(pipe.dominios.keys())))
print('Stats: ' + str(pipe.stats()))
print()

# Teste 1: Texto
print('--- Teste TEXTO ---')
r = pipe.executar('o rato roeu a roupa do rei de roma', 'texto', n_gerar=3)
print('  Score: %.3f, Nota: %.3f, Status: %s' % (r['score'], r['nota'], r['status']))
print('  Arquivos: ' + str(r.get('arquivos', [])))
print()

# Teste 2: Codigo
print('--- Teste CODIGO ---')
code = 'function hello() return "world" end'
r2 = pipe.executar(code, 'codigo', n_gerar=3)
print('  Score: %.3f, Nota: %.3f, Status: %s' % (r2['score'], r2['nota'], r2['status']))
print()

# Teste 3: API
print('--- Teste API ---')
api = 'Game.createNpcType("Golem") KeywordHandler("hi")'
r3 = pipe.executar(api, 'api', n_gerar=3)
print('  Score: %.3f, Nota: %.3f, Status: %s' % (r3['score'], r3['nota'], r3['status']))
print()

# Teste 4: Sprite
print('--- Teste SPRITE ---')
from mcr.sprite_corpus import carregar_categoria
sprites = carregar_categoria('armors', max_sprites=5)
if sprites:
    r4 = pipe.executar(sprites, 'sprite', n_gerar=3, salvar=True)
    print('  Score: %.3f, Nota: %.3f, Status: %s' % (r4['score'], r4['nota'], r4['status']))
    print('  Arquivos: ' + str(r4.get('arquivos', [])))

print()
print('=' * 60)
print('FASE 0 - Concluida')
print('=' * 60)
