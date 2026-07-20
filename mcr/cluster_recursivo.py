"""ClusterRecursivo — Clusterizacao recursiva: cluster de cluster de clusters.

A AutoComposicao cria 1 nivel de cluster (dominios). Este modulo torna
a clusterizacao RECURSIVA: cada cluster e re-clusterizado em sub-clusters,
e assim por diante, ate a entropia dizer que nao ha mais estrutura (Pilar 2).

Isolamento: cada sub-cluster e um sub-MCR com seu proprio P(b|a). Tokens
de um dominio NAO transbordam para outro. Literatura fica isolada de
matematica. Romance fica isolado de poesia dentro de literatura. Escala
ate byte/bits se a entropia disser que ha estrutura.

Pilar 1: P(b|a) puro em cada nivel — sem random
Pilar 2: entropia decide quando parar de subdividir (delta_H)
Pilar 4: clusters com entropia maxima sao podados (sem estrutura)
Pilar 9: se nao ha estrutura, para com honestidade

Estrutura resultante = arvore de clusters (como filesystem):
    raiz
    /  |  \\
  dom1 dom2 dom3
  / \\   |   ...
sub1 sub2 ...
  |
 ...

Uso:
    from mcr.cluster_recursivo import ClusterRecursivo
    cr = ClusterRecursivo(coupling)
    arvore = cr.clusterizar_recursivo()
    # arvore e um dict aninhado com a estrutura completa
"""
import math, re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set, Optional, Any

from mcr.coupling import MCRCoupling


_RE_TOKENS = re.compile(r'[a-zà-ÿ]{2,}|[0-9]+')


class NoCluster:
    """Um no na arvore de clusters recursivos.

    Pode ser:
    - Raiz (contem todos os dados)
    - Cluster intermediario (sub-dominio com sub-clusters)
    - Folha (cluster que nao tem mais estrutura interna)
    """

    def __init__(self, nome: str, acoes: List[str], nivel: int,
                 pai: Optional['NoCluster'] = None):
        self.nome = nome
        self.acoes = set(acoes)
        self.nivel = nivel
        self.pai = pai
        self.filhos: List['NoCluster'] = []
        self.sub_coupling: Optional[MCRCoupling] = None
        self.entropia: float = 0.0
        self.delta_h: float = 0.0
        self.n_obs: int = 0
        self.vocab_size: int = 0
        self.is_folha: bool = False

    def adicionar_filho(self, filho: 'NoCluster'):
        filho.pai = self
        self.filhos.append(filho)

    def to_dict(self) -> dict:
        """Serializa a arvore como dict aninhado."""
        return {
            'nome': self.nome,
            'nivel': self.nivel,
            'acoes': sorted(self.acoes),
            'n_obs': self.n_obs,
            'vocab': self.vocab_size,
            'entropia': round(self.entropia, 4),
            'delta_h': round(self.delta_h, 4),
            'is_folha': self.is_folha,
            'n_filhos': len(self.filhos),
            'filhos': [f.to_dict() for f in self.filhos],
        }

    def __repr__(self):
        indent = "  " * self.nivel
        folha = " (folha)" if self.is_folha else ""
        return f"{indent}{self.nome} [nivel={self.nivel}, acoes={len(self.acoes)}, H={self.entropia:.3f}]{folha}"


