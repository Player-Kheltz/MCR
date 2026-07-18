"""mcr.contrafactual — Raciocínio contrafactual: "o que aconteceria se...?"

Terceiro degrau da Escada de Causalidade de Pearl:
1. Associação:     P(B|A)     — o que B me diz sobre A?
2. Intervenção:    P(B|do(A)) — o que acontece com B se eu fizer A?
3. Contrafactual:  P(B(a')|A=a, B=b) — o que B seria se A tivesse sido a'?

Implementa os 3 passos do contrafactual de Pearl:
1. Abdução:    dado que observamos A=a, B=b, quais confounders U eram
               provavelmente presentes? P(U|A=a, B=b)
2. Ação:       substituir A por a' (do(A=a'))
3. Predição:   P(B'|do(A=a'), U) — o que B seria com a' e os mesmos U?

5 capacidades:
1. Contrafactual:      "se A fosse a', qual seria B?"
2. Necessidade causal: "A foi necessário para B?" (sem A, B não aconteceria?)
3. Suficiência causal: "A foi suficiente para B?" (com A, B sempre acontece?)
4. Cenários hipotéticos: gerar e avaliar múltiplos contrafactuais
5. Propagação: contrafactual em cadeia (se A mudasse, como C mudaria via B?)

Tudo Markov + entropia. Zero GPU, zero dependências.
Base: Pearl, J. (2009) Causality — Capítulo 7: Counterfactuals.
"""
import math
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Optional, Any

from mcr.causalidade import Causalidade


