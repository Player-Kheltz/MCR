#!/usr/bin/env python3
"""Indexa NPCs reais do Canary — corrige diretorios do CanaryIndexer."""
import sys, os, json, time

BASE_MCR = r"E:\MCR"
sys.path.insert(0, BASE_MCR)
sys.path.insert(0, r"E:\Projeto MCR\historia\Scripts\mcr_devia\knowledge")

PROJETO = r"E:\Projeto MCR"

# Importa e corrige NPC_DIRS global
import canary_indexer
canary_indexer.NPC_DIRS = [
    os.path.join(PROJETO, "Canary", "data-otservbr-global", "npc"),
    os.path.join(PROJETO, "Canary", "data-canary", "scripts", "MCR"),
]
CanaryIndexer = canary_indexer.CanaryIndexer

from rag_mcr import MCRRAG

t0 = time.time()
print("=" * 55)
print("  INDEXADOR DE NPCS CANARY — BATCH")
print("=" * 55)

idx = CanaryIndexer()
stats = idx.indexar(forcar=True)

print(f"  NPCs indexados: {stats['npcs']}")
print(f"  Shops: {stats['shops']} | Quests: {stats['quests']}")

if stats['npcs'] == 0:
    print("  ERRO: Nenhum NPC encontrado. Debug:")
    import canary_indexer as ci
    for d in ci.NPC_DIRS:
        print(f"    {d}: existe={os.path.isdir(d)}, count={len(os.listdir(d)) if os.path.isdir(d) else 0}")
    sys.exit(1)

# Alimenta RAG com exemplos de cada tipo
rag = MCRRAG()
tipos = {}
for n in idx.npcs:
    t = n['tipo']
    if t not in tipos:
        tipos[t] = []
    tipos[t].append(n)

alimentados = 0
for tipo, npcs in sorted(tipos.items()):
    amostra = npcs[:5]
    for n in amostra:
        texto = (
            f"NPC: {n['nome']}\n"
            f"Tipo: {n['tipo']}\n"
            f"Arquivo: {n['nome_arquivo']}\n"
            f"Descricao: {n.get('descricao', '')}\n"
            f"Palavras-chave: {', '.join(n.get('palavras_chave', []))}\n"
            f"Itens: {json.dumps(n.get('itens_shop', [])[:5], ensure_ascii=False)}\n"
        )
        try:
            rag.adicionar_texto(texto, fonte=f'canary_indexer/{tipo}/{n["nome"]}')
            alimentados += 1
        except Exception as e:
            print(f"    Erro RAG: {e}")
    print(f"  {tipo}: {len(amostra)} exemplos no RAG ({len(npcs)} total)")

t1 = time.time()
print(f"\n  Total: {alimentados} NPCs no RAG | {t1-t0:.1f}s")
print(f"  Tipos encontrados: {list(tipos.keys())}")
print("  Indexador pronto!\n")
