"""EpisodicGateway — Ponte entre EpisodicMemory e MCRCoupling.

Converte memórias episódicas em features markovianas que o coupling
entende. Usado como fonte de decisão EPI em coupling.decidir().

Pilar 1: P(acao | ep:licao) — transição markoviana.
Pilar 5: memórias são registradas e reconsultadas (loop fechado).
Pilar 7: correlação universal — qualquer experiência vira feature.
"""
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class EpisodicGateway:

    def __init__(self, episodic_memory=None):
        self._mem = episodic_memory
        self._cache_consulta: Dict[str, List[Tuple[str, float]]] = {}

    def registrar(self, request: str, resultado, licao: str = "") -> None:
        if self._mem is None:
            return
        self._mem.registrar(request, resultado, licao)

    def consultar(self, texto: str, n: int = 3) -> Dict[str, float]:
        if self._mem is None:
            return {}

        cache_key = f"{texto}|{n}"
        if cache_key in self._cache_consulta:
            return self._cache_consulta[cache_key]

        resultados = self._mem.buscar(texto, n=n)
        if not resultados:
            return {}

        dist: Dict[str, float] = defaultdict(float)
        for ep in resultados:
            resultado_str = str(ep.get('resultado', ''))
            score = ep.get('_score_reforco', 0.5)
            sucesso = ep.get('sucesso', False)
            peso = score * (1.3 if sucesso else 0.7)
            palavras = resultado_str.lower().split()
            for p in palavras:
                dist[p] += peso / max(len(palavras), 1)

        if not dist:
            return {}
        total = sum(dist.values()) or 1.0
        dist_norm = {k: v / total for k, v in dist.items()}
        self._cache_consulta[cache_key] = dist_norm
        return dist_norm

    def limpar_cache(self) -> None:
        self._cache_consulta.clear()