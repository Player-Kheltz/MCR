#!/usr/bin/env python
"""Simplify --json handler: replace sys.argv so normal parsing works."""
import sys

path = r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Old --json block
old_block = """    # Modo --json: comando via arquivo (sem shell, sem escaping)
    _from_json = False
    if '--json' in sys.argv:
        idx = sys.argv.index('--json')
        if idx + 1 < len(sys.argv):
            json_path = sys.argv[idx + 1]
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    import json as _json; cmd_data = _json.load(f)
                cmd = cmd_data.get('cmd', '')
                args = cmd_data.get('args', [])
                result_path = json_path.replace('_cmd', '_result')
            except Exception as e:
                print(f'[MCR-DevIA] Erro lendo {json_path}: {e}')
                return
        else:
            print('[MCR-DevIA] Use: --json <arquivo_cmd>')
            return

    if not _from_json:
        if len(sys.argv) < 2:
            print(__doc__)"""

# Check if old block exists
if old_block in content:
    # Replace with new simplified version
    new_block = """    # Modo --json: substitui sys.argv para evitar shell escaping
    if '--json' in sys.argv:
        idx = sys.argv.index('--json')
        if idx + 1 < len(sys.argv):
            json_path = sys.argv[idx + 1]
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    import json as _json
                    cmd_data = _json.load(f)
                sys.argv = [sys.argv[0], cmd_data.get('cmd', '')] + cmd_data.get('args', [])
            except Exception as e:
                print(f'[MCR-DevIA] Erro lendo {json_path}: {e}')
                return
        else:
            print('[MCR-DevIA] Use: --json <arquivo_cmd>')
            return

    if len(sys.argv) < 2:"""
    
    content = content.replace(old_block, new_block)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Verify syntax
    try:
        compile(content, path, 'exec')
        print('OK - modo --json simplificado')
    except SyntaxError as e:
        print(f'ERRO: {e}')
else:
    print('Bloco antigo nao encontrado, buscando alternativas...')
    # Search for the actual content
    for i, line in enumerate(open(path, encoding='utf-8')):
        if 'Modo --json' in line:
            print(f'L{i+1}: {line.rstrip()[:100]}')
