"""Teste isolado do Enricher para .lua."""
import sys
sys.path.insert(0, 'E:/Projeto MCR/scripts/mcr_devia')
from modulos.context_enricher import ContextEnricher
enricher = ContextEnricher()

# Teste com termos explicitos (simula o que o CR passaria)
r = enricher.enriquecer('O que e .lua no projeto MCR?', termos=['.lua', 'lua'])
print('Tipo:', r['tipo'])
print('Valido:', r['valido'])
print('Tamanho:', len(r['conteudo']), 'chars')
if r['conteudo']:
    print(r['conteudo'][:800])
else:
    print('(vazio)')

# Teste tambem o _gerar_tecnico direto
print('\n--- Teste direto _gerar_tecnico ---')
from modulos.context_enricher import ContextEnricher as CE
conteudo = enricher._gerar_tecnico(['.lua', 'lua'])
print('Tamanho:', len(conteudo), 'chars')
if conteudo:
    print(conteudo[:800])
else:
    print('(vazio - grep pode nao ter encontrado .lua)')
