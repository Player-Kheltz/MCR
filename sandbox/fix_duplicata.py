"""Remove duplicata de auto-integracao no resolver_ultra.py"""
import re

path = r'E:\Projeto MCR\sandbox\resolver_ultra.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Encontra a primeira secao de auto-integracao (sys.modules)
start = c.find('# AUTO-INTEGRACAO: chamar todos os detectores')
if start > 0:
    # Encontra o proximo '# 2.' depois
    next_section = c.find('\n    # 2.', start)
    if next_sector > 0:
        old_text = c[start:next_section]
        c = c.replace(old_text, '', 1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(c)
        print('Secao sys.modules removida. Sobrou so a globals().')
    else:
        print('Nao encontrou secao 2.')
else:
    print('Nao encontrou secao de auto-integracao')
