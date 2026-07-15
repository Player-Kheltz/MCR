"""mundo.py — Modelo causal MCR.

Princípio MCR:
  TUDO é P(b|a) — aprende P(estado_next | estado_atual, ação)
  Descoberta causal reversa: P(ação | delta_estado)

Uso:
  mundo = MCRMundo()
  mundo.aprender("ferreiro", "gerar_npc", "ferreiro.lua")
  mundo.predizer_acao("ferreiro", "ferreiro.lua") → "gerar_npc"
"""
from collections import defaultdict
from typing import Dict, List, Tuple, Optional


class MCRMundo:
    """Modelo causal: aprende efeitos de ações e infere causas."""

    def __init__(self):
        # estado → estado_next
        self._estado: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        # estado + ação → estado_next
        self._acao: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        # delta → ação (descoberta causal reversa)
        self._causal: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.total = 0

    def aprender(self, antes: str, acao: str, depois: str):
        """Aprende transição causal: (antes, ação) → depois."""
        self.total += 1
        self._estado[antes][depois] += 1
        chave_acao = f"{antes}|{acao}"
        self._acao[chave_acao][depois] += 1
        delta = self._calcular_delta(antes, depois)
        self._causal[delta][acao] += 1

    def predizer_estado(self, atual: str) -> Optional[str]:
        """Prediz próximo estado (sem ação específica)."""
        dist = self._estado.get(atual, {})
        if not dist:
            return None
        return max(dist, key=dist.get)

    def simular(self, atual: str, acao: str) -> Optional[str]:
        """Simula: dado estado e ação, qual o próximo estado?"""
        chave = f"{atual}|{acao}"
        dist = self._acao.get(chave, {})
        if not dist:
            return None
        return max(dist, key=dist.get)

    def predizer_acao(self, antes: str, depois: str) -> Optional[str]:
        """Descoberta causal reversa: qual ação transforma A em B?"""
        delta = self._calcular_delta(antes, depois)
        dist = self._causal.get(delta, {})
        if not dist:
            return None
        return max(dist, key=dist.get)

    def _calcular_delta(self, antes: str, depois: str) -> str:
        """Delta entre dois estados como fingerprint."""
        tokens_a = set(antes.split('|'))
        tokens_b = set(depois.split('|'))
        added = tokens_b - tokens_a
        removed = tokens_a - tokens_b
        return f"+{len(added)}-{len(removed)}"

    def estatisticas(self) -> Dict:
        return {
            'total': self.total,
            'estados': len(self._estado),
            'acoes': len(self._acao),
            'causais': len(self._causal),
        }
