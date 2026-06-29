"""Fixa todos os except sem corpo nos arquivos corrompidos pelo auto-repair."""
import os, re

ARQUIVOS = [
    r'E:\Projeto MCR\scripts\mcr_devia\context_crew.py',
    r'E:\Projeto MCR\scripts\mcr_devia\context_infinity.py',
    r'E:\Projeto MCR\scripts\mcr_devia\kernel.py',
]

for caminho in ARQUIVOS:
    if not os.path.exists(caminho):
        continue
    with open(caminho, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Remove backups antigos
    bak_path = caminho + '.bak'
    if os.path.exists(bak_path):
        os.remove(bak_path)
    
    # Procura except: linha seguida de linha em branco + definicao de classe/funcao
    # Padrao: "except ...:\n\n    def " ou "except ...:\n\nclass "
    original = conteudo
    
    # Substitui except sem corpo seguido de funcao/classe por except com pass
    # Ex: "except ImportError:\n\nclass ContextCrew:" -> "except ImportError:\n        pass\n\nclass ContextCrew:"
    conteudo = re.sub(
        r'(^\s*except\s+[^:]+:)\s*\n\s*\n(\s*(?:class|def)\s)',
        lambda m: m.group(1) + '\n        pass\n\n' + m.group(2),
        conteudo,
        flags=re.MULTILINE
    )
    
    # Substitui except: sem corpo seguido de outra linha nao indentada
    # Ex: "except KeyError:\n\n    def _salvar_cache" -> "except KeyError:\n        pass\n\n    def _salvar_cache"
    conteudo = re.sub(
        r'(^\s*except\s+[^:]+:)\s*\n\s*\n(\s{4}(?:class|def)\s)',
        lambda m: m.group(1) + '\n        pass\n\n' + m.group(2),
        conteudo,
        flags=re.MULTILINE
    )
    
    if conteudo != original:
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f'  {os.path.basename(caminho)}: corrigido')
    else:
        print(f'  {os.path.basename(caminho)}: sem alteracoes')

print('Feito.')
