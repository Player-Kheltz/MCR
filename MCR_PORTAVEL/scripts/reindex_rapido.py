"""Reindexa rapido: so PERSONALIDADE.md + lore."""
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

# 1. PERSONALIDADE.md
path = os.path.join(_MCR_ROOT, 'PERSONALIDADE.md')
with open(path, 'r', encoding='utf-8') as f:
    n = rag.adicionar_texto(f.read(), 'PERSONALIDADE.md')
print(f'PERSONALIDADE.md: {n} chunks ({time.time()-t0:.0f}s)')

# 2. Lore do projeto
lore = os.path.join(_MCR_ROOT, 'lore_base', 'mcr_systems.md')
if os.path.exists(lore):
    with open(lore, 'r', encoding='utf-8') as f:
        rag.adicionar_texto(f.read(), lore)
    print(f'Lore: 1 arquivo')

print(f'\nTotal: {rag.collection.count()} chunks em {time.time()-t0:.0f}s')
