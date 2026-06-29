"""Corrige indentacao de todos os except quebrados em kernel.py."""
import sys
caminho = r'E:\Projeto MCR\scripts\mcr_devia\kernel.py'
with open(caminho, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

def indent_linha(idx):
    return len(linhas[idx]) - len(linhas[idx].lstrip())

mudancas = 0
for i in range(len(linhas)):
    linha = linhas[i]
    stripped = linha.strip()
    if not stripped.startswith('except ') and not stripped.startswith('except:'):
        continue
    
    indent_atual = indent_linha(i)
    if indent_atual == 0:
        # Procura o try: correspondente
        for j in range(i - 1, max(-1, i - 30), -1):
            if j < 0: break
            if linhas[j].strip() == 'try:':
                indent_try = indent_linha(j)
                if indent_try > 0:
                    linhas[i] = ' ' * indent_try + linha.lstrip()
                    mudancas += 1
                    break
            if linhas[j].strip().startswith('class ') or linhas[j].strip().startswith('def '):
                break  # saiu do escopo — nao achou try

if mudancas:
    with open(caminho, 'w', encoding='utf-8') as f:
        f.writelines(linhas)
    
print(f'{mudancas} excepts corrigidos em kernel.py')
