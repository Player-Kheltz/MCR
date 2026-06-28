#!/usr/bin/env python
"""Add --stdin mode to MCR-DevIA - read JSON commands from stdin."""
import sys

path = r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add --stdin before --json handler
old = "    elif '--json' in sys.argv:"
new = """    elif '--stdin' in sys.argv:
        import json as _json_stdin
        cmd_data = _json_stdin.loads(sys.stdin.read())
        sys.argv = [sys.argv[0], cmd_data.get('cmd', ''), *cmd_data.get('args', [])]
    elif '--json' in sys.argv:"""

if old in content:
    content = content.replace(old, new)
    try:
        compile(content, path, 'exec')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('OK - modo --stdin adicionado')
    except SyntaxError as e:
        print(f'ERRO sintaxe: {e}')
else:
    print('Bloco nao encontrado')
