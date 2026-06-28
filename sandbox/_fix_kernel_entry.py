#!/usr/bin/env python3
"""Extrai main_kernel() de kernel.py e atualiza MCR_DevIA-Kernel.py."""
import sys

# 1. Kernel.py: extrair main_kernel() do if __name__
kpath = r'E:\Projeto MCR\scripts\mcr_devia\kernel.py'
with open(kpath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontra o bloco if __name__
start = None
end = None
for i, line in enumerate(lines):
    if "if __name__ == '__main__':" in line:
        start = i
    elif start is not None and i > start:
        if i == len(lines) - 1 or (i > start + 2 and line.strip() == '' and lines[i+1].strip() != ''):
            end = i + 1 if i + 1 < len(lines) else len(lines)
            break

if start is None:
    print('ERRO: if __name__ nao encontrado')
    sys.exit(1)

if end is None:
    end = len(lines)

# Cria funcao main_kernel + if __name__
func_lines = ['def main_kernel():\n']
for i in range(start + 1, end):
    line = lines[i]
    func_lines.append(line)  # Mantem indentacao original

func_lines.append('\n')
func_lines.append("if __name__ == '__main__':\n")
func_lines.append('    main_kernel()\n')

# Substitui no arquivo
lines[start:end] = func_lines

with open(kpath, 'w', encoding='utf-8') as f:
    f.writelines(lines)

try:
    compile(''.join(lines), kpath, 'exec')
    print('OK - kernel.py com main_kernel()')
except SyntaxError as e:
    print(f'ERRO kernel.py: {e}')
    sys.exit(1)

# 2. MCR_DevIA-Kernel.py: usar import em vez de exec()
mpath = r'E:\Projeto MCR\scripts\mcr_devia\MCR_DevIA-Kernel.py'
with open(mpath, 'r', encoding='utf-8') as f:
    content = f.read()

new_content = '''#!/usr/bin/env python
"""MCR-DevIA Kernel - Entry point CLI.
Uso: python MCR_DevIA-Kernel.py <comando> [args...]
     python MCR_DevIA-Kernel.py --json <arquivo.json>

Importa kernel.py e delega para main_kernel().
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == '__main__':
    from kernel import main_kernel
    main_kernel()
'''

with open(mpath, 'w', encoding='utf-8') as f:
    f.write(new_content)

try:
    compile(new_content, mpath, 'exec')
    print('OK - MCR_DevIA-Kernel.py usa import')
except SyntaxError as e:
    print(f'ERRO MCR_DevIA-Kernel.py: {e}')
    sys.exit(1)

print('Ambos arquivos atualizados com sucesso!')
