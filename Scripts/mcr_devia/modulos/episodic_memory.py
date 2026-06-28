"""EpisodicMemory — Memória episódica com embeddings + fallback keywords.

Armazena experiências (request + resultado + lição) e busca por similaridade.
Usa nomic-embed-text para embeddings (768 floats) quando disponível,
fallback para busca por palavras-chave.

Uso:
    mem = EpisodicMemory()
    mem.registrar("cria ferreiro", {...}, "usar templates shop")
    resultados = mem.buscar("cria npc ferreiro em eridanus")
"""
import os, json, time, re, hashlib, math
import urllib.request

# Path da memória (mesmo diretório do KG)
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MEMORIA_PATH = os.path.join(BASE, 'sandbox', '.mcr_episodios.json')

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api')

MAX_EPISODIOS = int(os.environ.get('MCR_MAX_EPISODIOS', '1000'))
EMBED_MODEL = 'nomic-embed-text:latest'

# Cache de embeddings para evitar chamadas repetidas
_embedding_cache = {}

# Stop words para extração de termos
STOP_WORDS = {
    'para', 'com', 'que', 'como', 'mais', 'mas', 'por', 'sao', 'esta',
    'pode', 'ser', 'tem', 'seu', 'sua', 'entre', 'sobre', 'quando',
    'onde', 'quem', 'qual', 'cada', 'todo', 'apos', 'isso', 'esse',
    'num', 'sem', 'sob', 'ate', 'sao', 'vai', 'era', 'foi', 'nos',
    'dos', 'das', 'nos', 'nas', 'numa', 'pelo', 'pela', 'aos', 'as',
}


