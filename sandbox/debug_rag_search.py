"""Debug: testa busca RAG com scores."""
import sys
sys.path.insert(0, r"E:\Projeto MCR\scripts")
from rag_query import search

for query in ["SPA", "Orbital Igneo", "sistema de progressao", "fogo"]:
    print(f"\nQuery: '{query}'")
    for mode_name, mode in [("player_mode=True", True), ("player_mode=False", False)]:
        results = search(query, top_k=3, player_mode=mode)
        print(f"  {mode_name}: {len(results)} resultados")
        for r in results:
            src = r["source"]
            score = r["score"]
            text = r["text"][:80]
            print(f"    [{score:.3f}] {src}")
            print(f"      {text}")
