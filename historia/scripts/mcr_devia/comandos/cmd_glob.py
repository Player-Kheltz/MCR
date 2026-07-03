"""Comando: glob - Busca arquivos por nome (auto-adiciona *)."""
import os, fnmatch

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def register():
    return {
        "name": "glob",
        "desc": "Busca arquivos por nome. Auto-adiciona * se padrao sem wildcard. Uso: glob <padrao> [--max N] [--type EXT]",
        "handler": execute,
        "args": [{"name": "padrao", "type": "str", "required": True}],
        "categoria": "busca",
    }

def execute(kg, ia, args, ctx_crew=None):
    if not args:
        print('[Glob] Uso: glob <padrao> [--max N] [--type EXT]')
        return True
    
    padrao = args[0]
    diretorio = BASE
    max_r = 20
    tipo = None
    
    for i, a in enumerate(args):
        if a == '--max' and i+1 < len(args): max_r = int(args[i+1])
        if a == '--type' and i+1 < len(args): tipo = args[i+1]
        if a == '--path' and i+1 < len(args): diretorio = args[i+1]
    
    # Auto-adiciona * se padrao nao tem wildcard
    if '*' not in padrao and '?' not in padrao:
        padrao_glob = f'*{padrao}*'
    else:
        padrao_glob = padrao
    
    resultados = []
    for root, dirs, files in os.walk(diretorio):
        dirs[:] = [d for d in dirs if not d.startswith(('.', '__pycache__', 'node_modules', 'vcpkg', '.vcpkg'))]
        for f in files:
            if tipo and not f.endswith(f'.{tipo}'):
                continue
            if fnmatch.fnmatch(f, padrao_glob):
                rel = os.path.relpath(os.path.join(root, f), diretorio)
                resultados.append(rel)
                if len(resultados) >= max_r:
                    break
        if len(resultados) >= max_r:
            break
    
    print(f'[Glob] \"{padrao}\" em {diretorio}: {len(resultados)} arquivos')
    for r in resultados:
        print(f'  {r}')
    if len(resultados) > max_r:
        print(f'  ... mais {len(resultados) - max_r} (use --max N para ver mais)')
    
    return True
