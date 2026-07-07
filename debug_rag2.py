"""Debug: busca hibrida para SPA."""
import sys, os, re, unicodedata
sys.path.insert(0, r'E:\MCR')
from rag_mcr import MCRRAG

rag = MCRRAG()

# Testa busca hibrida pra SPA
pergunta = 'explique o que e SPA no Projeto MCR'
print(f'Pergunta: {pergunta}')

# Normalizacao
import unicodedata
def norm(t):
    return unicodedata.normalize('NFKD', t).encode('ASCII', 'ignore').decode('ASCII').lower()

termos = set(re.findall(r'\b[a-zA-Z_-]{3,}\b', pergunta))
termos_norm = {norm(t) for t in termos}
print(f'Termos originais: {termos}')
print(f'Termos normalizados: {termos_norm}')

# Pega todos os docs e mostra os que tem SPA try:
resultados = rag.collection.get(limit=rag.collection.count())
for i, doc in enumerate(resultados.get("documents", [])):
    doc_norm = norm(doc)
    if 'spa' in doc_norm:
        fonte = resultados["metadatas"][i].get("fonte", "") if resultados.get("metadatas") else ""
        score = sum(1 for tn in termos_norm if tn in doc_norm) / len(termos_norm)
        print(f'\nMatch SPA (score={score:.2f}) [{fonte}]:')
        print(f'  {doc[:120]}...')

# Testa busca
docs = rag.buscar_hibrido(pergunta, k=3)
print(f'\n\nResultados buscar_hibrido: {len(docs)}')
for d in docs:
    print(f'  [{d.get("fonte","?")} score={d.get("score",0):.2f}] {d["texto"][:80]}')
