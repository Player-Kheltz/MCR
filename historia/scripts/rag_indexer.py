#!/usr/bin/env python3
"""
rag_indexer.py — Indexa codigo fonte e docs do MCR para busca semantica.

Uso:
    python "scripts/rag_indexer.py"              # Indexa tudo (modo normal)
    python "scripts/rag_indexer.py" --force      # Reindexa do zero
    python "scripts/rag_indexer.py" --stats      # Mostra estatisticas do indice

Arquitetura:
  - Le arquivos .cpp, .hpp, .lua, .h, .txt, .md de Canary/ e OTClient/
  - Divide em chunks de ~2000 chars com overlap de 200
  - Gera embeddings via Ollama (nomic-embed-text)
  - Salva em .rag_db/ (JSON + numpy)
"""
import os, sys, json, time, glob, hashlib, fnmatch
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAG_DIR = os.path.join(BASE_DIR, ".rag_db")
EMBED_URL = "http://localhost:11434/api/embed"
EMBED_MODEL = "nomic-embed-text:latest"

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200

INCLUDE_DIRS = [
    # Core
    os.path.join(BASE_DIR, "docs"),
    os.path.join(BASE_DIR, "Canary", "src"),
    os.path.join(BASE_DIR, "OTClient", "src"),
    os.path.join(BASE_DIR, "OTClient", "modules"),
    os.path.join(BASE_DIR, "Scripts"),
    # Canary data (server-side scripts)
    os.path.join(BASE_DIR, "Canary", "data-canary", "scripts"),
    os.path.join(BASE_DIR, "Canary", "data-otservbr-global", "scripts"),
    # Canary data/scripts/ subdirs (cobertura completa)
    os.path.join(BASE_DIR, "Canary", "data", "scripts", "talkactions"),
    os.path.join(BASE_DIR, "Canary", "data", "scripts", "actions"),
    os.path.join(BASE_DIR, "Canary", "data", "scripts", "creaturescripts"),
    os.path.join(BASE_DIR, "Canary", "data", "scripts", "globalevents"),
    os.path.join(BASE_DIR, "Canary", "data", "scripts", "movements"),
    os.path.join(BASE_DIR, "Canary", "data", "scripts", "spells"),
    os.path.join(BASE_DIR, "Canary", "data", "scripts", "runes"),
    os.path.join(BASE_DIR, "Canary", "data", "scripts", "weapons"),
    os.path.join(BASE_DIR, "Canary", "data", "scripts", "systems"),
    os.path.join(BASE_DIR, "Canary", "data", "scripts", "eventcallbacks"),
    os.path.join(BASE_DIR, "Canary", "data", "scripts", "lib"),
    os.path.join(BASE_DIR, "Canary", "data", "scripts", "libs"),
]
INCLUDE_EXTS = (".cpp", ".hpp", ".h", ".lua", ".txt", ".md", ".otui")
EXCLUDE_DIRS = ["build", ".git", "vcpkg_installed", "Backup", "node_modules", "__pycache__", ".rag_db", "docs/assets"]
EXCLUDE_FILES = ["extraido.txt", "reparado.txt", "traduzido.txt", "ficheiros_modificados.txt", "Lista de Items Uteis.txt", "relatorio_itens.txt", "Ordem.txt"]
EXCLUDE_FILE_PATTERNS = ["nomes_monstros*.txt", "test_*.py", "tmp_*", "bridge_*.txt", "bridge_*.log"]

# Padroes de exclusao para informacoes sensiveis
EXCLUDE_PATTERNS = [
    "*config.lua", "*.env", "*password*", "*secret*",
    "*senha*", "*.key", "*credential*", "*token*",
    "*apikey*", "*apikey*", "*.pem", "*id_rsa*"
]

# Linhas sensiveis que serao removidas do chunk ANTES de indexar
SENSITIVE_LINE_PATTERNS = [
    "password", "passwd", "senha", "secret", "api_key",
    "apiKey", "apikey", "token", "credential", "private_key",
    "mysql://", "postgres://", "mongodb://",
]


def log(msg):
    print(f"[INDEX] {msg}", flush=True)


def _embed_batch(batch_texts, batch_start, batch_size, total_batches, batch_num):
    """Envia um unico lote para a API de embedding. Usado por get_embeddings."""
    truncated = [t[:8000] for t in batch_texts]
    payload = json.dumps({
        "model": EMBED_MODEL,
        "input": truncated
    }).encode()
    req = urllib.request.Request(
        EMBED_URL, data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read())
        embs = data.get("embeddings", [])
        log(f"  lote {batch_num}/{total_batches}: {len(batch_texts)} embeddings (concluido)")
        return (batch_start, embs)
    except Exception as e:
        log(f"  lote {batch_num}/{total_batches}: ERRO - {e}")
        return (batch_start, [])


