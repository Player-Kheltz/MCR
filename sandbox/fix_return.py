"""Restaurar return e integracao no resolver_ultra.py"""
with open(r'E:\Projeto MCR\sandbox\resolver_ultra.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Procura onde inserir
marker = "problemas.append(f'chave string vs numero (possivel confusao)')"
insert_code = """

    # AUTO-INTEGRACAO: chamar detectores
    for nome, fn in list(globals().items()):
        if nome.startswith('detectar_') and callable(fn):
            try:
                if fn(texto):
                    problemas.append(nome.replace('detectar_', '').replace('_', ' '))
            except:
                pass

    return problemas
"""

idx = c.find(marker)
if idx > 0:
    # Encontra o final da linha
    end_of_line = c.find('\n', idx)
    # Encontra o proximo print depois
    next_print = c.find("\nprint('=", end_of_line)
    if next_print > 0:
        # Insere o codigo antes do print
        c = c[:next_print] + insert_code + c[next_print:]
        with open(r'E:\Projeto MCR\sandbox\resolver_ultra.py', 'w', encoding='utf-8') as f:
            f.write(c)
        print('OK! Return e integracao restaurados.')
    else:
        print('Nao encontrou print depois')
else:
    print('Nao encontrou marker')
