"""Debug: verifica estrutura do RAG index."""
import sys, json, os
sys.path.insert(0, r"E:\Projeto MCR\scripts")
from rag_query import load_index, is_player_source

result = load_index()
print("Tipo do resultado:", type(result))

if isinstance(result, tuple):
    data = result[0]
    chunks_list = data.get("chunks", [])
    print("Chunks na lista:", len(chunks_list))
    
    # Mostra estrutura dos primeiros
    for i, chunk in enumerate(chunks_list[:5]):
        print(f"  [{i}] id={chunk.get('id','?')} source={chunk.get('source','?')[:60]} text={chunk.get('text','')[:80]}")
        print(f"      player_source={is_player_source(chunk.get('source',''))}")
    
    # Conta quantos sao player_source
    total_ps = sum(1 for c in chunks_list if is_player_source(c.get('source', '')))
    print(f"\nTotal chunks: {len(chunks_list)}")
    print(f"Player source: {total_ps}")
    print(f"Other source: {len(chunks_list) - total_ps}")
    
    # Busca chunks de fogo/SPA
    for termo in ["fogo", "spa", "progressao", "orbital"]:
        matches = [c for c in chunks_list if termo.lower() in c.get("text","").lower()[:300]]
        ps_matches = [c for c in matches if is_player_source(c.get("source",""))]
        print(f"\n'{termo}': {len(matches)} encontrados, {len(ps_matches)} player_source")
        if matches:
            print(f"  Exemplo: source={matches[0].get('source','?')} text={matches[0].get('text','')[:100]}")
