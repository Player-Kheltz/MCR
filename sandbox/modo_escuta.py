"""Ativar modo escuta no resolver_ultra.py - detecta mas nao corrige"""
import re

path = r'E:\Projeto MCR\sandbox\resolver_ultra.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Encontra e remove o bloco de correcao com IA
start = c.find('TENTANDO CORRIGIR COM IA')
if start > 0:
    # Vai ate o final do arquivo
    end = c.find("def ia", start)
    if end < 0:
        end = len(c)
    
    # Substitui por modo escuta
    replacement = """print(f'\\n{"="*60}')
print(f'  MODO ESCUTA: detectando sem corrigir (projeto real)')
print(f'{'='*60}')
"""
    c = c[:start-15] + replacement + c[end:]
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('Modo escuta ATIVADO. Scanner reporta sem corrigir.')
else:
    print('Secao de correcao nao encontrada.')
