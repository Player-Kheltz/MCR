"""Fix ALL except indent issues in kernel.py."""
import sys
path = r'E:\Projeto MCR\scripts\mcr_devia\kernel.py'
with open(path, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

mudancas = 0
for i in range(len(linhas)):
    linha = linhas[i]
    stripped = linha.strip()
    if not stripped.startswith('except '):
        continue
    
    indent_atual = len(linha) - len(linha.lstrip())
    if indent_atual != 0:
        continue  # ja tem indent valida
    
    # Procura try: correspondente para tras
    for j in range(i - 1, -1, -1):
        if linhas[j].strip() == 'try:':
            indent_try = len(linhas[j]) - len(linhas[j].lstrip())
            linhas[i] = ' ' * indent_try + linha.lstrip()
            mudancas += 1
            break
        if linhas[j].strip().startswith(('def ', 'class ')):
            break  # mudou de escopo

# Remove except duplicados e adiciona pass onde necessario
new_lines = []
for i, linha in enumerate(linhas):
    new_lines.append(linha)
    stripped = linha.strip()
    if stripped.startswith('except') and stripped.endswith(':'):
        # Se proxima linha nao tem codigo valido, adiciona pass
        if i + 1 < len(linhas):
            prox = linhas[i + 1].strip()
            if not prox or prox.startswith(('except', 'def ', 'class ', '#', '"""')):
                indent = len(linha) - len(linha.lstrip())
                new_lines.append(' ' * (indent + 4) + 'pass\n')

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f'Corrigido: {mudancas} excepts')
