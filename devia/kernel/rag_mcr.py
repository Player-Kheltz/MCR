"""MCR-RAG — Retrieval-Augmented Generation para o Projeto MCR.
Usa ChromaDB + nomic-embed-text (Ollama) pra indexar e buscar docs do projeto."""
import os, json, time, hashlib, re, unicodedata
import urllib.request
import chromadb
from chromadb.utils import embedding_functions

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE, "cache", "rag")
os.makedirs(CACHE_DIR, exist_ok=True)

OLLAMA_URL = "http://localhost:11434/api/embeddings"
OLLAMA_CHAT = "http://localhost:11434/api/generate"

DOCS_DIRS = [
    os.path.join(BASE, "..", "Projeto MCR"),
    os.path.join(BASE, "..", "Projeto MCR", "docs"),
    os.path.join(BASE, "..", "Projeto MCR", "docs", "MCR - Instrucoes"),
]

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def embed_text(texto):
    """Gera embedding via nomic-embed-text no Ollama."""
    payload = json.dumps({"model": "nomic-embed-text", "prompt": texto}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload,
                                headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["embedding"]
    except Exception as e:
        print(f"[RAG] Erro embedding: {e}")
        return None


# ─── Client ChromaDB ───────────────────────────────────────────

class MCRRAG:
    """RAG do Projeto MCR: indexa docs, busca por similaridade."""
    
    def __init__(self, reset=False):
        self.client = chromadb.PersistentClient(path=CACHE_DIR)
        self.collection = None
        self._total_docs = 0
        self._inicializar(reset)
    
    def _inicializar(self, reset=False):
        """Cria ou carrega a colecao de documentos."""
        nome = "mcr_docs"
        if reset:
            try:
                self.client.delete_collection(nome)
            except:
                pass
        
        try:
            self.collection = self.client.get_collection(nome)
            self._total_docs = self.collection.count()
        except:
            self.collection = self.client.create_collection(
                name=nome,
                metadata={"hnsw:space": "cosine"}
            )
            self._total_docs = 0
    
    def _chunk_texto(self, texto, fonte=""):
        """Divide texto em chunks preservando secoes (##) e incluindo titulo da secao."""
        if not texto:
            return []
        
        # Divide por secoes (## Titulo)
        secoes_raw = re.split(r'^(#+ .+)$', texto, flags=re.MULTILINE)
        
        chunks = []
        titulo_atual = ""
        i = 0
        while i < len(secoes_raw):
            parte = secoes_raw[i].strip()
            if not parte:
                i += 1
                continue
            if parte.startswith('#') and len(parte) > 2:
                titulo_atual = parte
                i += 1
                continue
            
            # Acrescenta o titulo no inicio do chunk
            texto_completo = f"{titulo_atual}: {parte}" if titulo_atual else parte
            
            if len(texto_completo) < 80:
                # Muito curto, tenta juntar com o proximo
                if i + 1 < len(secoes_raw) and not secoes_raw[i+1].startswith('#'):
                    texto_completo += "\n" + secoes_raw[i+1]
                    i += 1
            
            # Divide secoes longas
            for j in range(0, len(texto_completo), CHUNK_SIZE - CHUNK_OVERLAP):
                chunk = texto_completo[j:j + CHUNK_SIZE]
                if not chunk.strip():
                    continue
                chunk_id = hashlib.md5(f"{fonte}:{i}:{j}".encode()).hexdigest()[:16]
                chunks.append({
                    "id": chunk_id,
                    "texto": chunk.strip()[:500],
                    "fonte": fonte,
                    "pos": j,
                })
            
            i += 1
        
        return chunks
    
    def indexar_diretorio(self, base_dir, max_arquivos=200):
        """Indexa todos os arquivos .md .txt .py .lua .cpp de um diretorio."""
        if not os.path.isdir(base_dir):
            return 0
        
        count = 0
        ext_validas = {'.md', '.txt', '.py', '.lua', '.cpp', '.hpp', '.cs'}
        ignorar = {'__pycache__', '.git', 'vcpkg', 'node_modules', 'Backup', 'bin', 'obj'}
        
        for raiz, dirs, arquivos in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in ignorar and not d.startswith('.')]
            for f in arquivos:
                if count >= max_arquivos:
                    break
                _, ext = os.path.splitext(f)
                if ext.lower() not in ext_validas:
                    continue
                caminho = os.path.join(raiz, f)
                try:
                    with open(caminho, 'r', encoding='utf-8', errors='replace') as fh:
                        texto = fh.read()
                except:
                    continue
                if len(texto) < 50:
                    continue
                chunks = self._chunk_texto(texto, caminho)
                self._adicionar_chunks(chunks)
                count += len(chunks)
            if count >= max_arquivos:
                break
        
        self._total_docs = self.collection.count()
        return count
    
    def _adicionar_chunks(self, chunks):
        """Adiciona chunks ao ChromaDB (em lotes)."""
        if not chunks:
            return
        
        ids = []
        textos = []
        metadatas = []
        embeddings = []
        
        for c in chunks:
            emb = embed_text(c["texto"])
            if emb is None:
                continue
            ids.append(c["id"])
            textos.append(c["texto"])
            metadatas.append({"fonte": c["fonte"][-100:]})
            embeddings.append(emb)
        
        if not ids:
            return
        
        try:
            self.collection.add(
                ids=ids,
                documents=textos,
                metadatas=metadatas,
                embeddings=embeddings
            )
            self._total_docs = self.collection.count()
        except Exception as e:
            print(f"[RAG] Erro adicionar: {e}")
    
    def adicionar_texto(self, texto, fonte=""):
        """Adiciona um texto ao indice RAG."""
        chunks = self._chunk_texto(texto, fonte)
        self._adicionar_chunks(chunks)
        return len(chunks)
    
    def _normalizar(self, texto):
        """Remove acentos pra matching."""
        return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII').lower()
    
    def buscar_hibrido(self, pergunta, k=3):
        """Busca hibrida: query nativa do ChromaDB (sem get() enorme)."""
        self._total_docs = self.collection.count()
        if self._total_docs == 0:
            return []
        
        # Tenta query com embedding + keyword via ChromaDB nativo
        try:
            resultados = self.collection.query(
                query_texts=[pergunta],
                n_results=min(k * 3, self._total_docs),
            )
        except:
            return self.buscar(pergunta, k)
        
        docs = resultados.get("documents", [[]])[0]
        if not docs:
            return self.buscar(pergunta, k)
        
        # Keyword re-ranking leve sobre os resultados do ChromaDB
        termos = set(re.findall(r'\b[a-zA-ZÀ-ÿ_]{3,}\b', pergunta.lower()))
        docs_com_score = []
        for i, doc in enumerate(docs):
            score = 1.0
            if termos:
                dn = self._normalizar(doc)
                matches = sum(1 for t in termos if self._normalizar(t) in dn)
                score += matches / max(len(termos), 1) * 10
            fonte = ""
            metas = resultados.get("metadatas", [[]])[0]
            if i < len(metas):
                fonte = metas[i].get("fonte", "") if isinstance(metas[i], dict) else ""
            docs_com_score.append({"texto": doc[:300], "fonte": fonte, "score": score})
        
        docs_com_score.sort(key=lambda x: -x["score"])
        return docs_com_score[:k]
    
    def buscar(self, pergunta, k=3):
        """Busca os K chunks mais relevantes para a pergunta."""
        # Garante que o contador esteja atualizado
        self._total_docs = self.collection.count()
        if self._total_docs == 0:
            return []
        
        emb = embed_text(pergunta)
        if emb is None:
            return []
        
        try:
            resultados = self.collection.query(
                query_embeddings=[emb],
                n_results=min(k, self._total_docs)
            )
        except Exception as e:
            print(f"[RAG] Erro busca: {e}")
            return []
        
        docs_encontrados = []
        if resultados and resultados.get("documents"):
            for i, doc_lista in enumerate(resultados["documents"]):
                for j, doc in enumerate(doc_lista):
                    fonte = ""
                    if resultados.get("metadatas"):
                        fonte = resultados["metadatas"][i][j].get("fonte", "")
                    docs_encontrados.append({
                        "texto": doc[:300],
                        "fonte": fonte,
                        "distancia": resultados.get("distances", [[0]])[i][j] if resultados.get("distances") else 0,
                    })
        
        return docs_encontrados
    
    def contexto_para_prompt(self, pergunta, k=3, max_chars=2000):
        """Formata contexto RAG pra injetar no prompt do LLM."""
        docs = self.buscar_hibrido(pergunta, k)
        if not docs:
            return ""
        
        partes = []
        chars = 0
        for d in docs:
            texto = f"[{os.path.basename(d['fonte'])}] {d['texto']}"
            if chars + len(texto) > max_chars:
                break
            partes.append(texto)
            chars += len(texto)
        
        return "### CONTEXTO DO PROJETO MCR:\n" + "\n\n".join(partes) + "\n### FIM CONTEXTO\n"
    
    def stats(self):
        return {
            "total_docs_indexados": self._total_docs,
            "colecao": "mcr_docs",
            "path": CACHE_DIR,
        }
