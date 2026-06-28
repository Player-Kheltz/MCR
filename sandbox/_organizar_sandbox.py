"""Organiza a sandbox em subpastas para melhor organizacao."""
import os, shutil, glob

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SANDBOX = os.path.join(BASE, 'sandbox')

# Mapeamento: padrao do arquivo -> pasta destino
ORGANIZACAO = {
    # NPCs gerados
    'npc_*.lua': 'npcs_gerados',
    '*_npc.lua': 'npcs_gerados',
    'npc.lua': 'npcs_gerados',
    '*.lua': 'npcs_gerados',  # generico lua
    # Testes
    '_test_*.py': 'testes',
    'test_*.py': 'testes',
    # Relatorios
    '.mcr_*_report.json': 'relatorios',
    '.mcr_*_log.jsonl': 'relatorios',
    'autoteste_*.json': 'relatorios',
    'autoteste_*.txt': 'relatorios',
    # Caches
    '.mcr_*.json': 'caches',
    '*.json': 'caches',
    '*.jsonl': 'caches',
    # Projetos gerados
    'jogo_*/': 'projetos_gerados',
    'app_*/': 'projetos_gerados',
    'bot_*/': 'projetos_gerados',
    'sistema_*/': 'projetos_gerados',
}

print("Organizando sandbox...")
print(f"  Pasta: {SANDBOX}")

# Cria as pastas de destino
pastas_criadas = set()
for padrao, destino in ORGANIZACAO.items():
    path = os.path.join(SANDBOX, destino)
    if destino not in pastas_criadas:
        os.makedirs(path, exist_ok=True)
        pastas_criadas.add(destino)

# Move arquivos (apenas os que estao na raiz da sandbox, nao em subpastas)
movidos = 0
for item in os.listdir(SANDBOX):
    item_path = os.path.join(SANDBOX, item)
    
    # Pula pastas que ja sao de organizacao
    if os.path.isdir(item_path) and item in pastas_criadas:
        continue
    # Pula pastas .mcr_devia, .git, etc
    if item.startswith('.'):
        continue
    
    # Determina destino
    item_lower = item.lower()
    destino = None
    for padrao, pasta in ORGANIZACAO.items():
        if padrao.endswith('/'):
            # Padrao de pasta
            if os.path.isdir(item_path) and item_lower.startswith(padrao[:-1]):
                destino = pasta
                break
        else:
            # Padrao de arquivo (glob)
            import fnmatch
            if fnmatch.fnmatch(item_lower, padrao) or fnmatch.fnmatch(item, padrao):
                destino = pasta
                break
    
    if destino:
        dest_path = os.path.join(SANDBOX, destino, item)
        try:
            shutil.move(item_path, dest_path)
            movidos += 1
            print(f"  Moveu: {item} -> {destino}/")
        except Exception as e:
            print(f"  ERRO ao mover {item}: {e}")

print(f"\n  Total: {movidos} arquivos/pastas organizados")
print("  OK")
