import sys, os, time, urllib.request, json
sys.path.insert(0, r'E:\MCR')
from rag_mcr import MCRRAG

rag = MCRRAG()
pergunta = 'explique o que e SPA no Projeto MCR'

# Debug da busca
docs = rag.buscar_hibrido(pergunta, k=5)
print('Resultados busca TF-IDF:')
for d in docs:
    score = d.get('score', 0)
    fonte = d.get('fonte', '?')
    texto = d.get('texto', '')[:100]
    print(f'  score={score:.3f} [{fonte}] {texto}')
