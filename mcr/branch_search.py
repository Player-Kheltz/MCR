"""BranchSearcher — Raciocínio multi-passo via busca em árvore.

Gera N caminhos de predição, avalia cada um com Equação 5D,
escolhe o melhor. "Pensar antes de falar" — explora múltiplas
hipóteses antes de commit.

Pilar 2: entropia decide quais caminhos explorar.
Pilar 5: cada caminho é avaliado e refinado (loop fechado).
Equação 5D: avalia qualidade de cada caminho candidato.

Uso:
    bs = BranchSearcher(coupling)
    melhor_caminho, nota = bs.buscar("criar monstro")
"""
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import math, re


class BranchSearcher:

    def __init__(self, coupling, n_caminhos: int = 3, profundidade: int = 2):
        self._coupling = coupling
        self._n_caminhos = n_caminhos
        self._profundidade = profundidade

    def buscar(self, texto: str) -> Tuple[str, float]:
        caminhos = self._gerar_caminhos(texto, self._profundidade)
        if not caminhos:
            acao, conf = self._predizer_interno(texto)
            return acao or "responder", conf

        melhor_caminho = None
        melhor_nota = -1.0

        for acao, sequencia in caminhos:
            nota = self._avaliar_caminho(texto, acao, sequencia)
            if nota > melhor_nota:
                melhor_nota = nota
                melhor_caminho = acao

        if melhor_caminho is None:
            acao, conf = self._predizer_interno(texto)
            return acao or "responder", conf

        return melhor_caminho, melhor_nota

    def _predizer_interno(self, texto: str) -> Tuple[Optional[str], float]:
        """Predição ligeira sem recursão: usa só _dist_palavras + _dist_features."""
        scores: Dict[str, float] = defaultdict(float)
        d1 = self._coupling._dist_palavras(texto)
        if d1:
            for a, v in d1.items():
                scores[a] += v * 0.6
        d2 = self._coupling._dist_features(texto)
        if d2:
            for a, v in d2.items():
                scores[a] += v * 0.4
        if not scores:
            return None, 0.0
        melhor = max(scores, key=scores.get)
        return melhor, scores[melhor]

    def _gerar_caminhos(self, texto: str, prof: int) -> List[Tuple[str, List[str]]]:
        acao, conf = self._predizer_interno(texto)
        if not acao:
            return []

        caminhos = [(acao, [acao])]
        visitados = {acao}

        for _ in range(prof - 1):
            novos = []
            for acao_atual, seq in caminhos:
                texto_expandido = f"{texto} {acao_atual}"
                prox_acao, prox_conf = self._predizer_interno(texto_expandido)
                if prox_acao and prox_acao not in visitados and prox_conf > 0.3:
                    visitados.add(prox_acao)
                    novos.append((prox_acao, seq + [prox_acao]))
            if novos:
                novos.sort(key=lambda x: -self._predizer_interno(f"{texto} {x[0]}")[1])
                caminhos.extend(novos[:self._n_caminhos])

        return caminhos[:self._n_caminhos]

    def _avaliar_caminho(self, texto: str, acao: str,
                          sequencia: List[str]) -> float:
        try:
            from mcr.equacao_mcr import avaliar_5d
        except ImportError:
            try:
                from equacao_mcr import avaliar_5d
            except ImportError:
                return 0.5

        _, conf = self._predizer_interno(texto)

        certeza = conf

        palavras_texto = set(self._coupling.tokenizar_universal(texto))
        palavras_acao = set(re.findall(r'[a-zà-ÿ]{2,}', acao.lower()))
        compartilhadas = palavras_texto & palavras_acao
        completude = len(compartilhadas) / max(len(palavras_acao), 1) if palavras_acao else 0.0

        palavras_seq = set()
        for s in sequencia:
            for p in re.findall(r'[a-zà-ÿ]{2,}', s.lower()):
                palavras_seq.add(p)
        n_distintas = len(palavras_seq)
        informacao = min(1.0, math.log2(n_distintas + 1) / math.log2(20))

        estabilidade = math.exp(-((informacao - 0.5) ** 2) / (2 * 0.1 ** 2))

        n_passos = len(sequencia)
        eficiencia = 1.0 / math.log2(max(n_passos + 1, 2))

        return avaliar_5d(certeza, completude, informacao, estabilidade, eficiencia)