def get_embeddings(texts, batch_size=100, max_workers=4):
    """
    Gera embeddings em paralelo via Ollama.
    - Divide textos em lotes de batch_size
    - Envia MULTIPLOS lotes simultaneamente via ThreadPoolExecutor
    - max_workers=4 envia 4 lotes de uma vez (ajuste conforme GPU)
    """
    results = [None] * len(texts)
    total_batches = max(1, (len(texts) - 1) // batch_size + 1)
    
    # Prepara todos os lotes
    batches = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_num = i // batch_size + 1
        batches.append((batch, i, batch_num))
    
    log(f"  Enviando {total_batches} lotes em paralelo (workers={max_workers})...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for batch, start, batch_num in batches:
            fut = executor.submit(_embed_batch, batch, start, batch_size, total_batches, batch_num)
            futures[fut] = start
        
        for fut in as_completed(futures):
            start, embs = fut.result()
            for j, emb in enumerate(embs):
                if start + j < len(results):
                    results[start + j] = emb
    
    # Relatorio final
    success = sum(1 for r in results if r is not None)
    log(f"  Embeddings concluidos: {success}/{len(texts)} bem-sucedidos")
    return results


def sanitize_text(text):
    """Remove linhas com informacoes sensiveis do texto."""
    lines = text.split("\n")
    clean = []
    for line in lines:
        lower = line.lower().strip()
        # Remove linhas que parecem conter credenciais
        if any(p in lower for p in SENSITIVE_LINE_PATTERNS):
            # So remove se parecer uma atribuicao (contem = ou : )
            if "=" in line or ":" in line:
                continue
        clean.append(line)
    return "\n".join(clean)

def chunk_text(text, source):
    """Divide texto em chunks com overlap."""
    text = sanitize_text(text)
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            # Tenta quebrar no final de linha
            newline = text.rfind("\n", start + CHUNK_SIZE // 2, end)
            if newline > start:
                end = newline
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunk_id = hashlib.md5(f"{source}:{start}".encode()).hexdigest()[:12]
            chunks.append({"id": chunk_id, "source": source, "text": chunk_text, "pos": start})
        start = end - CHUNK_OVERLAP if end < len(text) else len(text)
    return chunks


def scan_files():
    """Encontra todos os arquivos indexaveis."""
    files = []
    for inc_dir in INCLUDE_DIRS:
        if not os.path.exists(inc_dir):
            continue
        for root, dirs, fnames in os.walk(inc_dir):
            # Pula diretorios excluidos
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for fname in fnames:
                if fname.endswith(INCLUDE_EXTS) and fname not in EXCLUDE_FILES:
                    # Verifica padroes de exclusao de nome
                    if any(fnmatch.fnmatch(fname, p) for p in EXCLUDE_FILE_PATTERNS):
                        continue
                    # Verifica padroes de exclusao sensiveis
                    rel_path = os.path.relpath(os.path.join(root, fname), BASE_DIR)
                    if any(fnmatch.fnmatch(rel_path.lower(), p.lower()) for p in EXCLUDE_PATTERNS):
                        log(f"  EXCLUIDO (sensivel): {rel_path}")
                        continue
                    fpath = os.path.join(root, fname)
                    # Ignora arquivos grandes demais (>5MB)
                    try:
                        if os.path.getsize(fpath) > 5 * 1024 * 1024:
                            continue
                    except OSError:
                        continue
                    files.append(fpath)
    return files


def load_index():
    """Carrega indice existente com embeddings do .npy."""
    index_file = os.path.join(RAG_DIR, "index.json")
    emb_file = os.path.join(RAG_DIR, "embeddings.npy")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            index = json.load(f)
        if os.path.exists(emb_file):
            embs = np.load(emb_file)
            index["embeddings"] = embs.tolist()
            log(f"Embeddings carregados: {len(index['embeddings'])}")
        else:
            index["embeddings"] = []
        return index
    return {"chunks": [], "embeddings": [], "sources": {}}


def save_index(index):
    """Salva indice."""
    os.makedirs(RAG_DIR, exist_ok=True)
    # Salva metadados
    meta = {k: v for k, v in index.items() if k != "embeddings"}
    with open(os.path.join(RAG_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    # Salva embeddings como numpy
    emb_array = np.array(index.get("embeddings", []), dtype=np.float32)
    np.save(os.path.join(RAG_DIR, "embeddings.npy"), emb_array)
    log(f"Salvo: {len(meta['chunks'])} chunks, {emb_array.shape[0] if emb_array.size > 0 else 0} embeddings")


def cmd_index(force=False):
    """Indexa todos os arquivos.
    
    Estrategia de batch otimizada:
    1. Le e chunkifica TODOS os arquivos novos primeiro (barato, rapido)
    2. Gera embeddings de TODOS os chunks de uma vez em grandes lotes (batch_size=100)
    3. Salva UMA vez no final (sem I/O intermediario)
    """
    log("Escaneando arquivos...")
    start_time = time.time()
    files = scan_files()
    log(f"Encontrados {len(files)} arquivos")

    index = load_index() if not force else {"chunks": [], "embeddings": [], "sources": {}}

    # --- PASSO 1: Le e chunkifica todos os arquivos novos ---
    pending_chunks = []   # lista de dicts: {source, text, pos, id, mtime}
    total_processed = 0
    total_skipped = 0

    for idx, fpath in enumerate(files):
        rel_path = os.path.relpath(fpath, BASE_DIR)

        # Progresso a cada 10%
        if (idx + 1) % max(1, len(files) // 20) == 0:
            pct = (idx + 1) / len(files) * 100
            elapsed = time.time() - start_time
            remaining = (elapsed / (idx + 1)) * (len(files) - idx - 1) if idx > 0 else 0
            log(f"[{pct:.0f}%] chunkificando {idx+1}/{len(files)} | {len(pending_chunks)} chunks acumulados | ETA: {remaining:.0f}s")

        # Verifica se arquivo precisa ser (re)indexado
        try:
            mtime = os.path.getmtime(fpath)
        except OSError:
            continue
        cached_mtime = index.get("sources", {}).get(rel_path)
        if cached_mtime and cached_mtime >= mtime and not force:
            total_skipped += 1
            continue

        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except Exception:
            continue

        chunks = chunk_text(text, rel_path)
        if not chunks:
            continue

        # Guarda chunk + mtime para processamento posterior
        for c in chunks:
            c["_mtime"] = mtime
        pending_chunks.extend(chunks)
        total_processed += 1

    log(f"Chunkificacao concluida: {total_processed} arquivos, {len(pending_chunks)} chunks acumulados")

    # --- PASSO 2: Gera embeddings de TODOS os chunks de uma vez ---
    if pending_chunks:
        log(f"Gerando embeddings para {len(pending_chunks)} chunks (batch_size=100)...")
        texts = [c["text"] for c in pending_chunks]
        embs = get_embeddings(texts)

        # Associa embeddings aos chunks
        embedded = 0
        for chunk, emb in zip(pending_chunks, embs):
            if emb:
                index.setdefault("chunks", []).append({
                    "id": chunk["id"],
                    "source": chunk["source"],
                    "text": chunk["text"],
                    "pos": chunk["pos"]
                })
                index.setdefault("embeddings", []).append(emb)
                index["sources"][chunk["source"]] = chunk["_mtime"]
                embedded += 1

        log(f"Embeddings gerados para {embedded}/{len(pending_chunks)} chunks")

        # Salva UMA vez no final
        save_index(index)
    else:
        log("Nenhum arquivo novo para indexar.")

    elapsed = time.time() - start_time
    log(f"Indexacao concluida em {elapsed:.0f}s")
    log(f"  Processados: {total_processed} | Pulados (ja atuais): {total_skipped}")
    log(f"  Total: {len(index['chunks'])} chunks, {len(index['sources'])} arquivos")


def cmd_stats():
    """Mostra estatisticas do indice."""
    index = load_index()
    chunks = index.get("chunks", [])
    embs = index.get("embeddings", [])
    sources = index.get("sources", {})

    log(f"Chunks: {len(chunks)}")
    log(f"Embeddings: {len(embs)}")
    log(f"Arquivos indexados: {len(sources)}")
    log(f"Tamanho estimado: {len(embs) * 4 * 768 / 1024 / 1024:.1f} MB")

    # Top 10 fontes por numero de chunks
    from collections import Counter
    source_counts = Counter(c["source"] for c in chunks)
    log("\nTop 10 fontes:")
    for src, cnt in source_counts.most_common(10):
        log(f"  {cnt:4d}  {src}")


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--force":
        cmd_index(force=True)
    elif len(sys.argv) >= 2 and sys.argv[1] == "--stats":
        cmd_stats()
    else:
        cmd_index(force=False)


if __name__ == "__main__":
    main()
