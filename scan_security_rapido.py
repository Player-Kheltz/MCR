#!/usr/bin/env python3
"""SCAN DE SEGURANCA RAPIDO — Varre texto e historico Git."""
import os, sys, re, subprocess, time as _time

T0 = _time.time()
def log(msg):
    print(f'[{_time.time()-T0:.1f}s] {msg}', flush=True)

# Padroes de seguranca
PADROES = [
    (r'(?i)(senha|password|passwd|pwd|secret)\s*[=:][^;\n]{8,}', 'SENHA'),
    (r'(?i)(token|api_key|apikey)[=:][^;\n]{8,}', 'TOKEN'),
    (r'(?:ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]{36}', 'GITHUB_TOKEN'),
    (r'-----BEGIN\s+(?:RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY-----', 'CHAVE_PRIV'),
    (r'(?i)connection_string\s*[=:][^;\n]+', 'CONN_STR'),
    (r'mongodb(?:\+srv)?:\/\/[^\s;\'"]+', 'MONGO'),
    (r'postgresql?:\/\/[^\s;\'"]+', 'POSTGRES'),
]

def scan_arquivo(caminho):
    """Escaneia UM arquivo."""
    try:
        with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
            linhas = f.readlines()
    except:
        return []
    
    resultados = []
    for i, linha in enumerate(linhas, 1):
        if any(w in linha.lower() for w in ['exemplo', 'placeholder', 'your_', 'seu_']):
            continue
        for pattern, tipo in PADROES:
            if re.search(pattern, linha):
                resultados.append((tipo, caminho, i, linha.strip()[:100]))
                break
    return resultados

def scan_repo(repo_path, nome):
    """Escaneia repositorio Git."""
    log(f'=== {nome} ===')
    repo_path = os.path.abspath(repo_path)
    if not os.path.exists(os.path.join(repo_path, '.git')):
        log(f'  Nao e um repositorio Git')
        return [], []
    
    total_alertas = []
    
    # 1. Working tree
    log(f'  [1/2] Working tree...')
    n_arquivos = 0
    for root, dirs, files in os.walk(repo_path):
        if '.git' in dirs: dirs.remove('.git')
        if '__pycache__' in dirs: dirs.remove('__pycache__')
        if 'node_modules' in dirs: dirs.remove('node_modules')
        if 'vcpkg' in dirs: dirs.remove('vcpkg')
        if 'sandbox' in dirs: dirs.remove('sandbox')
        
        for fname in files:
            if fname.endswith(('.py', '.md', '.txt', '.json', '.lua', '.cfg', '.ini', '.env', '.yml', '.yaml', '.bat', '.ps1', '.sh', '.conf')):
                fpath = os.path.join(root, fname)
                resultados = scan_arquivo(fpath)
                total_alertas.extend(resultados)
                n_arquivos += 1
    
    log(f'  {n_arquivos} arquivos escaneados')
    
    # 2. Git history (git log -p com grep)
    log(f'  [2/2] Git history...')
    try:
        for pattern, tipo in PADROES:
            r = subprocess.run(
                ['git', '-C', repo_path, 'log', '--all', '-p', '-S', pattern.split('(')[0] if '(' in pattern else pattern[:10]],
                capture_output=True, text=True, timeout=30
            )
            if r.stdout:
                alertas = re.findall(pattern, r.stdout, re.IGNORECASE if '(?i)' in pattern else 0)
                if alertas:
                    log(f'    {tipo}: {len(alertas)} ocorrencias no historico')
                    total_alertas.append((tipo, '[HISTORICO]', 0, f'{len(alertas)} ocorrencias'))
    except Exception as e:
        log(f'  Erro no history: {e}')
    
    return total_alertas


# VARRE AMBOS OS REPOS
todos = []
for path, nome in [(r'E:\Projeto MCR', 'ProjetoMCR'), (r'E:\MCR', 'MCR')]:
    if os.path.exists(path):
        alertas = scan_repo(path, nome)
        todos.extend(alertas)
    else:
        log(f'{nome}: caminho nao encontrado')

# RELATORIO
print()
print('=' * 70)
print('RELATORIO DE SEGURANCA')
print('=' * 70)

if not todos:
    print('\n✅ NENHUM ALERTA ENCONTRADO')
else:
    print(f'\n⚠️  {len(todos)} ALERTAS:')
    for tipo, arq, linha, conteudo in todos:
        print(f'  [{tipo}] {arq}:{linha}')
        print(f'    {conteudo}')

print(f'\nTempo total: {_time.time()-T0:.1f}s')
print('=' * 70)
