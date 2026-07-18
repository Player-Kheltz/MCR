"""mcr.auto_composicao — Auto-composição: MCR que constrói MCRs.

O MCR agora observa um domínio, detecta que precisa de um especialista,
cria um novo MCRCoupling treinado para aquele domínio, e o orquestra.

É como mixture-of-experts mas markoviano: o MCR principal decide qual
especialista consultar (ou si mesmo) para cada input.

Pilar 6: O MCR descobre seus próprios níveis — aqui, ele descobre
que precisa de novos MCRs e os cria.

5 capacidades:
1. Observar domínio — detectar clusters de ações que formam sub-domínios
2. Criar especialista — gerar MCRCoupling com corpus do sub-domínio
3. Compor — construir equipe de especialistas (um por sub-domínio)
4. Orquestrar — rotear input para o especialista certo (NMI + 5D)
5. Avaliar — medir qualidade da composição (acerto vs MCR solo)

Tudo Markov + entropia + NMI. Zero GPU, zero dependências.
"""
import math
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Optional, Any

from mcr.coupling import MCRCoupling

try:
    from mcr.equacao_mcr import avaliar_5d
except ImportError:
    from equacao_mcr import avaliar_5d


class EspecialistaMCR:
    """Um MCR especialista para um sub-domínio.

    Cada especialista é um MCRCoupling com corpus focado em um
    conjunto específico de ações.
    """

    def __init__(self, nome: str, acoes: List[str],
                 coupling: MCRCoupling):
        self.nome = nome
        self.acoes = set(acoes)
        self._coupling = coupling
        # Estatísticas
        self._n_consultas = 0
        self._n_acertos = 0

    def consultar(self, estado: str) -> Tuple[str, float]:
        """Consulta o especialista para um estado."""
        self._n_consultas += 1
        return self._coupling.decidir(estado, (None, 0.0))

    def registrar_acerto(self, correto: bool) -> None:
        if correto:
            self._n_acertos += 1

    @property
    def taxa_acerto(self) -> float:
        return self._n_acertos / max(1, self._n_consultas)

    def estatisticas(self) -> Dict[str, Any]:
        return {
            'nome': self.nome,
            'acoes': list(self.acoes),
            'n_consultas': self._n_consultas,
            'n_acertos': self._n_acertos,
            'taxa_acerto': round(self.taxa_acerto, 4),
            'vocabulario': len(self._coupling._palavra_acao),
        }