def _cosine_similaridade(a, b):
    """Similaridade cosseno entre dois vetores."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _gerar_embedding(texto):
    """Gera embedding via Ollama. Retorna lista de floats ou None."""
    if texto in _embedding_cache:
        return _embedding_cache[texto]

    try:
        dados = json.dumps({
            'model': EMBED_MODEL,
            'prompt': texto[:500],  # limita tamanho
        }).encode()
        req = urllib.request.Request(
            f'{OLLAMA_URL}/embeddings',
            data=dados,
            headers={'Content-Type': 'application/json'}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
        embedding = resp.get('embedding')
        if embedding:
            _embedding_cache[texto] = embedding
            return embedding
    except Exception as e:
        print(f"[EpisodicMemory] Embedding error: {e}")

    return None


def _extrair_termos(texto):
    """Extrai termos relevantes para busca (4+ chars, sem stop words)."""
    palavras = re.findall(r'\b[a-zA-Z]{4,}\b', texto.lower())
    return list(set(p for p in palavras if p not in STOP_WORDS))[:15]


class EpisodicMemory:
    """Memória de experiências com busca híbrida (embeddings + keywords)."""

    def __init__(self, max_episodios=None):
        self.max_episodios = max_episodios or MAX_EPISODIOS
        self.episodios = self._carregar()
        self._has_embedding = self._verificar_embedding()

    def _verificar_embedding(self):
        """Verifica se modelo de embedding está disponível no Ollama."""
        try:
            req = urllib.request.Request(f'{OLLAMA_URL}/tags')
            resp = json.loads(urllib.request.urlopen(req, timeout=5).read())
            for m in resp.get('models', []):
                if 'nomic' in m.get('name', ''):
                    return True
        except Exception:
            pass
        return False

    def _carregar(self):
        """Carrega episódios do arquivo JSON."""
        if os.path.exists(MEMORIA_PATH):
            try:
                with open(MEMORIA_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def salvar(self):
        """Salva episódios, mantendo apenas os mais recentes."""
        os.makedirs(os.path.dirname(MEMORIA_PATH), exist_ok=True)
        # Poda: mantém só os N mais recentes
        if len(self.episodios) > self.max_episodios:
            self.episodios.sort(key=lambda e: e.get('timestamp', 0), reverse=True)
            self.episodios = self.episodios[:self.max_episodios]
        with open(MEMORIA_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.episodios, f, ensure_ascii=False, indent=2)

    def registrar(self, request, resultado, licao=""):
        """Registra uma experiência completa com embedding."""
        termos = _extrair_termos(request)

        episodio = {
            'id': hashlib.md5(f"{request}{time.time()}".encode()).hexdigest()[:12],
            'timestamp': time.time(),
            'request': request,
            'sucesso': resultado.get('sucesso', False) if isinstance(resultado, dict) else True,
            'resultado': str(resultado)[:300],
            'licao': licao[:300],
            'termos': termos,
            'reusos': 0,
        }

        # Tenta gerar embedding (vetor completo de 768 floats, ~3KB por episódio)
        if self._has_embedding:
            try:
                emb = _gerar_embedding(request)
                if emb and len(emb) > 10:
                    episodio['embedding'] = emb  # vetor completo salvo no JSON
            except Exception:
                pass

        self.episodios.append(episodio)
        self.salvar()
        return episodio['id']

    def buscar(self, request, n=3):
        """Busca episódios relevantes por similaridade semântica + keywords.

        Score híbrido (se embeddings disponíveis):
            - 70% similaridade cosseno
            - 30% match de keywords + recência + sucesso

        Fallback (sem embeddings):
            - 100% keywords + recência + sucesso
        """
        termos_request = _extrair_termos(request)
        if not termos_request and not self._has_embedding:
            return []

        # Gera embedding da consulta (se disponível)
        emb_request = None
        if self._has_embedding:
            try:
                emb_request = _gerar_embedding(request)
            except Exception:
                pass

        agora = time.time()
        scores = []

        for ep in self.episodios:
            # --- Filtro principal: KEYWORDS (pelo menos 1 match) ---
            match = sum(1 for t in termos_request if t in ep.get('termos', []))
            if match == 0:
                continue  # sem match de keyword, descarta

            score = 0.0

            # --- Embedding: boost de similaridade semântica (opcional) ---
            if emb_request and 'embedding' in ep and len(ep['embedding']) > 10:
                emb_ep = ep['embedding']
                score_sem = _cosine_similaridade(emb_request, emb_ep)
                # Embedding contribui com até 40% do score (boost, não filtro)
                score += 0.4 * score_sem

            # --- Keywords contribuem com o restante ---
            peso_keywords = min(1.0, match / max(len(termos_request), 1))
            peso_kw = 0.6 if emb_request else 1.0  # sem embedding = 100% keywords
            score += peso_kw * peso_keywords

            # --- Bônus de recência e sucesso (multiplicativo) ---
            dias = (agora - ep.get('timestamp', 0)) / 86400
            peso_recente = max(0.3, 1.0 - dias * 0.02)
            peso_sucesso = 1.3 if ep.get('sucesso', False) else 0.7
            score *= peso_recente * peso_sucesso

            # Threshold mínimo
            if score < 0.15:
                continue

            scores.append((score, ep))

        if not scores:
            return []

        scores.sort(key=lambda x: -x[0])

        # Marca como reusado
        for _, ep in scores[:n]:
            ep['reusos'] = ep.get('reusos', 0) + 1

        return [s[1] for s in scores[:n]]

    def limpar(self):
        """Limpa toda a memória."""
        self.episodios = []
        if os.path.exists(MEMORIA_PATH):
            os.remove(MEMORIA_PATH)

    def metricas(self):
        """Retorna métricas da memória."""
        if not self.episodios:
            return {'total': 0, 'taxa_sucesso': '0%', 'com_embedding': self._has_embedding}

        total = len(self.episodios)
        sucessos = sum(1 for e in self.episodios if e.get('sucesso', False))
        mais_reusada = max(self.episodios, key=lambda e: e.get('reusos', 0))

        return {
            'total': total,
            'taxa_sucesso': f'{sucessos / total * 100:.0f}%' if total > 0 else '0%',
            'com_embedding': self._has_embedding,
            'cache_embeddings': len(_embedding_cache),
            'mais_reutilizada': mais_reusada.get('request', '')[:80] if total > 0 else '',
        }
