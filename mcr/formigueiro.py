"""Formigueiro — Pertencimento multiplo e sobreposto.

Reformulação da clusterizacao: cada item pertence a MULTIPLOS clusters
em diferentes graus (P(cluster|item)). Nao exclusivo.

O numero 1 pertence a Fibonacci, Primos, Quadrados, Collatz —
simultaneamente. Um fragmento "16 8 4 2" toca Collatz sem ser
Collatz completo. A assinatura de algo = união de todos os clusters
que toca.

Como o formigueiro: cada formiga nao e operaria OU soldada — e tudo,
em diferentes graus. O formigueiro emerge da sobreposicao.

Pilar 1: P(cluster|item) — pertencimento markoviano, nao booleano
Pilar 2: grau de pertencimento emerge dos dados (NMI + IDF)
Pilar 9: se item nao toca nenhum cluster, admite (sem forçar)

Decisao NAO e rotear para UM cluster. E COMBINAR predicoes de TODOS
os clusters que o input toca, ponderadas pelo grau de pertencimento.

Uso:
    from mcr.formigueiro import Formigueiro
    f = Formigueiro(coupling)
    f.construir()
    resultado = f.decidir("sequencia dois quatro seis oito")
    # resultado contem TODOS os clusters tocados e suas predicoes
"""
import math, re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set, Optional, Any

from mcr.coupling import MCRCoupling


_RE_TOKENS = re.compile(r'[a-zà-ÿ]{2,}|[0-9]+')


