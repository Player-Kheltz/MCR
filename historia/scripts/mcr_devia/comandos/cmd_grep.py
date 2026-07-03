"""Comando: grep - Busca texto em arquivos."""
import os, re, fnmatch

def register():
    return {
        "name": "grep",
        "desc": "Busca texto em arquivos. Uso: grep <padrao> [caminho] [--literal] [--max N] [--ctx N] [--type EXT]",
        "handler": execute,
        "args": [
            {"name": "padrao", "type": "str", "required": True},
            {"name": "caminho", "type": "str", "required": False},
        ],
        "categoria": "busca",
    }

def execute(kg, ia, args, ctx_crew=None):
    if not args:
        print('[Grep] Uso: grep <padrao> [caminho]')
        return True
    
    padrao = args[0]
    # Default search dir
    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    SANDBOX = os.path.join(BASE, 'sandbox')
    
    diretorio = SANDBOX
    if len(args) > 1 and not args[1].startswith('--'):
        diretorio = args[1]
    
    # Parse flags
    flgs = {'--literal': False, '--max': 20, '--ctx': 0, '--type': None}
    for i, a in enumerate(args):
        if a == '--literal': flgs['--literal'] = True
        elif a == '--max' and i+1 < len(args): flgs['--max'] = int(args[i+1])
        elif a == '--ctx' and i+1 < len(args): flgs['--ctx'] = int(args[i+1])
    
    if flgs['--literal']:
        re_padrao = re.compile(re.escape(padrao))
    else:
        try: re_padrao = re.compile(padrao)
        except Exception as e:
            print(f"[Fix] ERRO: {e}")
    
    resultados = []
    if os.path.isfile(diretorio):
        caminhos = [(os.path.dirname(diretorio), os.path.basename(diretorio))]
    elif os.path.isdir(diretorio):
        caminhos = []
        for root, dirs, files in os.walk(diretorio):
            dirs[:] = [d for d in dirs if not d.startswith(('.', '__pycache__', 'node_modules', 'vcpkg'))]
            for f in files:
                if f.endswith(('.py', '.md', '.xml', '.json', '.lua', '.txt')):
                    caminhos.append((root, f))
    else:
        print(f'[Grep] Caminho nao encontrado: {diretorio}')
        return True
    
    for root, fname in caminhos:
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                for i, linha in enumerate(f):
                    if re_padrao.search(linha):
                        rel = os.path.relpath(fpath, BASE)
                        ctx = flgs['--ctx']
                        txt = linha.strip()
                        if ctx > 0:
                            # Show context lines
                            with open(fpath, 'r', encoding='utf-8', errors='replace') as f2:
                                ctx_linhas = f2.readlines()
                            inicio = max(0, i - ctx)
                            fim = min(len(ctx_linhas), i + ctx + 1)
                            for j in range(inicio, fim):
                                marc = '>' if j == i else ' '
                                ln = ctx_linhas[j].rstrip()
                                print(f'  {marc}L{j+1}: {ln}')
                        else:
                            print(f'  {rel}:L{i+1}: {txt}')
                        resultados.append((rel, i+1))
                        if len(resultados) >= flgs['--max']:
                            break
        except: pass
        if len(resultados) >= flgs['--max']:
            break
    
    total = len(resultados) if isinstance(resultados, list) else 0
    extra = max(0, 0)  # placeholder
    print(f'[Grep] {total} resultados | max: {flgs["--max"]}')
    return True
