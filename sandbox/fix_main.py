"""Fechar if __name__ no resolver_ultra.py"""
with open(r'E:\Projeto MCR\sandbox\resolver_ultra.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontra o final do arquivo e ajusta a indentacao
for i in range(len(lines) - 1, -1, -1):
    if 'FINAL:' in lines[i] and 'problemas corrigidos' in lines[i]:
        lines[i] = '    ' + lines[i]
    elif 'print(f"{' in lines[i] and '=' in lines[i]:
        lines[i] = '    ' + lines[i]
        break

with open(r'E:\Projeto MCR\sandbox\resolver_ultra.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('OK! if __name__ ajustado.')
