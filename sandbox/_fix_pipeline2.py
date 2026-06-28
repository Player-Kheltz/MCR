#!/usr/bin/env python3
"""Ajusta prompt do pipeline para equilibrio entre usar contexto e criar."""
path = r'E:\Projeto MCR\scripts\mcr_devia\modulos\pipeline.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_prompt = "'prompt': 'ATENCAO: Use SOMENTE o contexto abaixo. Nao invente nada fora dele. '\n                               'Ambientacao: Tibia (mundo medieval fantasia, sem tecnologia moderna, sem naves, sem espaco). '\n                               'Contexto OBRIGATORIO (use como REGRA, nao sugestao):\\\\n'"
new_prompt = "'prompt': 'Contexto de referencia (use como base, mas crie livremente dentro de Tibia):\\\\n'"

if old_prompt in content:
    content = content.replace(old_prompt, new_prompt)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    try:
        compile(content, path, 'exec')
        print('OK')
    except SyntaxError as e:
        print('ERRO:', e)
else:
    print('old_prompt nao encontrado')
    # Debug: show first 2000 chars
    print(content[:2000])
