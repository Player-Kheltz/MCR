#!/usr/bin/env python
"""Adiciona modo --json ao MCR-DevIA para IPC sem shell."""
import sys

path = r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Insert --json handler after line 954 (kg.purgar()) and before line 955 (if len(sys.argv))
# Find line "    if len(sys.argv) < 2:"
insert_before = None
for i, line in enumerate(lines):
    if 'if len(sys.argv) < 2:' in line:
        insert_before = i
        break

if insert_before is None:
    print('ERRO: nao encontrou linha alvo')
    sys.exit(1)

json_block = [
    '    # Modo --json: comando via arquivo (sem shell, sem escaping)\n',
    "    if '--json' in sys.argv:\n",
    '        idx = sys.argv.index(\'--json\')\n',
    '        if idx + 1 < len(sys.argv):\n',
    '            json_path = sys.argv[idx + 1]\n',
    '            try:\n',
    "                with open(json_path, 'r', encoding='utf-8') as f:\n",
    '                    cmd_data = json.load(f)\n',
    "                cmd = cmd_data.get('cmd', '')\n",
    '                args = cmd_data.get(\'args\', [])\n',
    "                result_path = json_path.replace('_cmd', '_result')\n",
    '            except Exception as e:\n',
    "                print(f'[MCR-DevIA] Erro lendo {json_path}: {e}')\n",
    '                return\n',
    '        else:\n',
    "            print('[MCR-DevIA] Use: --json <arquivo_cmd>')\n",
    '            return\n',
    '\n',
]

# Insert the block before the target line
for idx, line in enumerate(json_block):
    lines.insert(insert_before + idx, line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

# Verify syntax
try:
    compile(''.join(lines), path, 'exec')
    print(f'OK - modo --json adicionado ({len(json_block)} linhas antes da L{insert_before+1})')
except SyntaxError as e:
    print(f'ERRO de sintaxe: {e}')
    sys.exit(1)
