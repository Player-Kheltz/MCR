"""Comando: read - Le arquivos com offset/limit."""
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def register():
    return {
        "name": "read",
        "desc": "Le arquivo. Uso: read <path> [--offset N] [--limit N]",
        "handler": execute,
        "args": [{"name": "path", "type": "str", "required": True}],
        "categoria": "busca",
    }

def execute(kg, ia, args, ctx_crew=None):
    if not args:
        print('[Read] Uso: read <path> [--offset N] [--limit N]')
        return True
    
    path = args[0]
    if not os.path.isabs(path):
        path = os.path.join(BASE, path)
    
    if not os.path.exists(path):
        print(f'[Read] Arquivo nao encontrado: {path}')
        return True
    
    offset = 1
    limit = 2000
    for i, a in enumerate(args):
        if a == '--offset' and i+1 < len(args): offset = int(args[i+1])
        if a == '--limit' and i+1 < len(args): limit = int(args[i+1])
    
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        print(f'[Read] Erro: {e}')
        return True
    
    total = len(lines)
    start = max(0, offset - 1)
    end = min(total, start + limit)
    
    print(f'[Read] {os.path.basename(path)} ({total} linhas, L{offset}-L{end})')
    for i in range(start, end):
        txt = lines[i].rstrip().encode('ascii', errors='replace').decode('ascii')
        print(f'  L{i+1}: {txt}')
    if end < total:
        print(f'  ... mais {total - end} linhas (use --offset {end+1} para continuar)')
    
    return True
