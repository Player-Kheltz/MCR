"""modulos.context_enricher — Enriquecimento de contexto via KG."""
import re

try:
    from devia.kernel.mcr_kernel.signature import raw_token_set
except ImportError:
    raw_token_set = lambda t: set(re.findall(r'\b[a-zA-Z]{3,}\b', t.lower()))


class ContextEnricher:
    def __init__(self):
        self._kg = {}

    def enriquecer(self, contexto, pergunta=''):
        tokens_pergunta = raw_token_set(pergunta) if pergunta else set()
        tokens_contexto = raw_token_set(contexto) if contexto else set()
        intersecao = tokens_pergunta & tokens_contexto
        return {
            'tokens_relevantes': list(intersecao)[:10],
            'relevancia': len(intersecao) / max(len(tokens_pergunta | tokens_contexto), 1),
            'contexto_enriquecido': contexto,
        }

    def _classificar_carencia(self, pergunta):
        return 'geral'
