"""Decider — Classificador universal via FAST model (+ fallback deterministico).

Substitui regex/dict fixos por decisoes do FAST model.
Nao substitui seguranca deterministica (COMANDOS_BLOQUEADOS).
Cache LRU com TTL para evitar chamadas repetidas ao LLM.

Uso:
    decider = Decider(ia)
    tipo = decider.classificar("Cria um jogo em Python",
                                ['projeto_jogo', 'criar_codigo', 'pergunta'])
    # -> 'projeto_jogo'

    dados = decider.extrair_json("Cria um jogo de plataforma",
                                  {'nome': '', 'linguagem': ''})
    # -> {'nome': 'jogo_plataforma', 'linguagem': 'python'}
"""
import json, hashlib, time

# Cache LRU global com TTL
_cache = {}


def _cache_key(*args):
    return hashlib.md5(':'.join(str(a) for a in args).encode()).hexdigest()


def _get_cache(key, ttl=300):
    """Retorna valor do cache se ainda valido (TTL em segundos)."""
    entry = _cache.get(key)
    if entry and time.time() - entry['ts'] < ttl:
        return entry['valor']
    return None


def _set_cache(key, valor):
    """Armazena valor no cache com timestamp."""
    _cache[key] = {'valor': valor, 'ts': time.time()}
    # Poda simples: se cache crescer demais, limpa os mais antigos
    if len(_cache) > 500:
        velhos = sorted(_cache.keys(), key=lambda k: _cache[k]['ts'])
        for k in velhos:
            del _cache[k]


class Decider:
    """Tomador de decisoes universal via FAST model.

    Faz classificacoes e extracoes usando o FAST model (qwen2.5-coder:7b).
    Cache LRU com TTL 5min para evitar chamadas repetidas.
    Fallback deterministico se IA nao estiver disponivel.
    """

    def __init__(self, ia=None):
        self.ia = ia

    def classificar(self, texto, categorias, instrucao="", exemplos=None):
        """Classifica texto em uma das categorias via FAST.

        Args:
            texto: O que classificar (request, consulta, etc)
            categorias: Lista de opcoes validas (ex: ['local', 'cloud'])
            instrucao: Contexto extra para o prompt (opcional)
            exemplos: Lista de (texto_exemplo, categoria) para guiar o modelo

        Returns:
            str: Categoria escolhida, ou primeira opcao como fallback
        """
        key = _cache_key(texto, str(categorias), str(exemplos))
        cached = _get_cache(key)
        if cached:
            return cached

        if not self.ia:
            _set_cache(key, categorias[0])
            return categorias[0]

        # Monta prompt com exemplos (mais confiavel que instrucoes abstratas)
        prompt = ""
        if exemplos:
            prompt += "Exemplos:\n"
            for ex_texto, ex_cat in exemplos:  # max 6 exemplos
                prompt += f"{ex_texto} -> {ex_cat}\n"
            prompt += "\n"
        if instrucao:
            prompt += f"{instrucao}\n"
        prompt += (
            f"Categorias: {', '.join(categorias)}\n"
            f"Texto: {texto}\n"
            f"Categoria:"
        )

        try:
            resp = self.ia.fast(prompt, 0.1, "leve").strip().lower()
            # Tenta match exato primeiro
            for cat in categorias:
                if resp == cat.lower():
                    _set_cache(key, cat)
                    return cat
            # Match parcial (se veio "resposta: cloud" ou similar)
            for cat in categorias:
                if cat.lower() in resp:
                    _set_cache(key, cat)
                    return cat
        except Exception as e:
            print(f"[Decider] classificar error: {e}")

        _set_cache(key, categorias[0])
        return categorias[0]

    def extrair_json(self, texto, esquema_exemplo, instrucao="", exemplos=None):
        """Extrai dados estruturados via FAST.

        Args:
            texto: Texto para analisar (request, consulta)
            esquema_exemplo: Dict exemplificando a estrutura (ex: {'nome': ''})
            instrucao: Contexto extra (opcional)
            exemplos: Lista de (texto_exemplo, json_exemplo) para guiar o modelo

        Returns:
            dict: Dados extraidos (campos do esquema preenchidos)
        """
        key = _cache_key(texto, str(esquema_exemplo), str(exemplos))
        cached = _get_cache(key)
        if cached:
            return cached

        if not self.ia:
            _set_cache(key, esquema_exemplo)
            return dict(esquema_exemplo)

        campos = list(esquema_exemplo.keys())
        prompt = ""
        if exemplos:
            prompt += "Exemplos:\n"
            for ex_texto, ex_json in exemplos:
                prompt += f'"{ex_texto}" -> {json.dumps(ex_json, ensure_ascii=False)}\n'
            prompt += "\n"
        if instrucao:
            prompt += f"{instrucao}\n"
        prompt += (
            f"Responda APENAS com JSON. Campos: {', '.join(campos)}\n"
            f"Texto: {texto}\n"
            f"JSON:"
        )

        try:
            resp = self.ia.fast(prompt, 0.1, "leve")
            # Tenta extrair JSON da resposta (pode vir com texto antes)
            m = __import__('re').search(r'\{.*\}', resp, __import__('re').DOTALL)
            if m:
                dados = json.loads(m.group(0))
            else:
                dados = json.loads(resp)
            for k in campos:
                if k not in dados:
                    dados[k] = ''
            _set_cache(key, dados)
            return dados
        except Exception as e:
            pass
            # Se falhou, tenta parse mais agressivo
            try:
                resp_lower = resp.lower().strip()
                dados = {}
                for k in campos:
                    m = __import__('re').search(f'"{k}"\\s*:\\s*"([^"]+)"', resp_lower)
                    if m:
                        dados[k] = m.group(1)
                    else:
                        dados[k] = ''
                if any(dados.values()):
                    _set_cache(key, dados)
                    return dados
            except Exception:
                pass
            _set_cache(key, esquema_exemplo)
            return dict(esquema_exemplo)

    def limpar_cache(self):
        """Limpa o cache de decisoes."""
        _cache.clear()
