#!/usr/bin/env python
"""Remove garbage line and fix orphaned print/return."""
import sys

path = r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove lines 973-977 (0-indexed: 972-976) - garbage + orphaned print/return
# These were left over from the failed edit
del lines[972:977]  # removes L973-L977

# Insert the correct if len(sys.argv) < 2: block at this position
# The block that was deleted was:
#     if len(sys.argv) < 2:
#         print(__doc__)
#         print(metrics...)
#         return
# But the print at 975 also had a continuation line, let me add it back

insert_block = [
    '    if len(sys.argv) < 2:\n',
    '        print(__doc__)\n',
    '        print(f\'Licoes: {kg.data["metricas"]["licoes"]} | Geracao: {kg.data["metricas"]["geracoes"]}\'\n',
    '              f\' | Compilacao: {kg.data["metricas"]["compilacoes"]}\')\n',
    '        return\n',
    '\n',
]

for idx, line in enumerate(insert_block):
    lines.insert(972 + idx, line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

# Verify syntax
try:
    compile(''.join(lines), path, 'exec')
    print(f'OK - linhas 973-977 removidas e reinseridas corretamente')
except SyntaxError as e:
    print(f'ERRO de sintaxe: {e}')
    # Show context around error
    import traceback
    traceback.print_exc()
    sys.exit(1)
