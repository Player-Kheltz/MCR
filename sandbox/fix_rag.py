#!/usr/bin/env python3
"""Diagnostico e correcao do RAG load_index()."""
import sys, json, numpy as np
sys.path.insert(0, r"E:\Projeto MCR\scripts")

RAG_DIR = r"E:\Projeto MCR\.rag_db"

# Diagnostico
with open(RAG_DIR + "/index.json", encoding="utf-8", errors="replace") as f:
    index = json.load(f)

embeddings = np.load(RAG_DIR + "/embeddings.npy")
chunks = index.get("chunks", [])
sources = index.get("sources", {})

print(f"chunks: {len(chunks)}")
print(f"embeddings: {len(embeddings)}")
print(f"sources dict: {len(sources)} chaves")

if len(chunks) != len(embeddings):
    print(f"ERRO: {len(chunks)} chunks vs {len(embeddings)} embeddings")
    # Ajusta para o menor tamanho
    min_len = min(len(chunks), len(embeddings))
    chunks = chunks[:min_len]
    embeddings = embeddings[:min_len]
    print(f"Ajustado para {min_len}")
    index["chunks"] = chunks
    with open(RAG_DIR + "/index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    print("Corrigido e salvo!")
else:
    print(f"OK: {len(chunks)} chunks para {len(embeddings)} embeddings")

# Teste de busca
from rag_query import get_context
ctx = get_context("SPA", top_k=3, player_mode=True)
if ctx:
    print(f"\nBusca de teste 'SPA' (player_mode=True): {len(ctx)} chars")
    print(f"Primeiros 100: {ctx[:100]}")
else:
    print("\nBusca de teste 'SPA': vazio")
    
ctx2 = get_context("fogo habilidade", top_k=3, player_mode=False)
if ctx2:
    print(f"Busca de teste 'fogo habilidade': {len(ctx2)} chars")
else:
    print("Busca de teste 'fogo habilidade': vazio")
