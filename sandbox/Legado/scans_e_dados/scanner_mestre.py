"""MCR-DevIA — Scanner Mestre para todo o projeto MCR"""
import os, sys

# Importa o scanner do resolver_ultra
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Carrega as funcoes detectoras
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resolver_ultra.py'), 'rb') as f:
    src = f.read().decode('utf-8', errors='replace')

idx = src.find("if __name__ == '__main__':")
func_part = src[:idx] if idx > 0 else src
ns = {}
exec(func_part, ns)

# Filtra detectores
DETECTORES = {}
for nome in list(ns.keys()):
    if nome.startswith('detectar_') and callable(ns[nome]) and nome != 'detectar_encoding_latin1':
        DETECTORES[nome] = ns[nome]

def detectar_encoding(path):
    with open(path, 'rb') as f:
        raw = f.read(2000)
    try:
        raw.decode('utf-8')
        return None
    except UnicodeDecodeError:
        try:
            raw.decode('latin-1')
            return 'encoding'
        except:
            return 'encoding desconhecido'

def scan_arquivo(path):
    """Scan individual file returning list of problems."""
    problemas = []
    
    # Encoding
    enc = detectar_encoding(path)
    if enc:
        problemas.append(enc)
    
    # Leitura de texto
    with open(path, 'rb') as f:
        raw = f.read()
    try:
        texto = raw.decode('utf-8')
    except:
        texto = raw.decode('latin-1', errors='replace')
    
    # Nome longo
    nome = os.path.basename(path)
    if len(nome) > 60:
        problemas.append(f'nome longo ({len(nome)} chars)')
    
    # Detectores
    for nome_det, fn in sorted(DETECTORES.items()):
        try:
            if fn(texto):
                tag = nome_det.replace('detectar_', '').replace('_', ' ')
                if tag not in problemas:
                    problemas.append(tag)
        except:
            pass
    
    return problemas

# Diretorios para escanear (apenas .lua)
DIRS = [
    (r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades', 'habilidades'),
    (r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA', 'SPA (geral)'),
    (r'E:\Projeto MCR\Canary\data-canary\scripts\MCR', 'MCR scripts'),
]

EXCLUDE_DIRS = {'_backup_encoding', '__pycache__', '.git'}

print('='*70)
print('  MCR-DevIA — SCANNER MESTRE')
print('  Varrendo diretorios MCR em busca de problemas')
print('='*70)

total_arquivos = 0
total_problemas = 0
todos_resultados = {}

for base_dir, label in DIRS:
    if not os.path.exists(base_dir):
        print(f'\n  [AVISO] Diretorio nao encontrado: {base_dir}')
        continue
    
    print(f'\n--- {label}: {base_dir} ---')
    dir_arquivos = 0
    dir_problemas = 0
    
    for root, dirs, files in os.walk(base_dir):
        # Filtra diretorios de exclusao
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for f in sorted(files):
            if not f.endswith('.lua'): continue
            if '.bak' in f.lower(): continue
            if f == '.GABARITO.txt': continue
            
            path = os.path.join(root, f)
            problemas = scan_arquivo(path)
            total_arquivos += 1
            dir_arquivos += 1
            
            if problemas:
                total_problemas += 1
                dir_problemas += 1
                rel = os.path.relpath(path, base_dir)
                print(f'\n  [!] {rel}')
                for p in problemas:
                    ps = p.encode('ascii', 'replace').decode('ascii')
                    print(f'      - {ps}')
    
    if dir_arquivos > 0:
        pct = (dir_arquivos - dir_problemas) * 100 // dir_arquivos
        print(f'  -> {dir_problemas}/{dir_arquivos} com problemas ({pct}% limpo)')
    else:
        print(f'  -> Nenhum arquivo .lua encontrado')

print(f'\n{"="*70}')
print(f'  SCAN FINAL: {total_problemas}/{total_arquivos} arquivos com problemas')
print(f'  {total_arquivos - total_problemas}/{total_arquivos} limpos ({(total_arquivos-total_problemas)*100//max(1,total_arquivos)}%)')
print(f'{"="*70}')
