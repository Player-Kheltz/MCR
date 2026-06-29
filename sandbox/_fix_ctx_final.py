"""Fix ALL remaining syntax errors in context_crew.py by adding 'pass' after empty excepts."""
import re

path = r'E:\Projeto MCR\scripts\mcr_devia\context_crew.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add pass after except: lines that are followed by lower indent or blank+lower
linhas = content.split('\n')
new_linhas = []
for i, linha in enumerate(linhas):
    new_linhas.append(linha)
    stripped = linha.strip()
    if stripped.startswith('except') and stripped.endswith(':'):
        # Check if next non-blank line is at lower/equal indent
        prox = None
        for j in range(i+1, min(i+5, len(linhas))):
            if linhas[j].strip():
                prox = j
                break
        if prox is not None:
            indent_atual = len(linha) - len(linha.lstrip())
            indent_prox = len(linhas[prox]) - len(linhas[prox].lstrip())
            if indent_prox <= indent_atual:
                # Has no body - add pass
                new_linhas.append(' ' * (indent_atual + 4) + 'pass')

content = '\n'.join(new_linhas)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed context_crew.py')
