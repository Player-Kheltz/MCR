"""Comando: verificar_mudancas - Detecta alteracoes nos arquivos do MCR-DevIA."""
import os, hashlib, json, time

DEVIA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MANIFEST_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'sandbox', '.mcr_devia', 'file_manifest.json')

def register():
    return {
        "name": "verificar_mudancas",
        "desc": "Detecta alteracoes em arquivos do MCR-DevIA desde a ultima verificacao",
        "handler": execute,
        "args": [],
        "categoria": "kernel",
    }

def _hash_file(path):
    """Hash SHA256 de um arquivo."""
    try:
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return None

def execute(kg, ia, args, ctx_crew=None):
    # Carrega manifest anterior
    manifest = {}
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except: pass
    
    # Escaneia arquivos atuais
    alteracoes = []
    novos = []
    removidos = []
    
    # Arquivos para monitorar
    extensoes = ('.py', '.md', '.json', '.txt')
    pastas = [DEVIA_DIR]
    
    for pasta in pastas:
        for root, dirs, files in os.walk(pasta):
            dirs[:] = [d for d in dirs if not d.startswith(('.', '__pycache__', 'vcpkg'))]
            for f in files:
                if not f.endswith(extensoes): continue
                fpath = os.path.join(root, f)
                rel = os.path.relpath(fpath, DEVIA_DIR)
                
                hash_atual = _hash_file(fpath)
                if not hash_atual: continue
                
                if rel in manifest:
                    if manifest[rel] != hash_atual:
                        alteracoes.append(rel)
                else:
                    novos.append(rel)
                
                manifest[rel] = hash_atual
    
    # Detecta removidos
    for rel in list(manifest.keys()):
        fpath = os.path.join(DEVIA_DIR, rel)
        if not os.path.exists(fpath):
            removidos.append(rel)
            del manifest[rel]
    
    # Salva manifest atualizado
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    # Relatorio
    total = sum(1 for v in manifest.values())
    print(f'[Verificar] {total} arquivos monitorados')
    
    if alteracoes:
        print(f'[Verificar] {len(alteracoes)} arquivos ALTERADOS:')
        for a in alteracoes:
            print(f'  - {a}')
    if novos:
        print(f'[Verificar] {len(novos)} NOVOS arquivos:')
        for n in novos:
            print(f'  + {n}')
    if removidos:
        print(f'[Verificar] {len(removidos)} REMOVIDOS:')
        for r in removidos:
            print(f'  - {r}')
    
    if not alteracoes and not novos and not removidos:
        print('[Verificar] Nenhuma alteracao detectada')
    else:
        total_mudancas = len(alteracoes) + len(novos) + len(removidos)
        print(f'[Verificar] Total: {total_mudancas} mudancas')
        
        # Se tem alteracoes e kg disponivel, registra
        if kg and alteracoes:
            for a in alteracoes:  # So as 3 primeiras para nao poluir
                try:
                    with open(os.path.join(DEVIA_DIR, a), 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    kg.aprender(
                        erro=f"Arquivo alterado: {a}",
                        causa=f"Detectado por verificar_mudancas em {time.strftime('%Y-%m-%d %H:%M')}",
                        solucao=f"Arquivo foi modificado. Hash antigo: {manifest.get(a, '?')}...",
                        ctx="mudanca"
                    )
                except: pass
    
    return True
