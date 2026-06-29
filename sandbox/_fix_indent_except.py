"""Corrige indentacao de excepts quebrados pelo auto-repair em todos os arquivos.
Procura por except que comecam na coluna 0 (sem indentacao) e ajusta."""
import os, re

ARQUIVOS = [
    r'E:\Projeto MCR\scripts\mcr_devia\context_crew.py',
    r'E:\Projeto MCR\scripts\mcr_devia\context_infinity.py',
    r'E:\Projeto MCR\scripts\mcr_devia\kernel.py',
]

total = 0
for caminho in ARQUIVOS:
    if not os.path.exists(caminho):
        continue
    with open(caminho, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    
    novas_linhas = []
    mudancas = 0
    for i, linha in enumerate(linhas):
        # Procura por except: na coluna 0
        if linha.startswith('except ') or linha.strip().startswith('except '):
            # Tenta achar o try: correspondente (para tras)
            try_indent = None
            for j in range(i - 1, max(0, i - 20), -1):
                if linhas[j].strip().startswith('try:'):
                    # Pega a indentacao do try
                    try_indent = len(linhas[j]) - len(linhas[j].lstrip())
                    break
            if try_indent is not None:
                espacos_atuais = len(linha) - len(linha.lstrip())
                if espacos_atuais != try_indent:
                    nova_linha = ' ' * try_indent + linha.lstrip()
                    novas_linhas.append(nova_linha)
                    mudancas += 1
                    continue
        
        novas_linhas.append(linha)
    
    if mudancas > 0:
        with open(caminho, 'w', encoding='utf-8') as f:
            f.writelines(novas_linhas)
        total += mudancas
        print(f'  {os.path.basename(caminho)}: {mudancas} corrigidos')

print(f'\nTotal: {total} excepts reindentados')
