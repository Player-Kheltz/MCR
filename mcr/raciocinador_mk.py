"""RaciocinadorMarkoviano — Raciocínio multi-etapa via cadeia de pensamento.

MCR prediz 1 passo. Raciocínio complexo ("Se A>B e B>C, então A>C")
exige múltiplas etapas. Este módulo implementa chain-of-thought
markoviano:

1. Decompõe a pergunta em sub-perguntas
2. Para cada sub-pergunta, prediz resposta via coupling
3. Propaga respostas como contexto para a próxima sub-pergunta
4. Combina todas as respostas via compor()
5. Avalia a cadeia inteira com Equação 5D
6. Se confiança baixa, backtracks e tenta caminho alternativo

Pilar 1: cada passo é P(resposta | pergunta + contexto_acumulado)
Pilar 2: 5D decide se a cadeia é confiável
Pilar 5: cada passo alimenta o próximo (loop encadeado)
Pilar 7: fecho transitivo conecta etapas distantes

Uso:
    rac = RaciocinadorMarkoviano(coupling)
    resposta, confianca = rac.raciocinar("quanto e 2+2+3?")
"""
import re, math
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class RaciocinadorMarkoviano:

    def __init__(self, coupling, profundidade_max: int = 5,
                 n_alternativas: int = 3):
        self._coupling = coupling
        self._profundidade_max = profundidade_max
        self._n_alternativas = n_alternativas

    def raciocinar(self, pergunta: str,
                   contexto: str = "") -> Tuple[Optional[str], float]:
        """Raciocina sobre uma pergunta em múltiplas etapas.

        Chain-of-thought markoviano:
        1. Decompõe pergunta em sub-perguntas
        2. Resolve cada uma em sequência, propagando contexto
        3. Combina respostas via compor()
        4. Avalia cadeia com 5D

        Returns:
            (resposta_final, confianca_5d)
        """
        sub_perguntas = self._decompor(pergunta)
        if not sub_perguntas:
            sub_perguntas = [pergunta]

        respostas: List[Tuple[str, float]] = []
        contexto_acum = contexto

        for i, sub_p in enumerate(sub_perguntas):
            estado = f"{sub_p} {contexto_acum}".strip()
            pred, conf = self._coupling.decidir(estado, (None, 0.0))

            if not pred or conf < 0.3:
                alt = self._explorar_alternativas(estado)
                if alt:
                    pred, conf = alt

            if pred:
                respostas.append((pred, conf))
                contexto_acum = f"{contexto_acum} {pred}".strip()

            if len(respostas) >= self._profundidade_max:
                break

        if not respostas:
            return self._coupling.decidir(pergunta, (None, 0.0))

        resposta_final = respostas[-1][0]
        nota_5d = self._avaliar_cadeia(pergunta, respostas)

        return resposta_final, nota_5d

    def _decompor(self, pergunta: str) -> List[str]:
        """Decompõe pergunta em sub-perguntas.

        Heurística markoviana: separa por conectivos lógicos
        e marcadores de sequência. Zero hardcoded de domínio.
        """
        pergunta = pergunta.lower().strip()

        conectores = [
            r'\be\b', r'\boutro\b', r'\bdepois\b', r'\bentao\b',
            r'\blogo\b', r'\bportanto\b', r'\balem\b',
            r'\btambem\b', r'\bmas\b', r'\bporem\b',
        ]

        partes = [pergunta]
        for con in conectores:
            novas = []
            for p in partes:
                split = re.split(con, p)
                novas.extend(split)
            partes = novas

        sub_perguntas = [p.strip() for p in partes
                         if p.strip() and len(p.strip()) > 3]

        return sub_perguntas if len(sub_perguntas) > 1 else []

    def _explorar_alternativas(self, estado: str) -> Optional[Tuple[str, float]]:
        """Explora caminhos alternativos quando confiança é baixa.

        Usa fecho transitivo para encontrar respostas indiretas.
        """
        d_trn = self._coupling._dist_transitivo(estado, passos=3)
        if d_trn:
            melhor = max(d_trn, key=d_trn.get)
            if d_trn[melhor] > 0.3:
                return melhor, d_trn[melhor]

        d_palavras = self._coupling._dist_palavras(estado)
        if d_palavras:
            ordenado = sorted(d_palavras.items(), key=lambda x: -x[1])
            if len(ordenado) > 1:
                return ordenado[1][0], ordenado[1][1]

        return None

    def _avaliar_cadeia(self, pergunta: str,
                        respostas: List[Tuple[str, float]]) -> float:
        """Avalia a qualidade da cadeia de raciocínio com 5D.

        CERTEZA: confiança média das respostas
        COMPLETUDE: fração de sub-perguntas respondidas
        INFORMACAO: entropia da cadeia (diversidade de respostas)
        ESTABILIDADE: pune cadeia repetitiva (loop) ou caótica
        EFICIENCIA: 1/log2(n_passos+1) — recompensa caminhos curtos
        """
        try:
            from mcr.equacao_mcr import avaliar_5d
        except ImportError:
            from equacao_mcr import avaliar_5d

        if not respostas:
            return 0.0

        certeza = sum(c for _, c in respostas) / len(respostas)

        completude = len(respostas) / max(len(self._decompor(pergunta)), 1)
        completude = min(1.0, completude)

        counter = defaultdict(int)
        for r, _ in respostas:
            counter[r] += 1
        total = len(respostas)
        h = 0.0
        for c in counter.values():
            p = c / total
            if p > 0:
                h -= p * math.log2(p)
        max_h = math.log2(max(len(counter), 2))
        informacao = h / max_h if max_h > 0 else 0.0

        estabilidade = math.exp(-((informacao - 0.5) ** 2) / (2 * 0.15 ** 2))

        n_passos = len(respostas)
        eficiencia = 1.0 / math.log2(max(n_passos + 1, 2))

        return avaliar_5d(certeza, completude, informacao,
                          estabilidade, eficiencia)

    def silogismo(self, premissa_a: str, premissa_b: str,
                  ) -> Tuple[Optional[str], float]:
        """Raciocínio silogístico: Se A>B e B>C, então A>C.

        Usa fecho transitivo para conectar premissas.
        Pilar 7: correlação universal em múltiplos passos.
        """
        contexto = f"{premissa_a} {premissa_b}"
        return self.raciocinar(premissa_b, contexto=contexto)