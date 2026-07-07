"""Teste RAG: indexa docs do projeto e busca por conteudo."""
import sys, os, time
sys.path.insert(0, r'E:\MCR')
from rag_mcr import MCRRAG

print("=" * 50)
print("RAG MCR — Teste de Indexacao e Busca")
print("=" * 50)

rag = MCRRAG(reset=True)
print(f"\n[1] Indexando documentos-chave...")
t0 = time.time()

# Indexa so documentos-chave (nao diretorios inteiros)
chaves = [
    r"E:\Projeto MCR\PERSONALIDADE.md",
    r"E:\Projeto MCR\docs\MCR - Instrucoes\[Personalidade] MCR - Personalidade e Identidade de Dominios.txt",
]
total_chunks = 0
for path in chaves:
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        texto = f.read()
    for i in range(0, len(texto), 500-50):
        chunk = texto[i:i+500]
        if not chunk.strip():
            continue
        import urllib.request, json, hashlib
        emb = None
        try:
            payload = json.dumps({"model": "nomic-embed-text", "prompt": chunk[:500]}).encode()
            req = urllib.request.Request("http://localhost:11434/api/embeddings", data=payload, headers={"Content-Type":"application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                emb = json.loads(r.read())["embedding"]
        except:
            continue
        if emb:
            rag.collection.add(
                ids=[hashlib.md5(chunk.encode()).hexdigest()[:16]],
                documents=[chunk],
                metadatas=[{"fonte": os.path.basename(path)}],
                embeddings=[emb]
            )
            total_chunks += 1

t = time.time() - t0
print(f"  {total_chunks} chunks em {t:.1f}s")
print(f"  Stats: {rag.stats()}")

print(f"\n[2] Testando buscas...")
testes = [
    "o que e SPA no Projeto MCR",
    "como funciona a propagacao 4:2:1",
    "pilares permanentes do projeto",
    "encoding de arquivos lua",
]

for pergunta in testes:
    print(f"\n  Pergunta: {pergunta}")
    t0 = time.time()
    docs = rag.buscar(pergunta, k=2)
    t = time.time() - t0
    print(f"  Encontrados: {len(docs)} chunks em {t*1000:.0f}ms")
    for d in docs:
        print(f"    [{os.path.basename(d['fonte'])}] {d['texto'][:100]}...")
    
    # Mostra o contexto formatado pro LLM
    contexto = rag.contexto_para_prompt(pergunta, k=2)
    print(f"  Contexto pro LLM: {len(contexto)} chars")

# Teste com LLM
print(f"\n[3] Teste com LLM (com e sem RAG)...")
import urllib.request, json

pergunta = "explique o que e SPA"
contexto = rag.contexto_para_prompt(pergunta, k=3)

# Sem RAG
prompt_sem = f"Responda em PT-BR: {pergunta}"
payload = json.dumps({"model": "qwen2.5-coder:7b", "prompt": prompt_sem,
                      "stream": False, "options": {"num_predict": 256}}).encode()
req = urllib.request.Request("http://localhost:11434/api/generate", data=payload,
                             headers={"Content-Type": "application/json"})
t0 = time.time()
with urllib.request.urlopen(req, timeout=60) as r:
    resp_sem = json.loads(r.read()).get("response", "")
t_sem = time.time() - t0
print(f"  SEM RAG ({t_sem:.1f}s): {resp_sem[:120]}...")

# Com RAG
prompt_com = f"{contexto}\nBaseado no contexto acima, responda: {pergunta}"
payload = json.dumps({"model": "qwen2.5-coder:7b", "prompt": prompt_com,
                      "stream": False, "options": {"num_predict": 256}}).encode()
req = urllib.request.Request("http://localhost:11434/api/generate", data=payload,
                             headers={"Content-Type": "application/json"})
t0 = time.time()
with urllib.request.urlopen(req, timeout=60) as r:
    resp_com = json.loads(r.read()).get("response", "")
t_com = time.time() - t0
print(f"  COM RAG ({t_com:.1f}s): {resp_com[:120]}...")

print(f"\n  SEM: {'SPA' in resp_sem and 'Single' in resp_sem}")
print(f"  COM: {'SPA' in resp_com and ('Progressao' in resp_com or 'Aventureiro' in resp_com)}")
