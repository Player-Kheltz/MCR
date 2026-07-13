"""modulos.pattern_engine — Redireciona para mcr.pattern_miner."""
import re

try:
    from devia.kernel.mcr_kernel.signature import raw_token_set
except ImportError:
    raw_token_set = lambda t: set(re.findall(r'\b[a-zA-Z]{3,}\b', t.lower()))


class PatternEngine:
    def __init__(self):
        self._padroes = []

    def detectar(self, texto):
        tokens = raw_token_set(texto)
        padroes_encontrados = []
        if re.search(r'\b(function|local|end|if|then|else|for|while|return|import|class|def|var|let|const)\b', texto):
            padroes_encontrados.append('codigo')
        if re.search(r'\b(npc|monster|quest|spell|action)\b', texto, re.I):
            padroes_encontrados.append('tibia')
        return padroes_encontrados
