"""esquecimento.py — MCREsquecimento: poda de estados Markov.

Princípio MCR:
  Entropia descobre estrutura — estados com alta entropia (poucas transições)
  e baixa frequência são ruído. Estados com baixa entropia (muitas transições
  consistentes) são estrutura.

Poda remove estados com frequência < threshold, mantendo a cadeia enxuta.
"""
import math
from collections import Counter
from typing import Dict


class MCREsquecimento:
    """Poda estados Markov por entropia e frequência."""

    def __init__(self, freq_min: int = 2):
        self._freq_min = freq_min

    def podar(self, mk) -> Dict:
        """Remove estados com frequência abaixo do mínimo.

        Retorna estatísticas da poda.
        """
        removidos = 0
        mantidos = 0
        estados_antes = len(mk.transicoes)

        for estado in list(mk.transicoes.keys()):
            total = sum(mk.transicoes[estado].values())
            if total < self._freq_min:
                del mk.transicoes[estado]
                if estado in mk.freq:
                    del mk.freq[estado]
                removidos += 1
            else:
                mantidos += 1

        return {
            'estados_antes': estados_antes,
            'estados_depois': len(mk.transicoes),
            'removidos': removidos,
            'mantidos': mantidos,
            'total_transicoes': mk.total,
        }

    def podar_entropico(self, mk, threshold_h: float = 0.8) -> Dict:
        """Poda estados com alta entropia E baixa frequência.

        Alta entropia = distribuição uniforme entre ações = incerto.
        Se também tem baixa frequência, é ruído.
        """
        removidos = 0
        for estado in list(mk.transicoes.keys()):
            prox = mk.transicoes[estado]
            total = sum(prox.values())
            if total < 2:
                h = 1.0
            else:
                h = 0.0
                for c in prox.values():
                    p = c / total
                    if p > 0:
                        h -= p * math.log2(p)
                max_h = math.log2(max(len(prox), 2))
                h = h / max_h if max_h > 0 else 1.0

            if h > threshold_h and total < 3:
                del mk.transicoes[estado]
                if estado in mk.freq:
                    del mk.freq[estado]
                removidos += 1

        return {
            'estados_antes': len(mk.transicoes),
            'removidos': removidos,
        }
