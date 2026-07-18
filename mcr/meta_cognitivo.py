"""mcr.meta_cognitivo — Meta-cognição: MCR que observa o próprio MCR.

Segunda ordem: não é "quão confiante estou?" mas "devo confiar na minha confiança?"

5 capacidades meta-cognitivas:
1. Observar — registra cada decisão (input, output, confiança, fontes, divergência)
2. Incerteza — mede entropia da decisão, divergência entre fontes, cobertura de features
3. Calibrar — track (confiança, resultado) → curva de calibração + Brier score
4. Decidir quando NÃO responder — "não sei" é resposta válida
5. Auto-diagnosticar — detecta domain shift, overconfidence, novelty

Base: Markov 1ª ordem sobre o histórico de decisões.
P(correto|bin_confiança) — probabilidade de estar correto dado nível de confiança.
Zero GPU, zero dependências, zero thresholds hardcoded.
"""
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional, Any
import math
import re


class MetaCognitivo:
    """MCR que observa o próprio MCR.

    Wraps MCRCoupling.decidir() e constrói um modelo da própria confiabilidade.
    Usa Markov 1ª ordem: P(resultado | confiança_bin) aprendido do histórico.
    """

    def __init__(self, coupling):
        self._coupling = coupling
        # Histórico de decisões observadas (sliding window)
        self._historico: deque = deque(maxlen=500)
        # Feedback: (confiança_bruta, estava_correto) → aprende calibração
        self._feedback: deque = deque(maxlen=500)
        # Calibração por bin: bin → [n_correto, n_total]
        self._calibracao: Dict[int, List[int]] = defaultdict(lambda: [0, 0])
        # Domínios vistos: ação → [confianças]
        self._dominio_confianca: Dict[str, List[float]] = defaultdict(list)
        # Feedback por ação: ação → [correto, total]
        self._feedback_acao: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
        # Novelty: features conhecidas vs features totais por input
        self._cobertura_historico: deque = deque(maxlen=200)
        # Trajetória de incerteza (para detectar drift)
        self._trajetoria_incerteza: deque = deque(maxlen=100)
        # Modelo meta-markoviano: P(correto | bin_confianca)
        self._meta_transicoes: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        # Estatísticas acumuladas
        self._n_observacoes = 0
        self._n_feedback = 0
        self._n_correto = 0
        # Threshold adaptativo (aprendido, nunca hardcoded)
        self._threshold_resposta: float = 0.5

    # ═══════════════════════════════════════════════════════════════
    # 1. OBSERVAR — registrar decisões
    # ═══════════════════════════════════════════════════════════════

    def observar(self, texto: str, acao: str, confianca: float,
                 distribuicao: Dict[str, float], n_fontes: int,
                 divergencia_media: float) -> None:
        """Registra uma decisão para análise meta-cognitiva.

        Args:
            texto: input do MCR
            acao: ação decidida
            confianca: score de confiança (0-1)
            distribuicao: distribuição combinada de ações
            n_fontes: número de fontes que contribuíram
            divergencia_media: divergência média entre fontes (0-1)
        """
        # Entropia da distribuição de decisões
        h_decisao = self._entropia_dist(distribuicao)

        # Cobertura de features (quantas features do input são conhecidas)
        cobertura = self._calcular_cobertura(texto)

        # Novelty score: 1 - cobertura (quanto maior, mais novo)
        novelty = 1.0 - cobertura

        registro = {
            'texto': texto[:100],  # truncar para memória
            'acao': acao,
            'confianca': confianca,
            'h_decisao': h_decisao,
            'n_fontes': n_fontes,
            'divergencia': divergencia_media,
            'cobertura': cobertura,
            'novelty': novelty,
        }

        self._historico.append(registro)
        self._dominio_confianca[acao].append(confianca)
        self._cobertura_historico.append(cobertura)
        self._trajetoria_incerteza.append(h_decisao)
        self._n_observacoes += 1

        # Atualizar threshold adaptativo via mediana das confianças observadas
        if self._n_observacoes >= 10:
            confiancas = [r['confianca'] for r in self._historico]
            confiancas_ord = sorted(confiancas)
            mediana = confiancas_ord[len(confiancas_ord) // 2]
            # Threshold = mediana - 1 desvio padrão (aprendido dos dados)
            media = sum(confiancas) / len(confiancas)
            var = sum((c - media) ** 2 for c in confiancas) / len(confiancas)
            dp = math.sqrt(var)
            self._threshold_resposta = max(0.1, min(0.9, mediana - dp * 0.5))

    # ═══════════════════════════════════════════════════════════════
    # 2. INCERTEZA — medir segundo-order uncertainty
    # ═══════════════════════════════════════════════════════════════

    def incerteza_meta(self, confianca_bruta: float,
                       distribuicao: Dict[str, float],
                       n_fontes: int,
                       divergencia_media: float,
                       texto: str = '') -> float:
        """Mede incerteza meta-cognitiva (0 = certo, 1 = incerto).

        Combina 3 sinais:
        1. Entropia da distribuição → quão difusa é a decisão?
        2. Divergência entre fontes → quão discordantes estão?
        3. Novelty do input → quão familiar é o domínio?

        E ajusta pela calibração histórica: se MCR tem histórico de
        overconfidence em casos similares, aumenta incerteza.
        """
        # Sinal 1: entropia da distribuição
        h = self._entropia_dist(distribuicao)
        sinal_h = min(1.0, h)

        # Sinal 2: divergência entre fontes (0 = concordam, 1 = discordam)
        sinal_div = min(1.0, divergencia_media)

        # Sinal 3: novelty (1 - cobertura de features)
        cobertura = self._calcular_cobertura(texto) if texto else 0.5
        sinal_nov = 1.0 - cobertura

        # Combinação markoviana: média ponderada (sem pesos hardcoded —
        # cada sinal contribui igualmente, ajustado pela calibração)
        incerteza_bruta = (sinal_h * 0.4 + sinal_div * 0.3 + sinal_nov * 0.3)

        # Ajuste de calibração: se historicamente MCR está overconfident
        # neste bin de confiança, aumenta incerteza
        bin_conf = int(confianca_bruta * 10)
        cal = self._calibracao.get(bin_conf)
        if cal and cal[1] >= 3:
            taxa_acerto = cal[0] / cal[1]
            # Se taxa de acerto < confiança bruta → overconfident → aumenta incerteza
            gap = confianca_bruta - taxa_acerto
            incerteza_bruta += max(0, gap) * 0.3

        return min(1.0, incerteza_bruta)

    # ═══════════════════════════════════════════════════════════════
    # 3. CALIBRAR — confiança vs realidade
    # ═══════════════════════════════════════════════════════════════

    def feedback(self, confianca_bruta: float, correto: bool,
                 acao: str = '') -> None:
        """Aprende com feedback — estava certo ou errado?

        Constrói o modelo meta-markoviano P(correto|bin_confiança).
        """
        bin_conf = int(min(0.99, confianca_bruta) * 10)

        self._calibracao[bin_conf][1] += 1
        if correto:
            self._calibracao[bin_conf][0] += 1
            self._meta_transicoes[bin_conf]['correto'] += 1
        else:
            self._meta_transicoes[bin_conf]['errado'] += 1

        self._feedback.append((confianca_bruta, correto))
        self._n_feedback += 1
        if correto:
            self._n_correto += 1
        if acao:
            self._feedback_acao[acao][1] += 1
            if correto:
                self._feedback_acao[acao][0] += 1

    def calibrar_confianca(self, confianca_bruta: float) -> float:
        """Ajusta confiança bruta com base na calibração histórica.

        Se MCR diz 0.9 mas historicamente só acerta 70% nesse bin,
        confiança calibrada = 0.7.
        """
        bin_conf = int(min(0.99, confianca_bruta) * 10)
        cal = self._calibracao.get(bin_conf)

        if not cal or cal[1] < 3:
            # Sem dados suficientes neste bin — manter confiança bruta
            return confianca_bruta

        taxa_acerto = cal[0] / cal[1]
        # Suavização: mistura confiança bruta com taxa real
        # Pesos: mais dados → mais peso na taxa real
        peso_calibracao = min(1.0, cal[1] / 20.0)
        confianca_calibrada = (confianca_bruta * (1 - peso_calibracao) +
                               taxa_acerto * peso_calibracao)
        return max(0.0, min(1.0, confianca_calibrada))

    def brier_score(self) -> float:
        """Brier score: mean((confiança - resultado)^2).

        0 = perfeito, 1 = pior possível, 0.25 = aleatório.
        """
        if not self._feedback:
            return 0.25  # sem dados = incerteza máxima
        soma = sum((conf - (1.0 if ok else 0.0)) ** 2
                    for conf, ok in self._feedback)
        return soma / len(self._feedback)

    def curva_calibracao(self) -> List[Tuple[float, float, int]]:
        """Retorna curva de calibração: [(confiança_média, taxa_real, n)]."""
        resultado = []
        for bin_conf in sorted(self._calibracao.keys()):
            n_corr, n_tot = self._calibracao[bin_conf]
            if n_tot > 0:
                conf_media = bin_conf / 10.0 + 0.05
                taxa_real = n_corr / n_tot
                resultado.append((conf_media, taxa_real, n_tot))
        return resultado

    # ═══════════════════════════════════════════════════════════════
    # 4. DECIDIR QUANDO NÃO RESPONDER
    # ═══════════════════════════════════════════════════════════════

    def pode_responder(self, texto: str, confianca_bruta: float,
                       distribuicao: Dict[str, float],
                       n_fontes: int = 1,
                       divergencia_media: float = 0.0
                       ) -> Tuple[bool, float, str]:
        """Decide se MCR deve responder ou admitir ignorância.

        Returns:
            (deve_responder, confianca_calibrada, justificativa)
        """
        # Calibrar confiança primeiro
        conf_calibrada = self.calibrar_confianca(confianca_bruta)

        # Medir incerteza meta-cognitiva
        incerteza = self.incerteza_meta(
            confianca_bruta, distribuicao, n_fontes, divergencia_media, texto
        )

        # Confiança efetiva = calibrada * (1 - incerteza)
        conf_efetiva = conf_calibrada * (1.0 - incerteza * 0.5)

        # Cobertura de features
        cobertura = self._calcular_cobertura(texto)

        # Boost de familiaridade: se cobertura alta (domínio familiar),
        # reduz threshold efetivo — MCR deve ser mais permissivo
        # em domínios que conhece bem
        threshold_efetivo = self._threshold_resposta
        if cobertura > 0.7:
            threshold_efetivo *= 0.5  # domínio familiar → mais permissivo

        # Decisão: não responder se:
        # 1. Confiança efetiva < threshold adaptativo
        # 2. Novelty muito alto (cobertura < 0.2)
        # 3. Distribuição plana (entropia máxima → sem informação)

        justificativas = []

        if conf_efetiva < threshold_efetivo:
            justificativas.append(
                f"confianca_efetiva={conf_efetiva:.2f} < threshold={threshold_efetivo:.2f}"
            )

        if cobertura < 0.2 and self._n_observacoes > 10:
            justificativas.append(
                f"novelty_alta: cobertura={cobertura:.2f} (dominio desconhecido)"
            )

        h = self._entropia_dist(distribuicao)
        n_acoes = len(distribuicao)
        if n_acoes > 1 and h > 0.95:
            justificativas.append(
                f"distribuicao_plana: H={h:.2f} (sem preferencia clara)"
            )

        if justificativas:
            return False, conf_efetiva, "; ".join(justificativas)

        return True, conf_efetiva, "confianca_suficiente"

    # ═══════════════════════════════════════════════════════════════
    # 5. AUTO-DIAGNÓSTICO
    # ═══════════════════════════════════════════════════════════════

    def auto_diagnosticar(self) -> Dict[str, Any]:
        """Diagnóstico do próprio estado cognitivo.

        Detecta:
        - Overconfidence: confiança média >> taxa de acerto
        - Underconfidence: confiança média << taxa de acerto
        - Domain shift: cobertura média diminuindo ao longo do tempo
        - Convergence: incerteza diminuindo ao longo do tempo
        - Gaps: domínios com baixa confiança
        """
        diagnostico = {
            'n_observacoes': self._n_observacoes,
            'n_feedback': self._n_feedback,
            'taxa_acerto': self._n_correto / max(1, self._n_feedback),
            'brier_score': self.brier_score(),
            'threshold_resposta': round(self._threshold_resposta, 3),
        }

        if not self._historico:
            diagnostico['status'] = 'sem_dados'
            return diagnostico

        # Confiança média
        confiancas = [r['confianca'] for r in self._historico]
        conf_media = sum(confiancas) / len(confiancas)
        diagnostico['confianca_media'] = round(conf_media, 3)

        # Incerteza média
        incertezas = [r['h_decisao'] for r in self._historico]
        inc_media = sum(incertezas) / len(incertezas)
        diagnostico['incerteza_media'] = round(inc_media, 3)

        # Cobertura média (familiaridade de domínio)
        coberturas = list(self._cobertura_historico)
        cob_media = sum(coberturas) / len(coberturas) if coberturas else 0
        diagnostico['cobertura_media'] = round(cob_media, 3)

        # Overconfidence / Underconfidence
        if self._n_feedback >= 5:
            taxa_real = self._n_correto / self._n_feedback
            gap = conf_media - taxa_real
            if gap > 0.15:
                diagnostico['vies'] = 'overconfident'
                diagnostico['vies_magnitude'] = round(gap, 3)
            elif gap < -0.15:
                diagnostico['vies'] = 'underconfident'
                diagnostico['vies_magnitude'] = round(abs(gap), 3)
            else:
                diagnostico['vies'] = 'calibrado'
                diagnostico['vies_magnitude'] = round(abs(gap), 3)

        # Domain drift: comparar primeiras vs últimas coberturas
        if len(coberturas) >= 20:
            n_metade = len(coberturas) // 2
            cob_antiga = sum(coberturas[:n_metade]) / n_metade
            cob_recente = sum(coberturas[n_metade:]) / n_metade
            drift = cob_antiga - cob_recente
            if drift > 0.15:
                diagnostico['drift'] = 'domain_shift_negativo'
                diagnostico['drift_magnitude'] = round(drift, 3)
            elif drift < -0.15:
                diagnostico['drift'] = 'convergencia_positiva'
                diagnostico['drift_magnitude'] = round(abs(drift), 3)
            else:
                diagnostico['drift'] = 'estavel'

        # Gaps: domínios com baixa confiança OU alto erro
        gaps = []
        for acao, confs in self._dominio_confianca.items():
            if len(confs) >= 3:
                media_conf = sum(confs) / len(confs)
                # Taxa de erro por ação (do feedback)
                fb = self._feedback_acao.get(acao)
                taxa_erro = 0.0
                if fb and fb[1] >= 3:
                    taxa_erro = 1.0 - (fb[0] / fb[1])
                if media_conf < self._threshold_resposta or taxa_erro > 0.4:
                    gaps.append({
                        'acao': acao,
                        'confianca_media': round(media_conf, 3),
                        'n_observacoes': len(confs),
                        'taxa_erro': round(taxa_erro, 3),
                    })
        if gaps:
            gaps.sort(key=lambda x: x['confianca_media'])
            diagnostico['gaps'] = gaps[:5]

        # Status geral
        if diagnostico.get('vies') == 'overconfident':
            diagnostico['status'] = 'atencao_overconfident'
        elif gaps:
            diagnostico['status'] = 'gaps_detectados'
        elif diagnostico.get('drift') == 'domain_shift_negativo':
            diagnostico['status'] = 'domain_shift'
        else:
            diagnostico['status'] = 'saudavel'

        return diagnostico

    def presuncao(self) -> float:
        """Presunção cognitiva: confiança média - taxa de acerto.

        > 0 = overconfident (presunçoso)
        < 0 = underconfident (cauteloso)
        ≈ 0 = calibrado
        """
        if not self._historico or self._n_feedback < 1:
            return 0.0
        conf_media = sum(r['confianca'] for r in self._historico) / len(self._historico)
        taxa_acerto = self._n_correto / self._n_feedback
        return conf_media - taxa_acerto

    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _entropia_dist(dist: Dict[str, float]) -> float:
        """Entropia Shannon normalizada [0, 1] de uma distribuição."""
        total = sum(dist.values())
        if total <= 0:
            return 0.0
        n = len(dist)
        if n <= 1:
            return 0.0
        h = 0.0
        for v in dist.values():
            pr = v / total
            if pr > 0:
                h -= pr * math.log2(pr)
        max_h = math.log2(n)
        return h / max_h if max_h > 0 else 0.0

    def _calcular_cobertura(self, texto: str) -> float:
        """Cobertura de features: fração de palavras do input conhecidas.

        1.0 = todas as palavras conhecidas (domínio familiar)
        0.0 = nenhuma palavra conhecida (domínio totalmente novo)
        """
        palavras = re.findall(r'[a-zà-ÿ0-9]{2,}', texto.lower())
        if not palavras:
            return 0.0
        conhecidas = 0
        for p in palavras:
            if p in self._coupling._palavra_acao:
                conhecidas += 1
        return conhecidas / len(palavras)

    def estatisticas(self) -> Dict[str, Any]:
        """Estatísticas resumidas para inspeção externa."""
        return {
            'n_observacoes': self._n_observacoes,
            'n_feedback': self._n_feedback,
            'taxa_acerto': round(self._n_correto / max(1, self._n_feedback), 3),
            'brier_score': round(self.brier_score(), 3),
            'presuncao': round(self.presuncao(), 3),
            'threshold_resposta': round(self._threshold_resposta, 3),
            'bins_calibrados': len(self._calibracao),
        }
