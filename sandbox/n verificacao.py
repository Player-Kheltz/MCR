"""Ensinar MCR-DevIA a verificar antes de editar"""
import os, re

ULTIMATE_PATH = r'E:\Projeto MCR\sandbox\mcr_ultimate.py'

print('--- MCR-DevIA aprendendo a VERIFICAR antes de EDITAR ---\n')

# Le o arquivo
with open(ULTIMATE_PATH, 'r', encoding='utf-8', errors='replace') as f:
    conteudo = f.read()

# Verifica cada template
for tipo in ['npc', 'monster', 'item', 'quest', 'spell']:
    marker = f"'{tipo}':"
    if marker in conteudo:
        idx = conteudo.find(marker)
        snippet = conteudo[idx:idx+300]
        
        # Verifica se o formato é o esperado (template em string simples)
        if f"'template': '" in snippet:
            print(f'[OK] {tipo}: formato compativel com o reparo')
        else:
            print(f'[FORMATO DIFERENTE] {tipo}: template existe mas em formato diferente do esperado')
            print(f'  Trecho: {snippet[:150]}...\n')
            print(f'  ACAO: Em vez de tentar editar, registrar aprendizado:')
            print(f'  "O template de {tipo} esta em formato diferente. Nao vou editar ate entender o novo formato."')
    else:
        print(f'[AUSENTE] {tipo}: nao encontrado no arquivo')
        print(f'  ACAO: Template pode ter sido perdido na reescrita do arquivo.')

print('\n--- LICAO APRENDIDA ---')
print('Sempre verificar o formato antes de editar.')
print('Se o formato mudou, registrar e aprender, nao tentar editar no escuro.')
