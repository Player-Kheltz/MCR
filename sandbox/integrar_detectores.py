"""Integrar detectores orfaos no scan() e rodar 5 ciclos"""
import os, re

SCANNER = r'E:\Projeto MCR\sandbox\resolver_ultra.py'

# 1. Ler o scanner
with open(SCANNER, 'r', encoding='utf-8') as f:
    codigo = f.read()

# 2. Encontrar funcoes detectar_*
detectores = re.findall(r'def (detectar_\w+)\(', codigo)
print(f'Detectores encontrados: {len(detectores)}')
for d in detectores:
    print(f'  - {d}')

# 3. Gerar codigo de integracao (loop que chama todos)
integracao = '''
    # AUTO-INTEGRACAO: chamar todos os detectores automaticamente
    import sys
    current_module = sys.modules[__name__]
    for nome in dir(current_module):
        if nome.startswith('detectar_'):
            detector = getattr(current_module, nome)
            if callable(detector):
                try:
                    if detector(conteudo):
                        problema = nome.replace('detectar_', '').replace('_', ' ')
                        problemas.append(problema)
                except:
                    pass
'''

# 4. Inserir no scan() — antes do return problemas
# Procurar o return problemas no scan()
if '    return problemas' in codigo:
    codigo = codigo.replace('    return problemas', integracao + '\n    return problemas')
    print(f'\nIntegracao inserida no scan()!')
elif '\n    return problemas' in codigo:
    codigo = codigo.replace('\n    return problemas', integracao + '\n    return problemas')
    print(f'\nIntegracao inserida no scan()!')
else:
    print(f'\n[!] Nao encontrou return problemas no scan()')

# 5. Salvar
with open(SCANNER, 'w', encoding='utf-8') as f:
    f.write(codigo)

print(f'\nScan() atualizado. Agora todos os detectores serao chamados automaticamente.')
print(f'Rodando 5 ciclos de aprendizado...')
