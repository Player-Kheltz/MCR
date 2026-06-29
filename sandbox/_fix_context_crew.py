"""Corrige TODOS os except com indent 0 em context_crew.py."""
path = r'E:\Projeto MCR\scripts\mcr_devia\context_crew.py'
with open(path, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

mudancas = 0
for i in range(len(linhas)):
    linha = linhas[i]
    stripped = linha.strip()
    if not (stripped.startswith('except ') or stripped.startswith('except:')):
        continue
    
    indent_atual = len(linha) - len(linha.lstrip())
    if indent_atual > 0:
        continue  # ja tem indent
    
    # Procura o try: mais proximo ANTES, no mesmo nivel de bloco
    for j in range(i - 1, -1, -1):
        lj = linhas[j]
        if lj.strip() == 'try:':
            indent_try = len(lj) - len(lj.lstrip())
            if indent_try > 0:
                linhas[i] = ' ' * indent_try + linha.lstrip()
                mudancas += 1
                break
        # Se encontrar def/class, para (mudou de escopo)
        if lj.strip().startswith(('def ', 'class ')):
            # Usa indentacao da definicao + 4
            indent_def = len(lj) - len(lj.lstrip())
            linhas[i] = ' ' * (indent_def + 4) + linha.lstrip()
            mudancas += 1
            break

if mudancas:
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(linhas)
print(f'{mudancas} excepts corrigidos em context_crew.py')
