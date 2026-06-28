#!/usr/bin/env python3
"""Atualiza pipeline.py com prompts mais rigorosos para qualidade."""
path = r'E:\Projeto MCR\scripts\mcr_devia\modulos\pipeline.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Substitui o pipeline criativo com versao mais rigorosa
old_criativo = """            'criativo': {
                'etapas': [
                    {'nome': 'contexto', 'ferramenta': 'contexto', 'fonte': pergunta},
                    {'nome': 'personagens', 'ferramenta': 'fast', 'fonte': pergunta,
                     'prompt': 'Crie 3 nomes proprios de personagens para uma historia. So os nomes:', 'temp': 0.3},
                    {'nome': 'locais', 'ferramenta': 'fast', 'fonte': pergunta,
                     'prompt': 'Crie 2 nomes de locais fantasticos. So os nomes:', 'temp': 0.3},
                    {'nome': 'final', 'ferramenta': 'gerar', 'fonte': '$contexto',
                     'prompt': f'Com base no contexto abaixo, crie uma historia rica e detalhada. Use nomes proprios:\\n', 'temp': 0.5},
                ]
            },"""

new_criativo = """            'criativo': {
                'etapas': [
                    {'nome': 'contexto', 'ferramenta': 'contexto', 'fonte': pergunta},
                    {'nome': 'personagens', 'ferramenta': 'fast', 'fonte': pergunta,
                     'prompt': 'Crie 3 nomes proprios de personagens para Tibia (medieval fantasia). So os nomes:', 'temp': 0.3},
                    {'nome': 'locais', 'ferramenta': 'fast', 'fonte': pergunta,
                     'prompt': 'Crie 2 nomes de locais em Tibia (cidades, florestas, masmorras). So os nomes:', 'temp': 0.3},
                    {'nome': 'final', 'ferramenta': 'gerar', 'fonte': '$contexto',
                     'prompt': 'ATENCAO: Use SOMENTE o contexto abaixo. Nao invente nada fora dele. '
                               'Ambientacao: Tibia (mundo medieval fantasia, sem tecnologia moderna, sem naves, sem espaco). '
                               'Contexto OBRIGATORIO (use como REGRA, nao sugestao):\\n', 'temp': 0.5},
                    {'nome': 'validar', 'ferramenta': 'revisor', 'fonte': '$final'},
                ]
            },"""

if old_criativo in content:
    content = content.replace(old_criativo, new_criativo)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    try:
        compile(content, path, 'exec')
        print('OK - pipeline criativo atualizado com validacao')
    except SyntaxError as e:
        print('ERRO:', e)
else:
    print('old_criativo nao encontrado')