class AutoComposicao:
    """MCR que constrói MCRs especializados.

    Observa os clusters de ações no coupling principal, cria um
    especialista para cada cluster, e orquestra consultas roteando
    cada input para o especialista mais adequado.

    Uso:
        ac = AutoComposicao(coupling)
        especialistas = ac.compor(n_clusters=3)
        resultado = ac.orquestrar("criar monstro")
    """

    def __init__(self, coupling: MCRCoupling):
        self._coupling = coupling  # MCR principal (orquestrador)
        self._especialistas: Dict[str, EspecialistaMCR] = {}
        self._historico_orquestracao: List[Dict] = []

    # ═══════════════════════════════════════════════════════════════
    # 1. OBSERVAR DOMÍNIO — detectar sub-domínios via clustering
    # ═══════════════════════════════════════════════════════════════

    def observar_dominio(self) -> Dict[str, Any]:
        """Observa o coupling e identifica sub-domínios.

        Sub-domínios = clusters de ações que co-ocorrem (compartilham
        palavras via NMI). Ações que compartilham muitas palavras
        formam um cluster (sub-domínio).

        Returns:
            dict com 'n_clusters', 'clusters', 'acoes_por_cluster'
        """
        acoes = list(self._coupling._freq_acao.keys())
        if len(acoes) < 2:
            return {'n_clusters': 0, 'clusters': {}, 'acoes': acoes}

        # Calcular NMI entre cada par de ações (via _acao_features)
        nmi_matriz = {}
        for i, a1 in enumerate(acoes):
            for j, a2 in enumerate(acoes):
                if i < j:
                    feat1 = self._coupling._acao_features.get(a1, {})
                    feat2 = self._coupling._acao_features.get(a2, {})
                    if feat1 and feat2:
                        nmi = self._coupling._nmi(feat1, feat2)
                    else:
                        nmi = 0.0
                    nmi_matriz[(a1, a2)] = nmi

        # Clustering simples: aglomerativo por NMI
        # Threshold: mediana das NMIs (entropico, nao hardcoded)
        if nmi_matriz:
            nmis = sorted(nmi_matriz.values())
            threshold = nmis[len(nmis) // 2]
        else:
            threshold = 0.5

        # Union-Find para agrupar ações
        clusters: Dict[str, Set[str]] = {a: {a} for a in acoes}

        for (a1, a2), nmi in nmi_matriz.items():
            if nmi > threshold:
                # Merge clusters de a1 e a2
                c1 = self._encontrar_cluster(clusters, a1)
                c2 = self._encontrar_cluster(clusters, a2)
                if c1 != c2:
                    clusters[c1] = clusters[c1] | clusters[c2]
                    del clusters[c2]

        # Nomear clusters
        clusters_nomeados = {}
        for i, (_, acoes_set) in enumerate(clusters.items()):
            nome = f"dominio_{i+1}"
            clusters_nomeados[nome] = sorted(acoes_set)

        return {
            'n_clusters': len(clusters_nomeados),
            'clusters': clusters_nomeados,
            'threshold_nmi': round(threshold, 4),
            'acoes': acoes,
        }

    @staticmethod
    def _encontrar_cluster(clusters: Dict[str, Set[str]],
                           acao: str) -> str:
        """Encontra o cluster que contém a ação."""
        for nome, acoes in clusters.items():
            if acao in acoes:
                return nome
        return acao

    # ═══════════════════════════════════════════════════════════════
    # 2. CRIAR ESPECIALISTA — gerar MCRCoupling para sub-domínio
    # ═══════════════════════════════════════════════════════════════

    def criar_especialista(self, nome: str,
                           acoes: List[str]) -> EspecialistaMCR:
        """Cria um especialista para um conjunto de ações.

        Filtra o corpus do MCR principal para apenas exemplos das
        ações especificadas e treina um novo MCRCoupling.

        Args:
            nome: identificador do especialista
            acoes: lista de ações que o especialista deve cobrir

        Returns:
            EspecialistaMCR treinado.
        """
        coupling_esp = MCRCoupling()
        acoes_set = set(acoes)

        # Reconstruir corpus: para cada (palavra, acao) no coupling principal
        # que pertence ao sub-domínio, alimentar o especialista
        for palavra, dist in self._coupling._palavra_acao.items():
            for acao, count in dist.items():
                if acao in acoes_set:
                    # Alimentar count vezes (preservar frequência)
                    for _ in range(min(count, 5)):  # cap para performance
                        coupling_esp.alimentar(palavra, acao)

        # Copiar transições relevantes
        for pa, dist in self._coupling._transicao_palavra.items():
            # Só copiar se pa está no vocabulário do especialista
            if pa in coupling_esp._palavra_acao:
                for pb, count in dist.items():
                    coupling_esp._transicao_palavra[pa][pb] = count

        especialista = EspecialistaMCR(nome, acoes, coupling_esp)
        self._especialistas[nome] = especialista
        return especialista

    # ═══════════════════════════════════════════════════════════════
    # 3. COMPOR — construir equipe de especialistas
    # ═══════════════════════════════════════════════════════════════

    def compor(self, n_clusters: int = 0) -> Dict[str, Any]:
        """Compõe uma equipe de especialistas automaticamente.

        1. Observa domínio → identifica clusters
        2. Cria um especialista por cluster
        3. Retorna relatório da composição

        Args:
            n_clusters: se 0, detecta automaticamente via NMI

        Returns:
            dict com 'especialistas', 'n_clusters', 'clusters'
        """
        dominio = self.observar_dominio()
        clusters = dominio['clusters']

        if not clusters:
            return {
                'especialistas': [],
                'n_clusters': 0,
                'status': 'sem_dados',
            }

        especialistas_criados = []
        for nome_cluster, acoes in clusters.items():
            esp = self.criar_especialista(nome_cluster, acoes)
            especialistas_criados.append(esp.estatisticas())

        return {
            'especialistas': especialistas_criados,
            'n_clusters': len(especialistas_criados),
            'clusters': clusters,
            'threshold_nmi': dominio.get('threshold_nmi', 0.0),
            'status': 'composto',
        }

    # ═══════════════════════════════════════════════════════════════
    # 4. ORQUESTRAR — rotear input para especialista certo
    # ═══════════════════════════════════════════════════════════════

    def orquestrar(self, estado: str) -> Dict[str, Any]:
        """Roteia o input para o especialista mais adequado.

        Para cada especialista, calcula NMI entre o estado e o
        vocabulário do especialista. O especialista com maior NMI
        é o mais adequado.

        Se nenhum especialista tem NMI suficiente, usa o MCR principal.

        Returns:
            dict com 'acao', 'especialista_usado', 'confianca',
            'nmi_por_especialista'
        """
        if not self._especialistas:
            # Sem especialistas — usar MCR principal
            acao, conf = self._coupling.decidir(estado, (None, 0.0))
            return {
                'acao': acao,
                'confianca': round(conf, 4),
                'especialista_usado': 'mcr_principal',
                'nmi_por_especialista': {},
            }

        # Calcular NMI do estado com cada especialista
        sig_estado = self._coupling._assinatura_frase(estado)
        nmi_por_esp = {}

        for nome, esp in self._especialistas.items():
            # NMI entre estado e vocabulário do especialista
            nmi_sum = 0.0
            n_palavras = 0
            for palavra in esp._coupling._palavra_acao:
                sig_p = self._coupling._assinatura_palavra(palavra)
                if sig_p and sig_estado:
                    nmi = self._coupling._nmi(sig_p, sig_estado)
                    nmi_sum += nmi
                    n_palavras += 1
            nmi_medio = nmi_sum / max(n_palavras, 1)
            nmi_por_esp[nome] = round(nmi_medio, 4)

        # Escolher especialista com maior NMI
        melhor_esp = max(nmi_por_esp, key=nmi_por_esp.get)
        melhor_nmi = nmi_por_esp[melhor_esp]

        # Se NMI muito baixo, usar MCR principal
        if melhor_nmi < 0.01:
            acao, conf = self._coupling.decidir(estado, (None, 0.0))
            especialista_usado = 'mcr_principal'
        else:
            esp = self._especialistas[melhor_esp]
            acao, conf = esp.consultar(estado)
            especialista_usado = melhor_esp

        resultado = {
            'acao': acao,
            'confianca': round(conf, 4),
            'especialista_usado': especialista_usado,
            'nmi_por_especialista': nmi_por_esp,
        }

        self._historico_orquestracao.append({
            'estado': estado[:50],
            'especialista': especialista_usado,
            'acao': acao,
            'confianca': conf,
        })

        return resultado

    # ═══════════════════════════════════════════════════════════════
    # 5. AVALIAR — comparar composição vs MCR solo
    # ═══════════════════════════════════════════════════════════════

    def avaliar_composicao(self, dataset: List[Tuple[str, str]]
                           ) -> Dict[str, Any]:
        """Avalia a composição vs MCR principal solo.

        Compara accuracy do MCR orquestrado (com especialistas)
        vs MCR principal sem especialistas.

        Args:
            dataset: lista de (texto, acao_esperada)

        Returns:
            dict com 'accuracy_orquestrado', 'accuracy_solo', 'ganho'
        """
        n_correto_orq = 0
        n_correto_solo = 0

        for texto, acao_esperada in dataset:
            # Orquestrado
            resultado_orq = self.orquestrar(texto)
            if resultado_orq['acao'] == acao_esperada:
                n_correto_orq += 1

            # Solo (MCR principal)
            acao_solo, _ = self._coupling.decidir(texto, (None, 0.0))
            if acao_solo == acao_esperada:
                n_correto_solo += 1

        n = len(dataset)
        acc_orq = n_correto_orq / max(n, 1)
        acc_solo = n_correto_solo / max(n, 1)
        ganho = acc_orq - acc_solo

        return {
            'accuracy_orquestrado': round(acc_orq, 4),
            'accuracy_solo': round(acc_solo, 4),
            'ganho': round(ganho, 4),
            'n_testes': n,
            'n_correto_orquestrado': n_correto_orq,
            'n_correto_solo': n_correto_solo,
        }

    def feedback(self, estado: str, acao_correta: str) -> None:
        """Fornece feedback à composição (para estatísticas)."""
        resultado = self.orquestrar(estado)
        esp_nome = resultado['especialista_usado']

        if esp_nome in self._especialistas:
            correto = resultado['acao'] == acao_correta
            self._especialistas[esp_nome].registrar_acerto(correto)

    # ═══════════════════════════════════════════════════════════════
    # ESTATÍSTICAS
    # ═══════════════════════════════════════════════════════════════

    def listar_especialistas(self) -> List[str]:
        """Lista nomes dos especialistas."""
        return list(self._especialistas.keys())

    def obter_especialista(self, nome: str) -> Optional[EspecialistaMCR]:
        """Retorna um especialista pelo nome."""
        return self._especialistas.get(nome)

    def estatisticas(self) -> Dict[str, Any]:
        """Estatísticas da auto-composição."""
        return {
            'n_especialistas': len(self._especialistas),
            'especialistas': [e.estatisticas() for e in self._especialistas.values()],
            'n_orquestracoes': len(self._historico_orquestracao),
            'vocabulario_principal': len(self._coupling._palavra_acao),
        }
