#!/usr/bin/env python
"""Renomeia kernel.py -> MCR_DevIA-Kernel.py e cria alias legado."""
import os, shutil

DEVIA = r'E:\Projeto MCR\scripts\mcr_devia'
SRC = os.path.join(DEVIA, 'kernel.py')
DST = os.path.join(DEVIA, 'MCR_DevIA-Kernel.py')

# 1. Copia kernel.py para MCR_DevIA-Kernel.py
shutil.copy2(SRC, DST)
print(f'Copiado: kernel.py -> MCR_DevIA-Kernel.py')

# 2. Atualiza auto-referencias no novo arquivo
with open(DST, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('from kernel import MCRKernel', 'from MCR_DevIA-Kernel import MCRKernel')
content = content.replace('python kernel.py', 'python MCR_DevIA-Kernel.py')
with open(DST, 'w', encoding='utf-8') as f:
    f.write(content)
print('Auto-referencias atualizadas em MCR_DevIA-Kernel.py')

# 3. Atualiza referencias no kernel.py original tambem
with open(SRC, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('from kernel import MCRKernel', 'from MCR_DevIA-Kernel import MCRKernel')
with open(SRC, 'w', encoding='utf-8') as f:
    f.write(content)
print('kernel.py original atualizado')

# 4. Cria alias legado
LEGADO = os.path.join(DEVIA, 'MCR_DevIA-Legado.py')
with open(LEGADO, 'w', encoding='utf-8') as f:
    f.write('#!/usr/bin/env python\n')
    f.write('"""Alias para mcr_devia.py (legado) - mantido para compatibilidade."""\n')
    f.write('import sys, os\n')
    f.write('sys.path.insert(0, os.path.dirname(__file__))\n')
    f.write('from mcr_devia import main\n')
    f.write("if __name__ == '__main__':\n")
    f.write('    main()\n')
print(f'Alias criado: MCR_DevIA-Legado.py')

# 5. Verifica sintaxe
for fpath in [DST, LEGADO]:
    try:
        compile(open(fpath, encoding='utf-8').read(), fpath, 'exec')
        print(f'OK: {os.path.basename(fpath)}')
    except SyntaxError as e:
        print(f'ERRO em {fpath}: {e}')

print('\nFeito!')
