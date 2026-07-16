#!/usr/bin/env python3
"""Teste completo do PipelineUniversal — todas as fases."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcr.pipeline_universal import PipelineUniversal

pipe = PipelineUniversal()

# Registrar todos os dominios
from mcr.dominios.texto import DOMINIO as dom_texto
from mcr.dominios.codigo import DOMINIO as dom_codigo
from mcr.dominios.sprite import DOMINIO as dom_sprite
from mcr.dominios.api import DOMINIO as dom_api

pipe.registrar('texto', dom_texto)
pipe.registrar('codigo', dom_codigo)
pipe.registrar('sprite', dom_sprite)
pipe.registrar('api', dom_api)

print('=' * 70)
print('TESTE FINAL — PipelineUniversal')
print('=' * 70)

# 1. TEXTO
print('\n[1/4] TEXTO')
r = pipe.executar('o rato roeu a roupa do rei de roma', 'texto', n_gerar=3, salvar=True)
print('  Score: %.3f | Nota: %.3f | Status: %s' % (r['score'], r['nota'], r['status']))
print('  Thresholds: ' + json.dumps(r.get('thresholds', {})))
arquivos = r.get('arquivos', [])
for a in arquivos:
    with open(a, 'r', encoding='utf-8') as f:
        c = f.read()
    print('  [%s] %s' % (a.split('_')[-1], c[:60]))

# 2. CODIGO
print('\n[2/4] CODIGO')
code = 'function hello(name) return "Hello " .. name end'
r = pipe.executar(code, 'codigo', n_gerar=3, salvar=True)
print('  Score: %.3f | Nota: %.3f | Status: %s' % (r['score'], r['nota'], r['status']))

# 3. API
print('\n[3/4] API')
api = 'Game.createNpcType("Golem") KeywordHandler("hi") npcHandler:addModule()'
r = pipe.executar(api, 'api', n_gerar=3, salvar=True)
print('  Score: %.3f | Nota: %.3f | Status: %s' % (r['score'], r['nota'], r['status']))
arquivos = r.get('arquivos', [])
for a in arquivos:
    with open(a, 'r', encoding='utf-8') as f:
        c = f.read()
    print('  [%s] %d tokens' % (a.split('_')[-1], len(c.split())))

# 4. SPRITE
print('\n[4/4] SPRITE')
from mcr.sprite_corpus import carregar_categoria
for cat in ['armors', 'shields', 'sword_weapons', 'boots']:
    sprites = carregar_categoria(cat, max_sprites=5)
    if sprites:
        r = pipe.executar(sprites, 'sprite', n_gerar=3, salvar=True)
        print('  %-15s Score: %.3f | Nota: %.3f | Status: %s | Arquivos: %s' % (
            cat, r['score'], r['nota'], r['status'], len(r.get('arquivos', []))))

# Resumo
print('\n' + '=' * 70)
print('RESUMO')
print('=' * 70)
print(json.dumps(pipe.stats(), indent=2))
print()
print('PipelineUniversal: 4 dominios, 6 estagios, zero hardcode.')
print('Proximo: Fase 2 (Audio), Fase 3 (Integracao), Fase 4 (Auto), Fase 5 (Emergencia)')