class Formigueiro:
    """Pertencimento multiplo e sobreposto (formigueiro).

    Diferente de clustering exclusivo (arvore), cada item pertence a
    multiplos clusters em diferentes graus. A decisao combina predicoes
    de todos os clusters tocados.

    O formigueiro e a SOMA de todos os pertencimentos, nao a escolha
    de um unico.
    """

    def __init__(self, coupling: MCRCoupling):
        self._c = coupling
        self._clusters: Dict[str, Set[str]] = {}  # nome -> acoes
        self._sub_couplings: Dict[str, MCRCoupling] = {}
        self._pertencimento_cache: Dict[str, Dict[str, float]] = {}
        self._construido = False

    def construir(self) -> dict:
        """Construir o formigueiro: identificar clusters e criar sub-MCRs.

        Cada cluster e um sub-MCR isolado. Mas as ACOES podem aparecer
        em multiplos clusters (pertencimento sobreposto).
        """
        acoes = list(self._c._freq_acao.keys())
        if len(acoes) < 2:
            return {'n_clusters': 0, 'status': 'sem_dados'}

        # 1. Calcular NMI semantico entre pares de acoes
        nmi_matriz = self._calcular_nmi_acoes(acoes)

        # 2. Threshold emergente (Pilar 2): max gap na distribuicao
        nmis = sorted(nmi_matriz.values())
        threshold = self._threshold_emergente(nmis)

        # 3. Clustering: acoes que compartilham NMI > threshold formam cluster
        # MAS uma acao pode estar em multiplos clusters (pertencimento sobreposto)
        clusters = self._clusterizar_sobreposto(acoes, nmi_matriz, threshold)

        # 4. Criar sub-MCR para cada cluster
        for nome, acoes_cluster in clusters.items():
            sub = self._criar_sub_coupling(acoes_cluster)
            self._sub_couplings[nome] = sub
            self._clusters[nome] = acoes_cluster

        self._construido = True

        return {
            'n_clusters': len(self._clusters),
            'clusters': {n: sorted(a) for n, a in self._clusters.items()},
            'threshold': round(threshold, 4),
            'acoes_por_cluster': {n: len(a) for n, a in self._clusters.items()},
            'pertencimento_medio': self._pertencimento_medio(),
        }

    def _calcular_nmi_acoes(self, acoes: List[str]) -> Dict[Tuple[str, str], float]:
        """Calcula NMI semantico entre todos os pares de acoes."""
        nmi_matriz = {}
        for i, a1 in enumerate(acoes):
            for j, a2 in enumerate(acoes):
                if i < j:
                    feat1 = self._c._acao_features.get(a1, {})
                    feat2 = self._c._acao_features.get(a2, {})
                    if feat1 and feat2:
                        if hasattr(self._c, '_nmi_semantico'):
                            nmi = self._c._nmi_semantico(feat1, feat2)
                        else:
                            nmi = self._c._nmi(feat1, feat2)
                    else:
                        nmi = 0.0
                    nmi_matriz[(a1, a2)] = nmi
        return nmi_matriz

    @staticmethod
    def _threshold_emergente(nmis: List[float]) -> float:
        """Threshold emergente: max gap na distribuicao de NMIs."""
        if len(nmis) < 3:
            return nmis[len(nmis) // 2] if nmis else 0.5

        max_gap = 0.0
        idx_gap = len(nmis) // 2
        for i in range(1, len(nmis)):
            gap = nmis[i] - nmis[i - 1]
            if gap > max_gap:
                max_gap = gap
                idx_gap = i

        threshold = (nmis[idx_gap] + nmis[idx_gap - 1]) / 2

        # Se gap nao e significativo, usar mediana
        range_nmi = nmis[-1] - nmis[0]
        if range_nmi > 0 and max_gap / range_nmi < 0.1:
            threshold = nmis[len(nmis) // 2]

        return threshold

    def _clusterizar_sobreposto(self, acoes: List[str],
                                 nmi_matriz: Dict[Tuple[str, str], float],
                                 threshold: float) -> Dict[str, Set[str]]:
        """Clusteriza com pertencimento SOBREPOSTO.

        Diferente de union-find exclusivo, cada acao pode estar em
        multiplos clusters. Uma acao esta em um cluster se tem NMI >
        threshold com PELO MENOS UMA acao daquele cluster.

        Isso permite que "1" pertença a Fibonacci, Primos, Quadrados
        simultaneamente.
        """
        # Construir grafo de similaridade
        adjacentes: Dict[str, Set[str]] = defaultdict(set)
        for (a1, a2), nmi in nmi_matriz.items():
            if nmi > threshold:
                adjacentes[a1].add(a2)
                adjacentes[a2].add(a1)

        # Componentes conexas = clusters (union-find)
        visitados: Set[str] = set()
        clusters_exclusivos: List[Set[str]] = []

        def bfs(inicio: str) -> Set[str]:
            componente = set()
            fila = [inicio]
            while fila:
                atual = fila.pop()
                if atual in visitados:
                    continue
                visitados.add(atual)
                componente.add(atual)
                fila.extend(adjacentes[atual] - visitados)
            return componente

        for a in acoes:
            if a not in visitados:
                clusters_exclusivos.append(bfs(a))

        # Agora: pertencimento SOBREPOSTO
        # Para cada acao, encontra todos os clusters que ela TOCA
        # (tem NMI > threshold com pelo menos uma acao do cluster)
        clusters_nomeados: Dict[str, Set[str]] = {}
        for i, cluster in enumerate(clusters_exclusivos):
            nome = f"cluster_{i+1}"
            # Membros diretos do cluster
            clusters_nomeados[nome] = set(cluster)

        # Sobreposicao: para cada acao, verifica se ela toca outros clusters
        # mesmo sem ser membro direto
        for acao in acoes:
            for nome, membros in clusters_nomeados.items():
                if acao in membros:
                    continue  # ja e membro
                # Verifica se acao tem NMI > threshold com algum membro
                for membro in membros:
                    par = tuple(sorted([acao, membro]))
                    if par in nmi_matriz and nmi_matriz[par] > threshold:
                        # Acao toca este cluster — adicionar (pertencimento sobreposto)
                        # Mas so se NMI for significativo (acima do threshold)
                        clusters_nomeados[nome].add(acao)
                        break

        # Remover clusters vazios
        clusters_nomeados = {n: a for n, a in clusters_nomeados.items() if a}

        return clusters_nomeados

    def _criar_sub_coupling(self, acoes: Set[str]) -> MCRCoupling:
        """Cria sub-MCR isolado para um conjunto de acoes."""
        sub = MCRCoupling()
        acoes_set = acoes

        for palavra, dist in self._c._palavra_acao.items():
            for acao, count in dist.items():
                if acao in acoes_set:
                    for _ in range(min(count, 5)):
                        sub.alimentar(palavra, acao)

        for pa, dist in self._c._transicao_palavra.items():
            if pa in sub._palavra_acao:
                for pb, count in dist.items():
                    sub._transicao_palavra[pa][pb] = count

        return sub

    def pertencimento(self, texto: str) -> Dict[str, float]:
        """Calcula grau de pertencimento do texto a cada cluster.

        P(cluster|texto) = soma de P(acao|palavra) para cada palavra
        do texto que pertence a acoes daquele cluster.

        O texto pode pertencer a MULTIPLOS clusters simultaneamente.
        O grau e a forca do pertencimento (0 a 1).

        Isso e pertencimento markoviano PURO (Pilar 1):
        P(acao|palavra) = count(palavra,acao) / count(palavra)
        Ja esta no _palavra_acao do coupling.

        Returns:
            dict {nome_cluster: grau_pertencimento}
        """
        if not self._construido:
            raise RuntimeError("Formigueiro nao construido. Chame construir() primeiro.")

        # Cache
        cache_key = texto[:100]
        if cache_key in self._pertencimento_cache:
            return self._pertencimento_cache[cache_key]

        # Pertencimento via P(acao|palavra) — markoviano puro
        tokens = _RE_TOKENS.findall(texto.lower())
        votos_cluster: Dict[str, float] = defaultdict(float)

        for token in tokens:
            # P(acao|token) = count(token,acao) / sum(count(token,*))
            dist_acao = self._c._palavra_acao.get(token, {})
            total_token = sum(dist_acao.values())
            if total_token == 0:
                continue
            for acao, count in dist_acao.items():
                p_acao = count / total_token
                # Mapear acao -> cluster(s) que a contem
                for nome_cluster, acoes_cluster in self._clusters.items():
                    if acao in acoes_cluster:
                        votos_cluster[nome_cluster] += p_acao

        # Normalizar para soma = 1 (distribuicao de pertencimento)
        total = sum(votos_cluster.values())
        if total > 0:
            pertencimentos = {n: g / total for n, g in votos_cluster.items() if g > 0}
        else:
            pertencimentos = {}

        # Ordenar por grau
        pertencimentos = dict(sorted(pertencimentos.items(), key=lambda x: -x[1]))

        self._pertencimento_cache[cache_key] = pertencimentos
        return pertencimentos

    def decidir(self, texto: str) -> Dict[str, Any]:
        """Decide combinando predicoes de TODOS os clusters tocados.

        Diferente de rotear para UM cluster, o formigueiro combina
        as predicoes de todos os clusters que o input toca, ponderadas
        pelo grau de pertencimento.

        A acao final = combinacao ponderada das predicoes de cada cluster.
        """
        if not self._construido:
            raise RuntimeError("Formigueiro nao construido.")

        # 1. Calcular pertencimento
        pert = self.pertencimento(texto)

        if not pert:
            # Nao toca nenhum cluster — usar MCR global (Pilar 9)
            acao, conf = self._c.decidir(texto, (None, 0.0))
            return {
                'acao': acao,
                'confianca': round(conf, 4),
                'clusters_tocados': {},
                'predicoes_por_cluster': {},
                'fonte': 'global',
            }

        # 2. Para cada cluster tocado, obter predicao do sub-MCR
        predicoes = {}
        for nome, grau in pert.items():
            sub = self._sub_couplings.get(nome)
            if sub and len(sub._freq_acao) > 0:
                acao, conf = sub.decidir(texto, (None, 0.0))
                predicoes[nome] = {
                    'acao': acao,
                    'confianca': conf,
                    'grau_pertencimento': round(grau, 4),
                    'peso': round(grau * conf, 4),
                }

        if not predicoes:
            acao, conf = self._c.decidir(texto, (None, 0.0))
            return {
                'acao': acao,
                'confianca': round(conf, 4),
                'clusters_tocados': pert,
                'predicoes_por_cluster': {},
                'fonte': 'global_fallback',
            }

        # 3. Combinar predicoes ponderadas pelo grau de pertencimento
        # Cada cluster vota em uma acao com peso = grau * confianca
        votos: Dict[str, float] = defaultdict(float)
        for nome, pred in predicoes.items():
            votos[pred['acao']] += pred['peso']

        # Acao final = maior voto ponderado
        acao_final = max(votos.items(), key=lambda x: x[1])[0]
        conf_final = max(votos.items(), key=lambda x: x[1])[1]

        # Normalizar confianca
        total_votos = sum(votos.values())
        if total_votos > 0:
            conf_final = conf_final / total_votos

        return {
            'acao': acao_final,
            'confianca': round(conf_final, 4),
            'clusters_tocados': {n: round(g, 4) for n, g in pert.items()},
            'predicoes_por_cluster': predicoes,
            'fonte': 'formigueiro',
        }

    def _pertencimento_medio(self) -> float:
        """Calcula pertencimento medio (quantos clusters por acao)."""
        if not self._clusters:
            return 0.0
        contagem = Counter()
        for acoes in self._clusters.values():
            for a in acoes:
                contagem[a] += 1
        if not contagem:
            return 0.0
        return sum(contagem.values()) / len(contagem)

    def estatisticas(self) -> dict:
        """Estatisticas do formigueiro."""
        contagem = Counter()
        for acoes in self._clusters.values():
            for a in acoes:
                contagem[a] += 1

        dist_pertencimento = dict(Counter(contagem.values()))

        return {
            'n_clusters': len(self._clusters),
            'n_acoes': len(contagem),
            'pertencimento_medio': round(self._pertencimento_medio(), 2),
            'distribuicao_pertencimento': dist_pertencimento,
            'acoes_por_cluster': {n: len(a) for n, a in self._clusters.items()},
            'clusters_por_acao': dict(contagem),
        }
