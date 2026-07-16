"""bridge.py — Analogias cross-domain (MCRBridge).

Princípio MCR:
  Dados dois pares de entidades (A1,A2) e (B1,B2), verifica se
  a transformação A1→A2 é análoga a B1→B2 usando delta de fingerprints.

Uso:
  bridge = MCRBridge()
  resultado = bridge.analogia("ferreiro", "mago", "dragao", "demonio")
  → score de similaridade entre as transformações
"""
import math
from typing import Dict, List


class MCRBridge:
    """Analogias cross-domain via delta de fingerprints."""

    def __init__(self, dim: int = 8):
        self.dim = dim
        self.total = 0
        self._historico: List[Dict] = []

    def analogia(self, a1, a2, b1, b2) -> Dict:
        """Verifica se a transformação a1→a2 é análoga a b1→b2.

        Args:
            a1, a2: entidades no domínio A
            b1, b2: entidades no domínio B
        Returns:
            {'sim': similaridade, 'nota': score, 'analogo': True/False}
        """
        da = self._delta(a1, a2)
        db = self._delta(b1, b2)
        sim = self._similaridade(da, db)
        note = sim
        self.total += 1
        resultado = {
            'sim': round(sim, 3),
            'nota': round(note, 3),
            'analogo': note > 0.5,
        }
        self._historico.append(resultado)
        return resultado

    def _delta(self, x, y) -> List[float]:
        """Delta entre dois fingerprints."""
        fx = self._fingerprint(x)
        fy = self._fingerprint(y)
        d = self.dim or max(len(fx), len(fy), 1)
        delta = [0.0] * d
        for i in range(min(len(fx), len(fy), d)):
            delta[i] = abs(fx[i] - fy[i])
        return delta

    def _fingerprint(self, texto) -> List[float]:
        """Fingerprint genérico baseado em bytes."""
        if isinstance(texto, str):
            dados = texto.encode('utf-8')
        elif isinstance(texto, bytes):
            dados = texto
        else:
            dados = str(texto).encode('utf-8')

        d = self.dim
        buckets = [0.0] * d
        for b in dados:
            buckets[b % d] += 1
        total = sum(buckets) or 1
        return [b / total for b in buckets]

    def _similaridade(self, a: List[float], b: List[float]) -> float:
        """Similaridade cosseno entre dois vetores."""
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def estatisticas(self) -> Dict:
        """Resumo de analogias realizadas."""
        analogas = sum(1 for h in self._historico if h['analogo'])
        return {
            'total': self.total,
            'analogas': analogas,
            'pct_analogo': round(analogas / max(self.total, 1) * 100, 1),
        }