class Contrafactual:
    """Raciocínio contrafactual sobre o modelo markoviano do MCR.

    Construído sobre Causalidade (FASE 13). Usa confounders para
    abdução, intervir() para ação, e _prob_condicional() para predição.

    Uso:
        contra = Contrafactual(coupling)
        resultado = contra.o_que_se("criar", "monstro", "editar")
        # "se 'criar' fosse 'editar', o que aconteceria com 'monstro'?"
    """

    def __init__(self, coupling):
        self._coupling = coupling
        self._causal = Causalidade(coupling)

    # ═══════════════════════════════════════════════════════════════
    # 1. CONTRAFACTUAL — "se A fosse a', qual seria B?"
    # ═══════════════════════════════════════════════════════════════

    def o_que_se(self, a_obs: str, b_obs: str,
                 a_counter: str) -> Dict[str, Any]:
        """Calcula contrafactual: se A fosse a', qual seria B?

        Passos de Pearl:
        1. Abdução: dados A=a_obs, B=b_obs, quais confounders mais prováveis?
        2. Ação: substituir A por a_counter
        3. Predição: P(B'|do(a_counter), confounders_abduzidos)

        Args:
            a_obs: valor observado de A (o que aconteceu)
            b_obs: valor observado de B (o que aconteceu)
            a_counter: valor contrafactual de A (o que teria acontecido)

        Returns:
            dict com:
            - p_b_original: P(B|A=a_obs) — o que foi observado
            - p_b_contrafactual: P(B|do(A=a_counter), U) — o que seria
            - delta: diferença (magnitude da mudança contrafactual)
            - confounders_abduzidos: top confounders mais prováveis
            - acao_mudou: True se B mudou significativamente
        """
        # Passo 1: Abdução — quais confounders eram mais prováveis
        # dado que observamos A=a_obs e B=b_obs?
        confounders = self._abducao(a_obs, b_obs)

        # Passo 2+3: Ação + Predição
        # P(B|do(a_counter), confounders_abduzidos)
        p_b_original = self._causal._prob_condicional(b_obs, a_obs)

        # Caso trivial: se a_counter == a_obs, contrafactual = observado
        if a_counter == a_obs:
            p_b_contrafactual = p_b_original
        else:
            p_b_contrafactual = self._predicao_contrafactual(
                a_counter, b_obs, confounders
            )

        delta = abs(p_b_contrafactual - p_b_original)
        acao_mudou = delta > 0.05

        return {
            'a_observado': a_obs,
            'b_observado': b_obs,
            'a_contrafactual': a_counter,
            'p_b_original': round(p_b_original, 4),
            'p_b_contrafactual': round(p_b_contrafactual, 4),
            'delta': round(delta, 4),
            'acao_mudou': acao_mudou,
            'confounders_abduzidos': confounders[:3],
            'interpretacao': self._interpretar(p_b_original, p_b_contrafactual,
                                                a_obs, a_counter, b_obs),
        }

    # ═══════════════════════════════════════════════════════════════
    # 2. NECESSIDADE CAUSAL — "A foi necessário para B?"
    # ═══════════════════════════════════════════════════════════════

    def necessidade_causal(self, a: str, b: str) -> Dict[str, Any]:
        """Verifica se A foi necessário para B.

        Necessidade: P(B não aconteceria sem A).
        Contrafactual: "se A não tivesse acontecido, B ainda aconteceria?"

        Se P(B|do(¬A)) << P(B|A), então A foi necessário.
        Se P(B|do(¬A)) ~ P(B|A), então A não foi necessário.

        Usa a alternativa mais provável a A (palavra que mais co-ocorre
        com confounders de A) como ¬A.
        """
        # Encontrar ¬A: alternativa mais provável
        alternativa = self._melhor_alternativa(a)

        if alternativa == a:
            return {
                'a': a, 'b': b,
                'alternativa': None,
                'necessario': False,
                'p_b_com_a': 0.0,
                'p_b_sem_a': 0.0,
                'interpretacao': 'sem alternativa para comparar',
            }

        cf = self.o_que_se(a, b, alternativa)
        p_b_com = cf['p_b_original']
        p_b_sem = cf['p_b_contrafactual']

        # A foi necessário se B diminui muito sem A
        necessario = (p_b_com - p_b_sem) > 0.1

        return {
            'a': a, 'b': b,
            'alternativa': alternativa,
            'p_b_com_a': round(p_b_com, 4),
            'p_b_sem_a': round(p_b_sem, 4),
            'reducao': round(p_b_com - p_b_sem, 4),
            'necessario': necessario,
            'interpretacao': (
                f"A='{a}' foi necessario para B='{b}': "
                f"sem A, P(B) cai de {p_b_com:.2f} para {p_b_sem:.2f}"
                if necessario else
                f"A='{a}' nao foi necessario: "
                f"P(B) se mantem ({p_b_com:.2f} -> {p_b_sem:.2f})"
            ),
        }

    # ═══════════════════════════════════════════════════════════════
    # 3. SUFICIÊNCIA CAUSAL — "A foi suficiente para B?"
    # ═══════════════════════════════════════════════════════════════

    def suficiencia_causal(self, a: str, b: str) -> Dict[str, Any]:
        """Verifica se A foi suficiente para B.

        Suficiência: P(B aconteceria com A, mesmo sem outros fatores).
        Contrafactual: "se apenas A estivesse presente (sem confounders),
        B ainda aconteceria?"

        Se P(B|do(A)) > threshold, A foi suficiente.
        Compara com P(B|A) (observacional) — se próximas, A é suficiente
        sem precisar de confounders.
        """
        efeito = self._causal.efeito_causal(a, b)
        p_obs = efeito['p_b_dado_a']
        p_do = efeito['p_b_dado_do_a']

        # A é suficiente se P(B|do(A)) é alto (mesmo sem confounders)
        suficiente = p_do > 0.3

        # Razão suficiência: quanto P(do) se aproxima de P(obs)
        razao = p_do / max(p_obs, 0.001)

        return {
            'a': a, 'b': b,
            'p_b_observacional': round(p_obs, 4),
            'p_b_intervencional': round(p_do, 4),
            'razao': round(razao, 4),
            'suficiente': suficiente,
            'interpretacao': (
                f"A='{a}' foi suficiente para B='{b}': "
                f"P(B|do(A))={p_do:.2f} > 0.3"
                if suficiente else
                f"A='{a}' nao foi suficiente: "
                f"P(B|do(A))={p_do:.2f} < 0.3 (precisa de confounders)"
            ),
        }

    # ═══════════════════════════════════════════════════════════════
    # 4. CENÁRIOS HIPOTÉTICOS — múltiplos contrafactuais
    # ═══════════════════════════════════════════════════════════════

    def cenarios(self, a_obs: str, b_obs: str,
                 alternativas: List[str]) -> List[Dict[str, Any]]:
        """Gera múltiplos cenários contrafactuais.

        "Se A fosse a1, qual seria B? E se fosse a2? E a3?"

        Returns:
            Lista de resultados o_que_se() para cada alternativa.
        """
        resultados = []
        for alt in alternativas:
            if alt == a_obs:
                continue
            cf = self.o_que_se(a_obs, b_obs, alt)
            resultados.append(cf)
        return resultados

    def melhor_cenario(self, a_obs: str, b_obs: str,
                       alternativas: List[str]) -> Dict[str, Any]:
        """Encontra a alternativa que maximizaria B.

        "Qual valor de A maximizaria P(B)?"
        """
        cenarios = self.cenarios(a_obs, b_obs, alternativas)
        if not cenarios:
            return {'erro': 'sem_alternativas'}
        melhor = max(cenarios, key=lambda x: x['p_b_contrafactual'])
        melhor['melhor_alternativa'] = True
        return melhor

    # ═══════════════════════════════════════════════════════════════
    # 5. PROPAGAÇÃO CONTRAFACTUAL EM CADEIA
    # ═══════════════════════════════════════════════════════════════

    def propagar_contrafactual(self, a_obs: str, b_obs: str,
                               c_obs: str, a_counter: str) -> Dict[str, Any]:
        """Propaga contrafactual em cadeia: A -> B -> C.

        "Se A tivesse sido a', como B mudaria? E como isso afetaria C?"

        Passos:
        1. Contrafactual de A sobre B: P(B'|do(a_counter))
        2. Contrafactual de B' sobre C: P(C'|do(B'))
        3. Compara C original vs C contrafactual
        """
        # Passo 1: A -> B contrafactual
        cf_ab = self.o_que_se(a_obs, b_obs, a_counter)
        b_contra = cf_ab['p_b_contrafactual']

        # Passo 2: B' -> C
        # P(C|B) original
        p_c_original = self._causal._prob_condicional(c_obs, b_obs)
        # P(C|B') contrafactual — precisamos de uma palavra alternativa para B
        # que tenha probabilidade ~ b_contra
        b_alt = self._encontrar_palavra_com_prob(b_obs, c_obs, b_contra)
        if b_alt:
            p_c_contra = self._causal._prob_condicional(c_obs, b_alt)
        else:
            # Aproximação: escalar P(C|B) pela razão de B
            p_c_contra = p_c_original * (b_contra / max(cf_ab['p_b_original'], 0.001))
            p_c_contra = min(1.0, p_c_contra)

        delta_c = abs(p_c_contra - p_c_original)

        return {
            'a_observado': a_obs,
            'b_observado': b_obs,
            'c_observado': c_obs,
            'a_contrafactual': a_counter,
            'b_contrafactual_prob': round(b_contra, 4),
            'c_original_prob': round(p_c_original, 4),
            'c_contrafactual_prob': round(p_c_contra, 4),
            'delta_b': round(cf_ab['delta'], 4),
            'delta_c': round(delta_c, 4),
            'propagou': delta_c > 0.05,
            'cf_a_b': cf_ab,
        }

    # ═══════════════════════════════════════════════════════════════
    # HELPERS — passos internos de Pearl
    # ═══════════════════════════════════════════════════════════════

    def _abducao(self, a: str, b: str) -> List[Dict[str, Any]]:
        """Passo 1 de Pearl: abdução de confounders.

        Dado que observamos A=a e B=b, quais confounders C eram
        mais provavelmente presentes?

        P(C|A,B) ~ P(A|C) * P(B|C) * P(C) / P(A,B)

        Como P(A,B) é constante, ordenamos por P(A|C) * P(B|C) * P(C).
        """
        confounders = self._causal.identificar_confounders(a, b)

        # Reordenar por probabilidade posterior (abdução)
        # P(C|A,B) ~ P(A|C) * P(B|C) * P(C)
        for cf in confounders:
            c = cf['confounder']
            p_c = self._causal._prob_marginal(c)
            # Posterior ~ likelihood_A * likelihood_B * prior_C
            posterior = cf['p_a_dado_c'] * cf['p_b_dado_c'] * p_c
            cf['posterior'] = round(posterior, 6)

        confounders.sort(key=lambda x: -x.get('posterior', 0))
        return confounders

    def _predicao_contrafactual(self, a_counter: str, b: str,
                                confounders: List[Dict[str, Any]]) -> float:
        """Passo 2+3 de Pearl: ação + predição.

        P(B|do(a_counter), confounders_abduzidos)

        Backdoor adjustment com confounders abduzidos:
        soma_C P(B|a_counter, C) * P(C|abducao)
        """
        if not confounders:
            # Sem confounders: P(B|do(a_counter)) = P(B|a_counter)
            return self._causal._prob_condicional(b, a_counter)

        p_b = self._causal._prob_marginal(b)
        if p_b == 0:
            return self._causal._prob_condicional(b, a_counter)

        soma = 0.0
        soma_peso = 0.0

        for conf in confounders[:5]:
            c = conf['confounder']
            p_c = self._causal._prob_marginal(c)

            # P(B|a_counter, C) ~ P(B|a_counter) * P(B|C) / P(B)
            p_b_dado_ac = self._causal._prob_condicional(b, a_counter)
            p_b_dado_c = conf.get('p_b_dado_c',
                                   self._causal._prob_condicional(b, c))
            p_conj = (p_b_dado_ac * p_b_dado_c) / p_b if p_b > 0 else 0
            p_conj = min(1.0, p_conj)

            # Peso = posterior abduzido
            peso = conf.get('posterior', p_c)
            soma += p_conj * peso
            soma_peso += peso

        if soma_peso == 0:
            return self._causal._prob_condicional(b, a_counter)

        return soma / soma_peso

    def _melhor_alternativa(self, a: str) -> str:
        """Encontra a melhor alternativa para A (¬A).

        A alternativa é a palavra que mais co-ocorre com os mesmos
        confounders de A, mas não é A.
        """
        # Encontrar palavras que transicionam para os mesmos contextos
        # que A (via _transicao_palavra inbound)
        candidatos = defaultdict(float)

        for palavra, viz in self._coupling._transicao_palavra.items():
            if palavra == a:
                continue
            # Se A aparece como destino de `palavra`, é uma alternativa
            if a in viz:
                candidatos[palavra] += viz[a]

        # Também: palavras na mesma posição que A
        for chave, dist in self._coupling._posicao_acao.items():
            if chave.startswith('P0:') and a in dist:
                for outra, count in dist.items():
                    if outra != a:
                        candidatos[outra] += count * 0.5

        if not candidatos:
            # Fallback: palavra mais similar via NMI
            sig_a = self._coupling._assinatura_palavra(a)
            if sig_a:
                for outra in self._coupling._palavra_acao:
                    if outra == a:
                        continue
                    sig_o = self._coupling._assinatura_palavra(outra)
                    if sig_o:
                        nmi = self._coupling._nmi(sig_a, sig_o)
                        if nmi > 0.2:
                            candidatos[outra] = nmi

        if not candidatos:
            return a

        return max(candidatos, key=candidatos.get)

    def _encontrar_palavra_com_prob(self, b: str, c: str,
                                     prob_alvo: float) -> Optional[str]:
        """Encontra palavra B' tal que P(C|B') ~ prob_alvo."""
        if prob_alvo <= 0:
            return None

        melhor_palavra = None
        melhor_diff = float('inf')

        for palavra in self._coupling._palavra_acao:
            if palavra == b:
                continue
            p_c = self._causal._prob_condicional(c, palavra)
            diff = abs(p_c - prob_alvo)
            if diff < melhor_diff:
                melhor_diff = diff
                melhor_palavra = palavra

        return melhor_palavra

    @staticmethod
    def _interpretar(p_orig: float, p_contra: float,
                     a_obs: str, a_counter: str, b: str) -> str:
        """Gera interpretação textual do contrafactual."""
        if p_contra > p_orig + 0.1:
            return (f"Se '{a_obs}' fosse '{a_counter}', "
                    f"P({b}) aumentaria ({p_orig:.2f} -> {p_contra:.2f})")
        elif p_contra < p_orig - 0.1:
            return (f"Se '{a_obs}' fosse '{a_counter}', "
                    f"P({b}) diminuiria ({p_orig:.2f} -> {p_contra:.2f})")
        else:
            return (f"Se '{a_obs}' fosse '{a_counter}', "
                    f"P({b}) nao mudaria ({p_orig:.2f} -> {p_contra:.2f})")

    # ═══════════════════════════════════════════════════════════════
    # ESTATÍSTICAS
    # ═══════════════════════════════════════════════════════════════

    def estatisticas(self) -> Dict[str, Any]:
        """Estatísticas do módulo contrafactual."""
        return {
            'causalidade': self._causal.estatisticas(),
            'vocabulario': len(self._coupling._palavra_acao),
        }
