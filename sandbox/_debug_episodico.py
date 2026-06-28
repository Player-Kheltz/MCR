"""Debug da EpisodicMemory."""
import sys
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.episodic_memory import EpisodicMemory, _extrair_termos, _gerar_embedding, _cosine_similaridade

mem = EpisodicMemory()
mem.limpar()

# Registra
mem.registrar("cria ferreiro em eridanus", {'sucesso': True}, "shop")
mem.registrar("cria pocoes magicas", {'sucesso': True}, "items")
mem.registrar("cria guarda da cidade", {'sucesso': False}, "permissoes")

# Debug busca
consulta = "calcular imposto de renda"
print(f"Consulta: '{consulta}'")
termos = _extrair_termos(consulta)
print(f"Termos extraidos: {termos}")

if mem._has_embedding:
    emb = _gerar_embedding(consulta)
    print(f"Embedding gerado: {len(emb) if emb else 0} dimensoes")
    if emb:
        # Testa similaridade com cada episodio
        for ep in mem.episodios:
            if 'embedding' in ep:
                sim = _cosine_similaridade(emb, ep['embedding'])
                match_terms = sum(1 for t in termos if t in ep.get('termos', []))
                print(f"  vs '{ep['request'][:30]}': sim={sim:.3f}, match_terms={match_terms}")
else:
    print("Embedding NAO disponivel")
    # Testa fallback keywords
    for ep in mem.episodios:
        match_terms = sum(1 for t in termos if t in ep.get('termos', []))
        print(f"  vs '{ep['request'][:30]}': match_terms={match_terms}")

print("\nBusca (antes do fix manual):")
resultados = mem.buscar(consulta, n=2)
print(f"Resultados: {len(resultados)}")
for r in resultados:
    print(f"  - {r['request'][:50]}")
