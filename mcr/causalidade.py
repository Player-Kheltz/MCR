"""mcr.causalidade — Distinguir correlacao de causalidade.

O MCR ja calcula P(B|A) (correlacao markoviana). Mas correlacao nao
implica causalidade. Este modulo implementa do-calculus de Pearl:

P(B|do(A)) = intervir em A (remover confounders)
P(B|A)     = observar A (confounders podem enviesar)

Se P(B|do(A)) != P(B|A), ha confounding.
Se P(B|do(A)) = P(B|A), A causa B diretamente (sem confounder).

5 capacidades:
1. Confounders — identificar variaveis C que afetam A e B simultaneamente
2. Intervir (do) — P(B|do(A)) = soma sobre confounders P(B|A,C) * P(C)
3. Cadeia causal — A->B->C: P(C|do(A)) via propagacao
4. d-separacao — A e B sao independentes dado C?
5. Efeito causal — magnitude da diferenca P(B|do(A)) - P(B|A)

Tudo Markov + entropia. Zero GPU, zero dependencias.
Base: Pearl, J. (2009) Causality: Models, Reasoning, and Inference.
"""
import math
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Optional, Any


class Causalidade:
    """Inferencia causal sobre o modelo markoviano do MCR.

    O coupling ja tem P(acao|palavra) e P(palavra_b|palavra_a).
    Este modulo usa essas transicoes para:
    - identificar confounders (palavras que predizem tanto A quanto B)
    - calcular P(B|do(A)) via backdoor adjustment
    - detectar cadeias causais A->B->C
    - verificar d-separacao

    Uso:
        causal = Causalidade(coupling)
        confounders = causal.identificar_confounders("criar", "monstro")
        efeito = causal.efeito_causal("criar", "monstro")
    """

    def __init__(self, coupling):
        self._coupling = coupling
        # Cache de confounders
        self._cache_confounders: Dict[Tuple[str, str], List[str]] = {}

    # ═══════════════════════════════════════════════════════════════
    # 1. CONFOUNDERS — variaveis que afetam A e B
    # ═══════════════════════════════════════════════════════════════

    def identificar_confounders(self, a: str, b: str) -> List[Dict[str, float]]:
        """Identifica confounders de A e B.

        Um confounder C e uma variavel que:
        1. Prediz A: P(A|C) > P(A)  (C -> A)
        2. Prediz B: P(B|C) > P(B)  (C -> B)

        Se C prediz ambos, a correlacao P(B|A) pode ser espuria:
        nao e A que causa B, e C que causa ambos.

        Returns:
            Lista de {confounder, p_a_dado_c, p_b_dado_c, forca} ordenada por forca.
        """
        cache_key = (a, b)
        if cache_key in self._cache_confounders:
            return self._cache_confounders[cache_key]

        # P(A) e P(B) marginais (frequencia relativa no vocabulario)
        p_a = self._prob_marginal(a)
        p_b = self._prob_marginal(b)

        if p_a == 0 or p_b == 0:
            self._cache_confounders[cache_key] = []
            return []

        confounders = []

        # Para cada palavra C no vocabulario, verificar se prediz A e B
        for c in self._coupling._palavra_acao:
            if c == a or c == b:
                continue

            # P(A|C): A aparece apos C?
            p_a_dado_c = self._prob_condicional(a, c)
            # P(B|C): B aparece apos C?
            p_b_dado_c = self._prob_condicional(b, c)

            if p_a_dado_c == 0 or p_b_dado_c == 0:
                continue

            # Forca do confounder: quanto P(A|C) e P(B|C) excedem P(A) e P(B)
            lift_a = p_a_dado_c / p_a if p_a > 0 else 0
            lift_b = p_b_dado_c / p_b if p_b > 0 else 0

            # Confounder se ambos lifts > 1 (C aumenta prob de A E B)
            if lift_a > 1.0 and lift_b > 1.0:
                forca = min(lift_a, lift_b)  # limitado pelo menor lift
                confounders.append({
                    'confounder': c,
                    'p_a_dado_c': round(p_a_dado_c, 4),
                    'p_b_dado_c': round(p_b_dado_c, 4),
                    'lift_a': round(lift_a, 4),
                    'lift_b': round(lift_b, 4),
                    'forca': round(forca, 4),
                })

        confounders.sort(key=lambda x: -x['forca'])
        self._cache_confounders[cache_key] = confounders
        return confounders

    # ═══════════════════════════════════════════════════════════════
    # 2. INTERVIR (do) — P(B|do(A)) via backdoor adjustment
    # ═══════════════════════════════════════════════════════════════

    def intervir(self, a: str, b: str) -> float:
        """Calcula P(B|do(A)) via backdoor adjustment.

        Pearl's backdoor: P(B|do(A)) = soma_C P(B|A,C) * P(C)
        onde C sao os confounders.

        Se nao ha confounders, P(B|do(A)) = P(B|A).

        Returns:
            P(B|do(A)) no range [0, 1].
        """
        confounders = self.identificar_confounders(a, b)

        if not confounders:
            # Sem confounders: P(B|do(A)) = P(B|A)
            return self._prob_condicional(b, a)

        # Backdoor adjustment: soma sobre confounders
        # P(B|do(A)) = soma_C P(B|A,C) * P(C)
        # Aproximacao: P(B|A,C) ~ P(B|A) * P(B|C) / P(B)  (assumindo independencia condicional)
        # Simplificacao markoviana: media ponderada de P(B|A) e P(B|C)
        p_b_dado_a = self._prob_condicional(b, a)
        p_b = self._prob_marginal(b)

        if p_b == 0:
            return p_b_dado_a

        soma = 0.0
        soma_peso = 0.0

        for conf in confounders[:5]:  # top 5 confounders
            c = conf['confounder']
            p_c = self._prob_marginal(c)
            p_b_dado_c = conf['p_b_dado_c']

            # P(B|A,C) aproximado por multiplicacao normalizada
            # (assumindo C e A independentes dado B)
            p_b_dado_ac = (p_b_dado_a * p_b_dado_c) / p_b if p_b > 0 else 0
            p_b_dado_ac = min(1.0, p_b_dado_ac)

            soma += p_b_dado_ac * p_c
            soma_peso += p_c

        if soma_peso == 0:
            return p_b_dado_a

        return soma / soma_peso

    # ═══════════════════════════════════════════════════════════════
    # 3. EFEITO CAUSAL — magnitude do confounding
    # ═══════════════════════════════════════════════════════════════

    def efeito_causal(self, a: str, b: str) -> Dict[str, float]:
        """Compara P(B|A) (correlacao) com P(B|do(A)) (causalidade).

        Returns:
            dict com:
            - p_b_dado_a: P(B|A) — correlacao observacional
            - p_b_dado_do_a: P(B|do(A)) — efeito causal
            - diferenca: |P(B|do(A)) - P(B|A)| — magnitude do confounding
            - tipo: 'causal' (diff ~0), 'espurio' (diff alta), 'confundido' (diff media)
        """
        p_obs = self._prob_condicional(b, a)
        p_causal = self.intervir(a, b)
        diff = abs(p_causal - p_obs)

        if diff < 0.05:
            tipo = 'causal'  # P(B|A) ~ P(B|do(A)) -> A causa B
        elif diff < 0.20:
            tipo = 'confundido'  # parcialmente confundido
        else:
            tipo = 'espurio'  # alta diferenca -> correlacao espuria

        return {
            'p_b_dado_a': round(p_obs, 4),
            'p_b_dado_do_a': round(p_causal, 4),
            'diferenca': round(diff, 4),
            'tipo': tipo,
        }

    # ═══════════════════════════════════════════════════════════════
    # 4. CADEIA CAUSAL — A -> B -> C
    # ═══════════════════════════════════════════════════════════════

    def cadeia_causal(self, a: str, b: str, c: str) -> Dict[str, Any]:
        """Verifica se A -> B -> C forma uma cadeia causal.

        Em uma cadeia: P(C|do(A)) = soma_B P(C|B) * P(B|do(A))
        Se B media o efeito de A sobre C.

        Returns:
            dict com 'e_a_c', 'e_a_c_direto', 'mediado_por_b', 'e_cadeia'
        """
        # Efeito total de A sobre C
        e_ac = self.efeito_causal(a, c)
        # Efeito de A sobre B
        e_ab = self.efeito_causal(a, b)
        # Efeito de B sobre C
        e_bc = self.efeito_causal(b, c)

        # Efeito mediado: P(C|do(A)) via B
        p_b_do_a = e_ab['p_b_dado_do_a']
        p_c_dado_b = e_bc['p_b_dado_a']  # P(C|B)
        e_mediado = p_b_do_a * p_c_dado_b

        # Efeito direto (sem B)
        e_direto = e_ac['p_b_dado_do_a']

        # Se e_mediado ~ e_direto, B media todo o efeito (cadeia pura)
        ratio = e_mediado / max(e_direto, 0.001)
        e_cadeia = 0.7 < ratio < 1.3 and e_direto > 0.05

        return {
            'a': a, 'b': b, 'c': c,
            'e_a_sobre_b': e_ab,
            'e_b_sobre_c': e_bc,
            'e_a_sobre_c': e_ac,
            'e_mediado': round(e_mediado, 4),
            'e_direto': round(e_direto, 4),
            'ratio_mediacao': round(ratio, 4),
            'e_cadeia': e_cadeia,
        }

    # ═══════════════════════════════════════════════════════════════
    # 5. d-SEPARACAO — A e B independentes dado C?
    # ═══════════════════════════════════════════════════════════════

    def d_separacao(self, a: str, b: str, c: str) -> Dict[str, Any]:
        """Verifica se A e B sao d-separados dado C.

        d-separacao: toda caminho de A a B e bloqueado por C.
        Em markoviano: se P(B|A,C) = P(B|C), entao A e B sao
        independentes dado C (C bloqueia o caminho).

        Returns:
            dict com 'independentes', 'p_b_dado_a_c', 'p_b_dado_c', 'diferenca'
        """
        p_b_dado_c = self._prob_condicional(b, c)
        p_b_dado_ac = self._prob_condicional_conjunta(b, a, c)

        diff = abs(p_b_dado_ac - p_b_dado_c)

        # d-separados se a diferenca for pequena (< 0.05)
        independentes = diff < 0.05

        return {
            'a': a, 'b': b, 'c': c,
            'p_b_dado_c': round(p_b_dado_c, 4),
            'p_b_dado_a_c': round(p_b_dado_ac, 4),
            'diferenca': round(diff, 4),
            'independentes': independentes,
        }

    # ═══════════════════════════════════════════════════════════════
    # HELPERS — probabilidades a partir do coupling
    # ═══════════════════════════════════════════════════════════════

    def _prob_marginal(self, palavra: str) -> float:
        """P(palavra) = frequencia relativa no vocabulario."""
        total_vocab = sum(
            sum(dist.values()) for dist in self._coupling._palavra_acao.values()
        )
        if total_vocab == 0:
            return 0.0
        dist = self._coupling._palavra_acao.get(palavra, {})
        return sum(dist.values()) / total_vocab

    def _prob_condicional(self, b: str, a: str) -> float:
        """P(B|A) = frequencia de B apos A / frequencia total apos A.

        Usa _transicao_palavra: P(palavra_b | palavra_a).
        """
        vizinhos = self._coupling._transicao_palavra.get(a, {})
        total = sum(vizinhos.values())
        if total == 0:
            # Fallback: co-ocorrencia via _palavra_acao
            dist_a = self._coupling._palavra_acao.get(a, {})
            dist_b = self._coupling._palavra_acao.get(b, {})
            # Se compartilham acoes, ha correlacao
            acoes_comuns = set(dist_a.keys()) & set(dist_b.keys())
            if acoes_comuns and dist_a and dist_b:
                total_a = sum(dist_a.values())
                total_b = sum(dist_b.values())
                overlap = sum(min(dist_a[ac], dist_b[ac]) for ac in acoes_comuns)
                return overlap / max(total_a, total_b)
            return 0.0
        return vizinhos.get(b, 0) / total

    def _prob_condicional_conjunta(self, b: str, a: str, c: str) -> float:
        """P(B|A,C) aproximado.

        Aproximacao markoviana: P(B|A,C) ~ P(B|A) * P(B|C) / P(B)
        (assumindo A e C independentes dado B).
        """
        p_b_dado_a = self._prob_condicional(b, a)
        p_b_dado_c = self._prob_condicional(b, c)
        p_b = self._prob_marginal(b)

        if p_b == 0:
            return max(p_b_dado_a, p_b_dado_c)

        # Multiplicacao normalizada (noisy-OR)
        p_conj = (p_b_dado_a * p_b_dado_c) / p_b
        return min(1.0, p_conj)

    # ═══════════════════════════════════════════════════════════════
    # ESTATISTICAS
    # ═══════════════════════════════════════════════════════════════

    def estatisticas(self) -> Dict[str, Any]:
        """Estatisticas do modulo de causalidade."""
        return {
            'cache_confounders': len(self._cache_confounders),
            'vocabulario': len(self._coupling._palavra_acao),
            'transicoes': len(self._coupling._transicao_palavra),
        }
