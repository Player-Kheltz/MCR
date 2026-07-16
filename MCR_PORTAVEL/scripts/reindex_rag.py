"""Recria o indice RAG do zero com conteudo correto."""
import sys, os, time

_MCR_ROOT = os.path.join(os.path.dirname(__file__), '..')
_MCR_KERNEL = os.path.join(_MCR_ROOT, 'devia', 'kernel')
if _MCR_ROOT not in sys.path:
    sys.path.insert(0, _MCR_ROOT)
if _MCR_KERNEL not in sys.path:
    sys.path.insert(0, _MCR_KERNEL)

from rag_mcr import MCRRAG

rag = MCRRAG(reset=True)
t0 = time.time()

# 1. PERSONALIDADE.md (identidade do sistema)
path1 = os.path.join(_MCR_ROOT, 'PERSONALIDADE.md')
with open(path1, 'r', encoding='utf-8') as f:
    n1 = rag.adicionar_texto(f.read(), 'PERSONALIDADE.md')
print(f'PERSONALIDADE.md: {n1} chunks')

# 2. Lore do projeto (definicoes corretas)
path_lore = os.path.join(_MCR_ROOT, 'lore_base')
if os.path.isdir(path_lore):
    for f in os.listdir(path_lore):
        if not f.endswith('.md'): continue
        caminho = os.path.join(path_lore, f)
        with open(caminho, 'r', encoding='utf-8') as fh:
            texto = fh.read()
        if len(texto) > 50:
            n = rag.adicionar_texto(texto, caminho)
            print(f'Lore {f}: {n} chunks')

# 3. Scripts Lua do Canary (NPCs, actions, lib) - so alguns pra teste
canary_base = os.path.join(_MCR_ROOT, 'server')
dirs_lua = [
    os.path.join(canary_base, 'data', 'npclib'),
    os.path.join(canary_base, 'data-canary', 'scripts', 'actions'),
    os.path.join(canary_base, 'data-otservbr-global', 'npc'),
]
total_lua = 0
for diretorio in dirs_lua:
    if not os.path.isdir(diretorio): continue
    for raiz, _, arquivos in os.walk(diretorio):
        for f in arquivos:
            if not f.endswith('.lua'): continue
            if total_lua >= 100: break  # Limite pra nao travar
            caminho = os.path.join(raiz, f)
            try:
                with open(caminho, 'r', encoding='utf-8', errors='replace') as fh:
                    texto = fh.read()
            except Exception: continue
            if len(texto) < 100 or len(texto) > 10000: continue
            rag.adicionar_texto(texto, caminho)
            total_lua += 1
        if total_lua >= 100: break

print(f'Scripts Lua: {total_lua} arquivos')

t = time.time() - t0
print(f'\nTotal: {rag.collection.count()} chunks em {t:.0f}s')
