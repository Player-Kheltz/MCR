"""Valida e corrige syntaxe de todos os modulos afetados pelo auto-repair."""
import os, re, sys

ARQUIVOS = [
    r'E:\Projeto MCR\scripts\mcr_devia\context_crew.py',
    r'E:\Projeto MCR\scripts\mcr_devia\context_infinity.py',
    r'E:\Projeto MCR\scripts\mcr_devia\kernel.py',
]

for caminho in ARQUIVOS:
    if not os.path.exists(caminho):
        continue
    
    print(f'Validando {os.path.basename(caminho)}...')
    
    for tentativa in range(10):  # max 10 iteracoes
        try:
            compile(open(caminho, 'r', encoding='utf-8').read(), caminho, 'exec')
            print(f'  OK!')
            break
        except SyntaxError as e:
            print(f'  Erro L{e.lineno}: {e.msg}')
            
            with open(caminho, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
            
            linha = e.lineno - 1  # 0-based
            if linha < 0 or linha >= len(linhas):
                print(f'  Linha invalida: {e.lineno}')
                break
            
            # Mostra a linha problematica
            texto_linha = linhas[linha].rstrip()
            print(f'    L{e.lineno}: {texto_linha}')
            
            if 'expected an indented block after' in e.msg and 'except' in e.msg:
                # Adiciona pass apos except sem corpo
                indent = len(linhas[linha]) - len(linhas[linha].lstrip())
                linhas.insert(linha + 1, ' ' * (indent + 4) + 'pass\n')
                print(f'    -> Adicionado pass apos except')
            
            elif 'unexpected indent' in e.msg or 'unindent does not match' in e.msg:
                # Tenta corrigir indentacao baseado no try anterior
                pass  # Mais complexo - precisamos analisar cada caso
                # Por enquanto, remove espacos extras
                linha_atual = linhas[linha]
                espacos_atuais = len(linha_atual) - len(linha_atual.lstrip())
                # Tenta indentacao de 4 em 4
                indent_corrigida = (espacos_atuais // 4) * 4
                if indent_corrigida != espacos_atuais:
                    linhas[linha] = ' ' * indent_corrigida + linha_atual.lstrip()
                    print(f'    -> Indentacao corrigida: {espacos_atuais} -> {indent_corrigida}')
            
            elif 'expected' in e.msg and 'block' in e.msg:
                # try sem except ou except sem corpo
                # Verifica se ha um try na linha anterior
                for j in range(linha, max(0, linha - 5), -1):
                    if linhas[j].strip().startswith('try:'):
                        # Adiciona except Exception: pass
                        indent = len(linhas[j]) - len(linhas[j].lstrip())
                        linhas.insert(linha + 1, ' ' * indent + 'except Exception:\n')
                        linhas.insert(linha + 2, ' ' * (indent + 4) + 'pass\n')
                        print(f'    -> Adicionado except Exception para try em L{j+1}')
                        break
            
            # Salva e tenta de novo
            with open(caminho, 'w', encoding='utf-8') as f:
                f.writelines(linhas)
    
    else:
        print(f'  FALHOU apos {tentativa+1} tentativas')
