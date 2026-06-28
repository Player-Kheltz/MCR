"""Teste isolado do Context Enricher."""
import sys
sys.path.insert(0, 'E:/Projeto MCR/scripts/mcr_devia')
from modulos.context_enricher import ContextEnricher
import json

enricher = ContextEnricher()

for pergunta in [
    'Crie uma lore para a cidade inicial Eridanus do projeto MCR',
    'O que e .lua no projeto MCR?',
    'Explique a diferenca entre SPA e SHC',
]:
    print(f'\n{"="*50}')
    print(f'PERGUNTA: {pergunta}')
    print(f'{"="*50}')
    resultado = enricher.enriquecer(pergunta)
    print(f'Tipo: {resultado["tipo"]}')
    print(f'Valido: {resultado["valido"]}')
    print(f'Tempo: {resultado["tempo"]}s')
    print(f'Tamanho: {len(resultado["conteudo"])} chars')
    if resultado['conteudo']:
        print(f'Conteudo:')
        print(resultado['conteudo'][:800])
    else:
        print('  (vazio)')
