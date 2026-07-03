"""Teste da EpisodicMemory (Fase 1)."""
import sys, os, time
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.episodic_memory import EpisodicMemory

print("=== Teste EpisodicMemory (Fase 1) ===")
mem = EpisodicMemory()
mem.limpar()  # começa limpo

# --- Teste 1: Registrar ---
print("\n1. Registrar experiencias...")
id1 = mem.registrar("cria ferreiro em eridanus", {'sucesso': True}, "usar templates shop para ferreiro")
id2 = mem.registrar("cria pocoes magicas", {'sucesso': True}, "usar items.xml para pocoes")
id3 = mem.registrar("cria guarda da cidade", {'sucesso': False}, "guardas precisam de permissao especial")
print(f"   IDs: {id1}, {id2}, {id3}")
assert id1 and id2 and id3, "Falhou ao registrar"

# --- Teste 2: Busca similar ---
print("\n2. Busca por 'cria npc ferreiro'...")
resultados = mem.buscar("cria npc ferreiro", n=2)
print(f"   Encontrados: {len(resultados)}")
for r in resultados:
    print(f"   - [{r['id']}] {r['request'][:50]} (score de similaridade)")
assert len(resultados) >= 1, "Deveria encontrar ferreiro"

# --- Teste 3: Busca sem match ---
print("\n3. Busca sem match...")
resultados = mem.buscar("calcular imposto de renda", n=2)
print(f"   Encontrados: {len(resultados)} (esperado: 0)")
assert len(resultados) == 0, "Nao deveria encontrar nada"

# --- Teste 4: Persistencia ---
print("\n4. Persistencia...")
mem2 = EpisodicMemory()
print(f"   Memoria 1: {len(mem.episodios)} episodios")
print(f"   Memoria 2: {len(mem2.episodios)} episodios")
assert len(mem2.episodios) == len(mem.episodios), "Persistencia falhou"

# --- Teste 5: Sucesso pesa mais ---
print("\n5. Experiencia com sucesso tem prioridade...")
# ja temos: ferreiro (sucesso=True), guarda (sucesso=False)
resultados = mem.buscar("cria guarda", n=2)
print(f"   Encontrados: {len(resultados)}")
for r in resultados:
    print(f"   - [{r['id']}] {r['request'][:50]} sucesso={r['sucesso']}")

# --- Teste 6: Metricas ---
print("\n6. Metricas...")
metrics = mem.metricas()
print(f"   Total: {metrics['total']}")
print(f"   Taxa sucesso: {metrics['taxa_sucesso']}")
print(f"   Com embedding: {metrics['com_embedding']}")
print(f"   Cache embeddings: {metrics['cache_embeddings']}")

# --- Teste 7: Embedding direto ---
print("\n7. Teste embedding (se disponivel)...")
if mem._has_embedding:
    from modulos.episodic_memory import _gerar_embedding
    emb = _gerar_embedding("cria npc ferreiro")
    if emb:
        print(f"   Embedding gerado: {len(emb)} dimensoes")
        print(f"   Primeiros 5 valores: {emb[:5]}")
    else:
        print("   Falha ao gerar embedding")
else:
    print("   Embedding NAO disponivel")

print("\n=== TODOS OS TESTES PASSARAM ===")
mem.limpar()  # limpa ao final
