"""Corrige indentacao de TODOS os except em context_crew.py baseado nos try: correspondentes."""
path = r'E:\Projeto MCR\scripts\mcr_devia\context_crew.py'
with open(path, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

def encontrar_try_mais_proximo(pos_linha):
    """Procura o try: mais proximo antes da posicao, considerando block depth."""
    depth_atual = 0
    melhor_try = None
    melhor_dist = 999
    for j in range(pos_linha - 1, max(-1, pos_linha - 50), -1):
        if j < 0: break
        linha = linhas[j].strip()
        if linha.startswith('class ') or linha.startswith('def '):
            break  # saiu do escopo
        if linha == 'try:':
            # Verifica se esse try esta no mesmo nivel ou acima
            indent_try = len(linhas[j]) - len(linhas[j].lstrip())
            if indent_try <= depth_atual:
                dist = pos_linha - j
                if dist < melhor_dist:
                    melhor_dist = dist
                    melhor_try = j
                    break
    return melhor_try

mudancas = 0
for i, linha in enumerate(linhas):
    stripped = linha.strip()
    if not stripped.startswith('except'):
        continue
    if stripped.startswith('except:'):
        continue  # except: pass inline, ok
    
    indent_atual = len(linha) - len(linha.lstrip())
    
    # Procura o try: correspondente
    try_idx = encontrar_try_mais_proximo(i)
    if try_idx is not None:
        indent_try = len(linhas[try_idx]) - len(linhas[try_idx].lstrip())
        if indent_atual != indent_try:
            linhas[i] = ' ' * indent_try + linha.lstrip()
            mudancas += 1
            print(f'  L{i+1}: indent {indent_atual} -> {indent_try}')

if mudancas:
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(linhas)
    print(f'\nTotal: {mudancas} correcoes')
else:
    print('Nenhuma correcao necessaria')
