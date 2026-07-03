#!/usr/bin/env python3
"""
rag_query.py — Busca chunks relevantes no indice RAG.

Uso:
    python "scripts/rag_query.py" "o que e GFB?"
    python "scripts/rag_query.py" "como funciona o SPA?" --top 5
    python "scripts/rag_query.py" "perseguicao multi piso" --context
    python "scripts/rag_query.py" "como funciona o SPA?" --player  # so fontes player-safe
"""
import os, sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAG_DIR = os.path.join(BASE_DIR, ".rag_db")
EMBED_URL = "http://localhost:11434/api/embed"
EMBED_MODEL = "nomic-embed-text:latest"

# Caminhos player-safe (o que o assistente pode usar para responder JOGADORES)
# IMPORTANTE: os source paths do RAG usam o caminho relativo ao BASE_DIR
# Ex: "Canary\data-canary\scripts\MCR\...", "docs\MCR - Instru\u00e7\u00f5es\..."
_PLAYER_SAFE_PATHS = [
    "docs" + os.sep + "MCR - Instru\u00e7\u00f5es",
    "Canary" + os.sep + "data-canary" + os.sep + "scripts" + os.sep + "MCR",
    "Canary" + os.sep + "data" + os.sep + "scripts" + os.sep + "talkactions",
    "Canary" + os.sep + "data" + os.sep + "scripts" + os.sep + "actions",
    "Scripts" + os.sep + "mcr_knowledge.txt",
]


def is_player_source(source):
    """Retorna True se o chunk vem de fonte segura para jogadores."""
    s = source.replace("/", os.sep)
    for p in _PLAYER_SAFE_PATHS:
        if s.startswith(p):
            return True
    return False


def load_index():
    idx_file = os.path.join(RAG_DIR, "index.json")
    emb_file = os.path.join(RAG_DIR, "embeddings.npy")
    if not os.path.exists(idx_file) or not os.path.exists(emb_file):
        return None, None
    with open(idx_file, "r", encoding="utf-8") as f:
        index = json.load(f)
    embeddings = np.load(emb_file)
    return index, embeddings


def get_query_embedding(query):
    payload = json.dumps({"model": EMBED_MODEL, "input": query}).encode()
    req = urllib.request.Request(
        EMBED_URL, data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        return np.array(data["embeddings"][0], dtype=np.float32)
    except Exception as e:
        print(f"[ERRO] embedding: {e}", file=sys.stderr)
        return None


def cosine_similarity(a, b):
    dot = np.dot(a, b)
    return dot / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10)


def search(query, top_k=5, player_mode=False):
    index, embeddings = load_index()
    if index is None:
        print("[ERRO] Indice nao encontrado. Execute rag_indexer.py primeiro.", file=sys.stderr)
        return []

    q_emb = get_query_embedding(query)
    if q_emb is None:
        return []

    chunks = index.get("chunks", [])
    if len(chunks) != len(embeddings):
        print(f"[ERRO] Inconsistencia: {len(chunks)} chunks vs {len(embeddings)} embeddings", file=sys.stderr)
        return []

    scores = []
    for i, emb in enumerate(embeddings):
        # Filtro player-mode: pula chunks de fontes nao seguras
        if player_mode and not is_player_source(chunks[i].get("source", "")):
            continue
        score = cosine_similarity(q_emb, emb)
        scores.append((score, i))

    scores.sort(key=lambda x: x[0], reverse=True)
    # Threshold adaptativo: player_mode ja filtra fontes
    threshold = 0.60 if player_mode else 0.65
    results = []
    for score, i in scores[:top_k]:
        if score > threshold:
            results.append({
                "score": float(score),
                "source": chunks[i].get("source", "?"),
                "text": chunks[i].get("text", "")[:500],
                "id": chunks[i].get("id", "")
            })
    return results


def cmd_search(query, top_k=5, show_context=False, player_mode=False):
    results = search(query, top_k, player_mode=player_mode)
    if not results:
        print("(nenhum resultado relevante)")
        return ""

    context_parts = []
    for i, r in enumerate(results):
        src = r["source"]
        score = r["score"]
        text = r["text"]
        print(f"\n[{i+1}] ({score:.3f}) {src}")
        if show_context:
            print(f"    {text[:300]}...")
        context_parts.append(f"Fonte [{src}]:\n{text}")

    context = "\n\n".join(context_parts)
    return context


def get_context(query, top_k=3, player_mode=False):
    """Retorna string de contexto para usar em prompts (sem prints).
    
    Args:
        query: texto da pergunta
        top_k: numero maximo de chunks
        player_mode: se True, filtra apenas fontes seguras para jogadores
    """
    results = search(query, top_k, player_mode=player_mode)
    if not results:
        return ""
    parts = []
    for r in results:
        parts.append(f"[{r['source']}]: {r['text'][:500]}")
    return "\n\n".join(parts)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    query = sys.argv[1]
    top_k = 5
    show_context = False
    context_only = "--context-only" in sys.argv
    player_mode = "--player" in sys.argv

    if "--top" in sys.argv:
        idx = sys.argv.index("--top")
        if idx + 1 < len(sys.argv):
            top_k = int(sys.argv[idx + 1])
    if "--context" in sys.argv:
        show_context = True

    if context_only:
        print(get_context(query, top_k, player_mode=player_mode))
    else:
        cmd_search(query, top_k, show_context, player_mode=player_mode)


if __name__ == "__main__":
    main()
