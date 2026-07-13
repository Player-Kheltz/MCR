"""modulos.lexico_v2 — Tokenizador Markov universal.

Redireciona para mcr.markov_router.MCRMarkovRouter.
"""
import re
from collections import Counter

try:
    from mcr.markov_router import MCRMarkovRouter as _Router

    def tokenizar_v2(texto):
        return re.findall(r'\b[a-zA-Z0-9_]{2,}\b', texto.lower())

    def tokenizar_v2_mcr(texto):
        tokens = tokenizar_v2(texto)
        return {t: ('mcr' if len(t) > 3 and any(k in t.lower() for k in ['mcr', 'code', 'lua', 'npc']) else 'llm') for t in tokens}

    def tipos_unicos():
        return {'mcr', 'llm', 'desconhecido'}

    def verificar_markov(token, router=None):
        if router is None:
            router = _Router()
        pred, conf = router.mk_palavra.predizer(token)
        return pred, conf

    _CATEGORIA_PATTERNS = {
        'mcr': re.compile(r'\b(mcr|markov|kg|pattern|npc|lua|canary|tibia)\b', re.I),
        'llm': re.compile(r'\b(llm|gpt|openai|transformer|token|prompt)\b', re.I),
    }
except ImportError:
    def tokenizar_v2(texto):
        return re.findall(r'\b[a-zA-Z0-9_]{2,}\b', texto.lower())

    def tokenizar_v2_mcr(texto):
        return {t: 'desconhecido' for t in tokenizar_v2(texto)}

    def tipos_unicos():
        return {'desconhecido'}

    def verificar_markov(token, router=None):
        return token, 0.0

    _CATEGORIA_PATTERNS = {}
