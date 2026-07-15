"""MCRCoupling — Acoplamento multi-nível com superposição entrópica.

Princípios MCR:
  TUDO é P(b|a) — cada nível gera uma distribuição de probabilidade
  Entropia descobre estrutura — níveis mais certos (H baixa) pesam mais
  Mesmo motor — mesma lógica pra qualquer número de níveis
  Fecha o loop — aprende com cada decisão, Equação avalia

Superposição: combina N distribuições ponderadas por (1-H_normalizada).
  Sem ifs — apenas argmax sobre a distribuição final.
"""
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import re, math


class MCRCoupling:
    """Acoplamento multi-nível que aprende e combina sinais parciais.

    Níveis:
      palavra → ação   (tokens do input)
      cluster → ação   (Observer cluster)
      posição → ação   (estrutura do fingerprint)

    Superposição: argmax sobre soma ponderada das distribuições de cada nível,
    onde o peso de cada nível = (1 - entropia_normalizada).
    """

    def __init__(self):
        self._palavra_acao: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._cluster_acao: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._posicao_acao: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._total = 0
        self._freq_acao: Dict[str, int] = defaultdict(int)

    def alimentar(self, texto: str, acao: str):
        """Alimenta o coupling com uma observação."""
        self._total += 1
        acao = str(acao).replace('_lua', '')
        self._freq_acao[acao] += 1

        palavras = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        for p in set(palavras):
            self._palavra_acao[p][acao] += 1

        partes = texto.replace('_', ' ').split()
        for i, p in enumerate(partes[:6]):
            self._posicao_acao[f"P{i}:{p[:10]}"][acao] += 1

    def alimentar_lote(self, pares: list):
        """Alimenta coupling com lote de (texto, ação)."""
        for texto, acao in pares:
            self.alimentar(texto, acao)

    def alimentar_cluster(self, cluster_id, acao: str):
        """Alimenta correlação Observer cluster → ação."""
        acao = str(acao).replace('_lua', '')
        self._cluster_acao[f"C{cluster_id}"][acao] += 1

    # ═══════════════════════════════════════════════════════
    # SUPERPOSIÇÃO ENTROPICA — o coração do MCR
    # ═══════════════════════════════════════════════════════

    def decidir(self, texto: str, mk_pred: Tuple[Optional[str], float],
                cluster_id=None, cluster_conf=0.0) -> Tuple[str, float]:
        """Superposição multi-nível: combina todos os níveis em uma decisão.

        Cada nível produz uma distribuição. Distribuições são combinadas
        com peso = (1 - entropia_normalizada). argmax sobre o resultado.

        Sem ifs. Sem cascade. Apenas matemática.
        """
        # Coleta distribuições de cada nível
        distribs = []

        # Nível 1: Markov 1ª ordem
        acao_mk, conf_mk = mk_pred
        if acao_mk:
            d_mk = {str(acao_mk).replace('_lua', ''): conf_mk}
            h_mk = self._entropia_dist(d_mk)
            distribs.append((d_mk, h_mk))

        # Nível 2: Coupling palavras → ação
        d_palavra = self._dist_palavras(texto)
        if d_palavra:
            h_pal = self._entropia_dist(d_palavra)
            distribs.append((d_palavra, h_pal))

        # Nível 3: Observer cluster → ação
        if cluster_id is not None:
            d_cluster = self._dist_cluster(cluster_id)
            if d_cluster:
                h_cl = self._entropia_dist(d_cluster)
                distribs.append((d_cluster, h_cl))

        # Nível 4: Posições do fingerprint → ação
        d_pos = self._dist_posicoes(texto)
        if d_pos:
            h_pos = self._entropia_dist(d_pos)
            distribs.append((d_pos, h_pos))

        # Superposição: combina todas as distribuições
        if not distribs:
            return (acao_mk or 'responder'), conf_mk

        combinada = self._superpor(distribs)
        if not combinada:
            return (acao_mk or 'responder'), conf_mk

        melhor = max(combinada, key=combinada.get)
        conf = combinada[melhor]
        return melhor, conf

    # ═══════════════════════════════════════════════════════
    # SUPERPOSIÇÃO
    # ═══════════════════════════════════════════════════════

    def _superpor(self, distribs: List[Tuple[Dict[str, float], float]]) -> Dict[str, float]:
        """Combina N distribuições com peso entrópico.

        Cada distribuição i tem peso w_i = (1 - H_i).
        Distribuições mais certas (entropia baixa) pesam mais.
        """
        if not distribs:
            return {}

        # Normaliza pesos
        pesos_raw = [(1.0 - h) for _, h in distribs]
        total_raw = sum(pesos_raw) or 1.0
        pesos = [w / total_raw for w in pesos_raw]

        # Soma ponderada
        combinada: Dict[str, float] = defaultdict(float)
        for (d, _), peso in zip(distribs, pesos):
            if not d:
                continue
            # Normaliza a distribuição antes de somar
            total_d = sum(d.values()) or 1.0
            for acao, prob in d.items():
                combinada[acao] += (prob / total_d) * peso

        # Normaliza resultado
        total = sum(combinada.values()) or 1.0
        return {a: s / total for a, s in combinada.items()}

    # ═══════════════════════════════════════════════════════
    # DISTRIBUIÇÕES POR NÍVEL
    # ═══════════════════════════════════════════════════════

    def _dist_palavras(self, texto: str) -> Dict[str, float]:
        """Distribuição de ações a partir das palavras do input."""
        palavras = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        scores: Dict[str, float] = defaultdict(float)
        for p in set(palavras):
            dist = self._palavra_acao.get(p, {})
            total = sum(dist.values()) or 1
            for a, c in dist.items():
                scores[a] += c / total
        return dict(scores) if scores else {}

    def _dist_cluster(self, cluster_id) -> Dict[str, float]:
        """Distribuição de ações a partir do Observer cluster."""
        dist = self._cluster_acao.get(f"C{cluster_id}", {})
        if not dist:
            return {}
        total = sum(dist.values()) or 1
        return {a: c / total for a, c in dist.items()}

    def _dist_posicoes(self, texto: str) -> Dict[str, float]:
        """Distribuição de ações a partir das posições do fingerprint."""
        partes = texto.replace('_', ' ').split()
        scores: Dict[str, float] = defaultdict(float)
        for i, p in enumerate(partes[:6]):
            dist = self._posicao_acao.get(f"P{i}:{p[:10]}", {})
            total = sum(dist.values()) or 1
            for a, c in dist.items():
                scores[a] += c / total
        return dict(scores) if scores else {}

    # ═══════════════════════════════════════════════════════
    # ENTROPIA
    # ═══════════════════════════════════════════════════════

    def _entropia_dist(self, d: Dict[str, float]) -> float:
        """Entropia Shannon de uma distribuição de probabilidade."""
        if not d:
            return 1.0
        total = sum(d.values()) or 1.0
        h = 0.0
        for v in d.values():
            p = v / total
            if p > 0:
                h -= p * math.log2(p)
        max_h = math.log2(max(len(d), 2))
        return h / max_h if max_h > 0 else 1.0

    # ═══════════════════════════════════════════════════════
    # LEGADO (compatibilidade)
    # ═══════════════════════════════════════════════════════

    def predizer(self, texto: str, acao_markov: str = None) -> Tuple[Optional[str], float]:
        """Compatibilidade com API antiga — delega para decidir."""
        return self.decidir(texto, (acao_markov, 0.5 if acao_markov else 0.0))

    def predizer_cluster(self, cluster_id, acao_markov: str = None) -> Tuple[Optional[str], float]:
        """Prediz ação baseado apenas no cluster."""
        d = self._dist_cluster(cluster_id)
        if not d:
            return None, 0.0
        melhor = max(d, key=d.get)
        return melhor, d[melhor]

    def estatisticas(self) -> Dict:
        return {
            'total': self._total,
            'palavras': len(self._palavra_acao),
            'clusters': len(self._cluster_acao),
            'posicoes': len(self._posicao_acao),
        }
