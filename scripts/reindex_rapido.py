"""Reindexa rapido: so PERSONALIDADE.md + lore."""
import sys, os, time
sys.path.insert(0, r'E:\MCR')
from rag_mcr import MCRRAG

rag = MCRRAG(reset=True)
t0 = time.time()

# 1. PERSONALIDADE.md
path = r'E:\Projeto MCR\PERSONALIDADE.md'
with open(path, 'r', encoding='utf-8') as f:
    n = rag.adicionar_texto(f.read(), 'PERSONALIDADE.md')
print(f'PERSONALIDADE.md: {n} chunks ({time.time()-t0:.0f}s)')

# 2. Lore do projeto
lore = r'E:\Projeto MCR\lore_base\mcr_systems.md'
if os.path.exists(lore):
    with open(lore, 'r', encoding='utf-8') as f:
        rag.adicionar_texto(f.read(), lore)
    print(f'Lore: 1 arquivo')

print(f'\nTotal: {rag.collection.count()} chunks em {time.time()-t0:.0f}s')
