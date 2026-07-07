import sys; sys.path.insert(0, r'E:\MCR')
from rag_mcr import MCRRAG

rag = MCRRAG()
count = rag.collection.count()
print(f'Collection count: {count}')
if count > 0:
    results = rag.collection.peek()
    print(f'First doc metadata: {results["metadatas"][0]}')
    print(f'First doc text: {results["documents"][0][:100]}')
    
    # Test de busca
    import urllib.request, json
    payload = json.dumps({"model": "nomic-embed-text", "prompt": "o que e SPA"}).encode()
    req = urllib.request.Request("http://localhost:11434/api/embeddings", data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            emb = json.loads(r.read()).get("embedding")
        if emb:
            results = rag.collection.query(query_embeddings=[emb], n_results=3)
            print(f'Query results: {len(results.get("documents", [[]])[0])} docs')
            for d in results.get("documents", [[]])[0]:
                print(f'  - {d[:80]}...')
    except Exception as e:
        print(f'Erro: {e}')
else:
    print('Collection empty. Add some docs first.')