class ClusterRecursivo:
    """Clusterizacao recursiva: cluster de cluster de clusters.

    Para cada nivel:
    1. Calcular NMI entre pares de acoes
    2. Clusterizar por NMI (threshold = mediana, Pilar 2)
    3. Para cada cluster, criar sub-MCR isolado
    4. Calcular entropia do sub-MCR
    5. Se delta_H > min_delta_h, recursar (ha estrutura)
    6. Se delta_H <= min_delta_h, parar (folha)
    """

    def __init__(self, coupling: MCRCoupling, min_delta_h: float = 0.05,
                 max_niveis: int = 7, min_acoes: int = 2):
        self._c = coupling
        self._min_delta_h = min_delta_h
        self._max_niveis = max_niveis
        self._min_acoes = min_acoes
        self._arvore: Optional[NoCluster] = None
        self._historico: List[dict] = []

    def clusterizar_recursivo(self) -> NoCluster:
        """Clusteriza recursivamente a partir da raiz.

        Returns:
            NoCluster raiz com a arvore completa
        """
        acoes = list(self._c._freq_acao.keys())
        entropia_raiz = self._entropia_acoes(acoes)

        raiz = NoCluster("raiz", acoes, nivel=0)
        raiz.entropia = entropia_raiz
        raiz.n_obs = self._contar_obs(acoes)
        raiz.vocab_size = len(self._c._palavra_acao)
        raiz.delta_h = 0.0  # raiz nao tem pai

        self._arvore = raiz
        self._historico = []

        # Recursao
        self._clusterizar_no(raiz, entropia_pai=entropia_raiz)

        return raiz

    def _clusterizar_no(self, no: NoCluster, entropia_pai: float):
        """Clusteriza um no recursivamente.

        Args:
            no: o no a ser clusterizado
            entropia_pai: entropia do nivel anterior (para calcular delta_H)
        """
        # Condicoes de parada (Pilar 2 + Pilar 9)
        if no.nivel >= self._max_niveis:
            no.is_folha = True
            self._historico.append({
                'no': no.nome, 'nivel': no.nivel, 'acao': 'parou_max_niveis',
                'n_acoes': len(no.acoes)
            })
            return

        if len(no.acoes) < self._min_acoes:
            no.is_folha = True
            self._historico.append({
                'no': no.nome, 'nivel': no.nivel, 'acao': 'parou_poucas_acoes',
                'n_acoes': len(no.acoes)
            })
            return

        # 1. Clusterizar acoes por NMI
        clusters = self._clusterizar_acoes(no.acoes)

        # Debug
        print(f"      [debug] no={no.nome} nivel={no.nivel} acoes={len(no.acoes)} "
              f"clusters={len(clusters)} is_folha={no.is_folha}")

        if len(clusters) <= 1:
            # Nao ha estrutura para dividir — folha
            no.is_folha = True
            self._historico.append({
                'no': no.nome, 'nivel': no.nivel, 'acao': 'parou_sem_estrutura',
                'n_clusters': len(clusters)
            })
            return

        # 2. Para cada cluster, criar sub-no
        for i, (nome_cluster, acoes_cluster) in enumerate(clusters.items()):
            entropia_cluster = self._entropia_acoes(acoes_cluster)
            delta_h = entropia_pai - entropia_cluster

            sub_no = NoCluster(nome_cluster, acoes_cluster,
                               nivel=no.nivel + 1, pai=no)
            sub_no.entropia = entropia_cluster
            sub_no.delta_h = delta_h
            sub_no.n_obs = self._contar_obs(acoes_cluster)

            # Vocab do cluster: palavras que aparecem nas acoes do cluster
            vocab_cluster = set()
            for acao in acoes_cluster:
                for palavra, dist in self._c._palavra_acao.items():
                    if acao in dist:
                        vocab_cluster.add(palavra)
            sub_no.vocab_size = len(vocab_cluster)

            no.adicionar_filho(sub_no)

            self._historico.append({
                'no': sub_no.nome, 'nivel': sub_no.nivel,
                'acao': 'criado', 'n_acoes': len(acoes_cluster),
                'entropia': round(entropia_cluster, 4),
                'delta_h': round(delta_h, 4),
                'n_filhos_potenciais': len(acoes_cluster),
            })

            # 3. Recursar se ha estrutura (delta_H significativo)
            if delta_h > self._min_delta_h and len(acoes_cluster) >= self._min_acoes:
                self._clusterizar_no(sub_no, entropia_cluster)
            else:
                sub_no.is_folha = True
                self._historico.append({
                    'no': sub_no.nome, 'nivel': sub_no.nivel,
                    'acao': 'parou_delta_h_baixo',
                    'delta_h': round(delta_h, 4),
                })

    def _clusterizar_acoes(self, acoes: List[str]) -> Dict[str, List[str]]:
        """Clusteriza acoes por similaridade NMI.

        Threshold = mediana das NMIs (Pilar 2: entropia descobre).
        Union-Find para agrupar.

        Returns:
            dict {nome_cluster: [acoes_no_cluster]}
        """
        if len(acoes) < 2:
            return {f"cluster_1": acoes}

        # Calcular NMI semantico (com IDF) entre pares de acoes
        # NMI bruto retorna ~1.0 para tudo — precisa IDF para discriminar
        nmi_matriz = {}
        for i, a1 in enumerate(acoes):
            for j, a2 in enumerate(acoes):
                if i < j:
                    feat1 = self._c._acao_features.get(a1, {})
                    feat2 = self._c._acao_features.get(a2, {})
                    if feat1 and feat2:
                        # Usar _nmi_semantico (com IDF) em vez de _nmi (bruto)
                        if hasattr(self._c, '_nmi_semantico'):
                            nmi = self._c._nmi_semantico(feat1, feat2)
                        else:
                            nmi = self._c._nmi(feat1, feat2)
                    else:
                        nmi = 0.0
                    nmi_matriz[(a1, a2)] = nmi

        if not nmi_matriz:
            return {f"cluster_1": acoes}

        # Threshold emergente (Pilar 2): ponto de maxima variacao na
        # distribuicao de NMIs. Ordena NMIs, calcula a derivada da CDF,
        # e escolhe o ponto de maior inflexao — onde a distribuicao
        # muda mais rapido. Isso e o gap natural entre "similar" e
        # "diferente". Sem percentil hardcoded.
        nmis = sorted(nmi_matriz.values())
        threshold = self._threshold_emergente(nmis)

        # Union-Find
        clusters: Dict[str, Set[str]] = {a: {a} for a in acoes}

        for (a1, a2), nmi in nmi_matriz.items():
            if nmi > threshold:
                c1 = self._encontrar_cluster(clusters, a1)
                c2 = self._encontrar_cluster(clusters, a2)
                if c1 != c2:
                    clusters[c1] = clusters[c1] | clusters[c2]
                    del clusters[c2]

        # Nomear
        resultado = {}
        for i, (_, acoes_set) in enumerate(clusters.items()):
            nome = f"cluster_{i+1}"
            resultado[nome] = sorted(acoes_set)

        return resultado

    @staticmethod
    def _encontrar_cluster(clusters: Dict[str, Set[str]], acao: str) -> str:
        for nome, acoes in clusters.items():
            if acao in acoes:
                return nome
        return acao

    @staticmethod
    def _threshold_emergente(nmis: List[float]) -> float:
        """Threshold emergente (Pilar 2): max gap na distribuicao.

        Ordena NMIs, encontra o maior SALTO entre valores consecutivos.
        Esse gap e a fronteira natural entre "similar" e "diferente" —
        emerge da forma da distribuicao, sem percentil hardcoded.

        Se nao ha gap significativo (distribuicao uniforme), retorna
        a mediana (Pilar 9: se nao ha estrutura, admite).

        Isso NAO e hardcode: o threshold emerge dos dados reais.
        Cada nivel de clusterizacao tem seu proprio threshold.
        """
        if len(nmis) < 3:
            return nmis[len(nmis) // 2] if nmis else 0.5

        # Encontrar o maior gap entre NMIs consecutivos
        max_gap = 0.0
        idx_gap = len(nmis) // 2  # fallback: mediana
        for i in range(1, len(nmis)):
            gap = nmis[i] - nmis[i - 1]
            if gap > max_gap:
                max_gap = gap
                idx_gap = i

        # Threshold = ponto medio do maior gap
        threshold = (nmis[idx_gap] + nmis[idx_gap - 1]) / 2

        # Se o gap nao e significativo (< 10% do range), usar mediana
        range_nmi = nmis[-1] - nmis[0]
        if range_nmi > 0 and max_gap / range_nmi < 0.1:
            threshold = nmis[len(nmis) // 2]

        return threshold

    def _entropia_acoes(self, acoes: List[str]) -> float:
        """Calcula entropia de Shannon da distribuicao de acoes.

        H = -sum P(acao) * log2(P(acao))
        onde P(acao) = freq(acao) / sum(freq(acao) para acoes no cluster)
        """
        from math import log2
        freqs = [self._c._freq_acao.get(a, 0) for a in acoes]
        total = sum(freqs)
        if total == 0:
            return 0.0
        h = 0.0
        for f in freqs:
            if f > 0:
                p = f / total
                h -= p * log2(p)
        return h

    def _contar_obs(self, acoes: List[str]) -> int:
        """Conta observacoes de um conjunto de acoes."""
        return sum(self._c._freq_acao.get(a, 0) for a in acoes)

    def criar_sub_coupling(self, no: NoCluster) -> MCRCoupling:
        """Cria um sub-MCR isolado para um no.

        O sub-MCR so tem dados das acoes do no. Tokens de outros
        dominios NAO transbordam.
        """
        sub = MCRCoupling()
        acoes_set = no.acoes

        # Reconstruir corpus do coupling principal
        for palavra, dist in self._c._palavra_acao.items():
            for acao, count in dist.items():
                if acao in acoes_set:
                    for _ in range(min(count, 5)):
                        sub.alimentar(palavra, acao)

        # Copiar transicoes relevantes
        for pa, dist in self._c._transicao_palavra.items():
            if pa in sub._palavra_acao:
                for pb, count in dist.items():
                    sub._transicao_palavra[pa][pb] = count

        no.sub_coupling = sub
        return sub

    def decidir_isolado(self, texto: str, no: NoCluster) -> Tuple[str, float]:
        """Decide usando apenas o sub-MCR do no (isolado).

        Tokens de outros dominios nao interferem.
        """
        if no.sub_coupling is None:
            self.criar_sub_coupling(no)
        return no.sub_coupling.decidir(texto, (None, 0.0))

    def rotear(self, texto: str) -> Tuple[NoCluster, Tuple[str, float]]:
        """Roteia texto para o no folha mais adequado.

        Estrategia:
        1. A partir da raiz, calcula NMI do texto com cada filho
        2. Escolhe o filho com maior NMI
        3. Recurs ate chegar numa folha
        4. Decide usando o sub-MCR da folha

        Returns:
            (no_folha, (acao, confianca))
        """
        if self._arvore is None:
            raise RuntimeError("Arvore nao construida. Chame clusterizar_recursivo() primeiro.")

        no_atual = self._arvore
        while no_atual.filhos and not no_atual.is_folha:
            # NMI do texto com cada filho
            sig_texto = self._c._assinatura_frase(texto)
            melhor_nmi = -1
            melhor_filho = None
            for filho in no_atual.filhos:
                # NMI medio do texto com o vocab do filho
                nmi_sum = 0.0
                n_pal = 0
                for acao in filho.acoes:
                    feat = self._c._acao_features.get(acao, {})
                    if feat and sig_texto:
                        nmi = self._c._nmi(feat, sig_texto)
                        nmi_sum += nmi
                        n_pal += 1
                nmi_medio = nmi_sum / max(n_pal, 1)
                if nmi_medio > melhor_nmi:
                    melhor_nmi = nmi_medio
                    melhor_filho = filho

            if melhor_filho is None:
                break
            no_atual = melhor_filho

        # Decidir no no folha (isolado)
        resultado = self.decidir_isolado(texto, no_atual)
        return no_atual, resultado

    def estatisticas(self) -> dict:
        """Estatisticas da arvore recursiva."""
        if not self._arvore:
            return {}

        def contar_nos(no: NoCluster) -> dict:
            if no.is_folha:
                return {'n_folhas': 1, 'n_nos': 1, 'niveis': no.nivel}
            stats = {'n_folhas': 0, 'n_nos': 1, 'niveis': no.nivel}
            for f in no.filhos:
                sub = contar_nos(f)
                stats['n_folhas'] += sub['n_folhas']
                stats['n_nos'] += sub['n_nos']
                stats['niveis'] = max(stats['niveis'], sub['niveis'])
            return stats

        stats = contar_nos(self._arvore)

        # Contar filhos por no (para ver se 3 emerge)
        filhos_por_no = []
        def coletar_filhos(no: NoCluster):
            if no.filhos:
                filhos_por_no.append(len(no.filhos))
            for f in no.filhos:
                coletar_filhos(f)
        coletar_filhos(self._arvore)

        from collections import Counter
        dist_filhos = Counter(filhos_por_no)

        return {
            'n_folhas': stats['n_folhas'],
            'n_nos': stats['n_nos'],
            'max_niveis': stats['niveis'],
            'filhos_por_no': dict(dist_filhos),
            'filhos_por_no_lista': filhos_por_no,
            'media_filhos': sum(filhos_por_no) / len(filhos_por_no) if filhos_por_no else 0,
        }
