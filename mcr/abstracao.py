"""mcr.abstracao — Abstração hierárquica emergente.

O MCR trabalha em tokens. Cognição real opera em CONCEITOS. Este
módulo faz conceitos emergirem de padrões de padrões via NMI.

Descoberta: duas palavras pertencem ao mesmo conceito se têm
distribuições P(acao|palavra) similares (NMI alta). Conceitos
emergem sem labels, sem supervised learning — só Markov + NMI.

Hierarquia de 4 níveis:
  Nível 0: Palavras     (criar, gerar, fazer, monstro, npc, ...)
  Nível 1: Conceitos    (criacao, edicao, busca, aprendizado, ...)
  Nível 2: Temas        (acao, objeto, elemento, ...)
  Nível 3: Dominios     (sintatico, semantico, ...)

Cada nível abstrai o anterior (compressão lossy). Decisões em nível
de conceito generalizam para palavras nunca vistas.

5 capacidades:
1. Detectar conceitos — agrupar palavras por NMI de P(acao|palavra)
2. Construir hierarquia — conceitos de conceitos (n níveis)
3. Abstrair — converter texto em representação conceitual
4. Decidir em conceito — classificar via conceitos (generaliza)
5. Generalizar — atribuir palavra nova ao conceito mais próximo

Tudo Markov + entropia + NMI. Zero GPU, zero labels.
"""
import math
import re
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Optional, Any


class Conceito:
    """Um conceito emergente: cluster de palavras com distribuições similares."""

    _contador = 0

    def __init__(self, palavras: Set[str],
                 distribuicao: Dict[str, float],
                 nivel: int = 1):
        self.palavras = palavras
        self.distribuicao = distribuicao
        self.nivel = nivel
        # Nome auto-gerado: palavra mais central (maior frequência)
        self.nome = self._gerar_nome()
        # Conceitos filhos (para hierarquia)
        self.filhos: List['Conceito'] = []
        Conceito._contador += 1
        self.id = Conceito._contador

    def _gerar_nome(self) -> str:
        """Gera nome do conceito: palavra de maior informação do cluster."""
        if not self.palavras:
            return f"conceito_{self.id}"
        # Palavra mais frequente no vocabulário
        return sorted(self.palavras)[0]

    def contem(self, palavra: str) -> bool:
        return palavra in self.palavras

    def adicionar(self, palavra: str) -> None:
        self.palavras.add(palavra)

    def estatisticas(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'nome': self.nome,
            'nivel': self.nivel,
            'n_palavras': len(self.palavras),
            'palavras': sorted(list(self.palavras))[:10],
            'acoes_top': dict(sorted(
                self.distribuicao.items(), key=lambda x: -x[1]
            )[:3]),
            'n_filhos': len(self.filhos),
        }


class AbstracaoHierarquica:
    """Constrói hierarquia de abstração emergente.

    Conceitos emergem de clusters de palavras com distribuições
    P(acao|palavra) similares (NMI alta). A hierarquia é construída
    recursivamente: conceitos de conceitos.

    Uso:
        abstr = AbstracaoHierarquica(coupling)
        conceitos = abstr.detectar_conceitos()
        hierarquia = abstr.construir_hierarquia(niveis=3)
        acao = abstr.decidir_em_conceito("palavra nova desconhecida")
    """

    def __init__(self, coupling):
        self._coupling = coupling
        self._conceitos: List[Conceito] = []
        self._hierarquia: Dict[int, List[Conceito]] = {}
        self._indice_palavra_conceito: Dict[str, Conceito] = {}
        self._construido: bool = False

    # ═══════════════════════════════════════════════════════════════
    # 1. DETECTAR CONCEITOS — agrupar palavras por NMI
    # ═══════════════════════════════════════════════════════════════

    def detectar_conceitos(self) -> List[Conceito]:
        """Agrupa palavras por similaridade de P(acao|palavra).

        Duas palavras pertencem ao mesmo conceito se suas distribuições
        P(acao|palavra) são similares (NMI alta entre distribuições de
        ações, não entre assinaturas sublexicais).

        Returns:
            Lista de Conceito (nível 1).
        """
        palavras = list(self._coupling._palavra_acao.keys())
        if len(palavras) < 2:
            self._conceitos = []
            return []

        # Construir assinaturas de AÇÕES (não sublexicais)
        # P(acao|palavra) → {acao: count} = assinatura de ação
        assinaturas_acao: Dict[str, Dict[str, int]] = {}
        for p in palavras:
            dist = self._coupling._palavra_acao.get(p, {})
            if sum(dist.values()) > 0:
                assinaturas_acao[p] = dict(dist)

        palavras_com_sig = list(assinaturas_acao.keys())
        if len(palavras_com_sig) < 2:
            # Cada palavra é seu próprio conceito
            for p in palavras:
                dist = dict(self._coupling._palavra_acao[p])
                total = sum(dist.values()) or 1
                dist_norm = {a: c / total for a, c in dist.items()}
                c = Conceito({p}, dist_norm, nivel=1)
                self._conceitos.append(c)
                self._indice_palavra_conceito[p] = c
            return self._conceitos

        # Calcular NMI entre distribuições de AÇÕES de cada par
        nmi_matriz: Dict[Tuple[str, str], float] = {}
        for i, p1 in enumerate(palavras_com_sig):
            for j, p2 in enumerate(palavras_com_sig):
                if i < j:
                    nmi = self._coupling._nmi(
                        assinaturas_acao[p1], assinaturas_acao[p2]
                    )
                    nmi_matriz[(p1, p2)] = nmi

        # Agrupamento primário: por ação dominante (top-1)
        # Palavras com a mesma ação dominante pertencem ao mesmo conceito
        grupos_acao: Dict[str, Set[str]] = defaultdict(set)
        for p in palavras_com_sig:
            dist = assinaturas_acao[p]
            top_acao = max(dist, key=dist.get)
            grupos_acao[top_acao].add(p)

        # Refinamento: dentro de cada grupo, usar NMI para subdividir
        # se houver palavras com distribuições muito diferentes
        clusters: Dict[str, Set[str]] = {}
        for acao, palavras_no_grupo in grupos_acao.items():
            if len(palavras_no_grupo) <= 1:
                for p in palavras_no_grupo:
                    clusters[p] = {p}
                continue

            # Calcular NMI entre pares dentro do grupo
            pals = list(palavras_no_grupo)
            sub_nmi: Dict[Tuple[str, str], float] = {}
            for i, p1 in enumerate(pals):
                for j, p2 in enumerate(pals):
                    if i < j:
                        nmi = self._coupling._nmi(
                            assinaturas_acao[p1], assinaturas_acao[p2]
                        )
                        sub_nmi[(p1, p2)] = nmi

            # Se NMI dentro do grupo é alta (> 0.5), manter juntos
            # Se baixa, subdividir
            sub_clusters: Dict[str, Set[str]] = {p: {p} for p in pals}
            for (p1, p2), nmi in sub_nmi.items():
                if nmi > 0.3:  # mesmo conceito
                    c1 = self._encontrar_cluster(sub_clusters, p1)
                    c2 = self._encontrar_cluster(sub_clusters, p2)
                    if c1 != c2:
                        sub_clusters[c1] = sub_clusters[c1] | sub_clusters[c2]
                        del sub_clusters[c2]
                elif nmi == 0 and len(assinaturas_acao[p1]) == 1 and len(assinaturas_acao[p2]) == 1:
                    # Ambas têm 1 ação e é a mesma → mesmo conceito
                    top1 = max(assinaturas_acao[p1], key=assinaturas_acao[p1].get)
                    top2 = max(assinaturas_acao[p2], key=assinaturas_acao[p2].get)
                    if top1 == top2:
                        c1 = self._encontrar_cluster(sub_clusters, p1)
                        c2 = self._encontrar_cluster(sub_clusters, p2)
                        if c1 != c2:
                            sub_clusters[c1] = sub_clusters[c1] | sub_clusters[c2]
                            del sub_clusters[c2]

            for _, palavras_sub in sub_clusters.items():
                # Usar primeira palavra como chave
                chave = sorted(palavras_sub)[0]
                clusters[chave] = palavras_sub

        if not nmi_matriz:
            # Cada palavra é seu próprio conceito
            for p in palavras:
                dist = dict(self._coupling._palavra_acao[p])
                total = sum(dist.values()) or 1
                dist_norm = {a: c / total for a, c in dist.items()}
                c = Conceito({p}, dist_norm, nivel=1)
                self._conceitos.append(c)
                self._indice_palavra_conceito[p] = c
            return self._conceitos

        # Threshold entrópico: 75º percentil das NMIs (mais restritivo
        # que mediana — só agrupa palavras realmente similares)
        nmis = sorted(nmi_matriz.values())
        threshold = nmis[len(nmis) * 3 // 4] if len(nmis) >= 4 else nmis[-1]

        # Union-Find para agrupar palavras
        clusters: Dict[str, Set[str]] = {p: {p} for p in palavras_com_sig}

        for (p1, p2), nmi in nmi_matriz.items():
            if nmi > threshold:
                c1 = self._encontrar_cluster(clusters, p1)
                c2 = self._encontrar_cluster(clusters, p2)
                if c1 != c2:
                    clusters[c1] = clusters[c1] | clusters[c2]
                    del clusters[c2]

        # Criar Conceitos a partir dos clusters
        self._conceitos = []
        self._indice_palavra_conceito = {}

        for _, palavras_set in clusters.items():
            # Agregar distribuição P(acao|conceito)
            dist_agregada: Dict[str, int] = defaultdict(int)
            for p in palavras_set:
                dist = self._coupling._palavra_acao.get(p, {})
                for acao, count in dist.items():
                    dist_agregada[acao] += count

            total = sum(dist_agregada.values()) or 1
            dist_norm = {a: c / total for a, c in dist_agregada.items()}

            conceito = Conceito(palavras_set, dist_norm, nivel=1)
            self._conceitos.append(conceito)

            for p in palavras_set:
                self._indice_palavra_conceito[p] = conceito

        # Palavras sem assinatura: atribuir ao conceito da palavra mais similar
        for p in palavras:
            if p not in self._indice_palavra_conceito:
                dist = dict(self._coupling._palavra_acao.get(p, {}))
                total = sum(dist.values()) or 1
                dist_norm = {a: c / total for a, c in dist.items()}
                conceito = Conceito({p}, dist_norm, nivel=1)
                self._conceitos.append(conceito)
                self._indice_palavra_conceito[p] = conceito

        return self._conceitos

    @staticmethod
    def _encontrar_cluster(clusters: Dict[str, Set[str]], palavra: str) -> str:
        for chave, palavras in clusters.items():
            if palavra in palavras:
                return chave
        return palavra

    # ═══════════════════════════════════════════════════════════════
    # 2. CONSTRUIR HIERARQUIA — conceitos de conceitos
    # ═══════════════════════════════════════════════════════════════

    def construir_hierarquia(self, n_niveis: int = 3) -> Dict[int, List[Conceito]]:
        """Constrói hierarquia de abstração com n níveis.

        Nível 1: Conceitos (clusters de palavras)
        Nível 2: Temas (clusters de conceitos)
        Nível 3: Domínios (clusters de temas)

        Cada nível agrupa o anterior por NMI das distribuições.

        Returns:
            dict {nivel: [Conceito, ...]}
        """
        if not self._conceitos:
            self.detectar_conceitos()

        self._hierarquia = {1: list(self._conceitos)}

        nivel_atual = 1
        conceitos_atual = list(self._conceitos)

        while nivel_atual < n_niveis and len(conceitos_atual) > 1:
            nivel_atual += 1
            conceitos_prox = self._agrupar_conceitos(conceitos_atual, nivel_atual)
            self._hierarquia[nivel_atual] = conceitos_prox
            conceitos_atual = conceitos_prox

        self._construido = True
        return self._hierarquia

    def _agrupar_conceitos(self, conceitos: List[Conceito],
                           nivel: int) -> List[Conceito]:
        """Agrupa conceitos em conceitos de nível superior."""
        if len(conceitos) <= 1:
            return conceitos

        # Calcular NMI entre distribuições de conceitos
        nmi_matriz: Dict[Tuple[int, int], float] = {}

        for i, c1 in enumerate(conceitos):
            for j, c2 in enumerate(conceitos):
                if i < j:
                    # NMI entre distribuições (converter para assinaturas)
                    sig1 = {a: int(v * 1000) for a, v in c1.distribuicao.items()}
                    sig2 = {a: int(v * 1000) for a, v in c2.distribuicao.items()}
                    if sig1 and sig2:
                        nmi = self._coupling._nmi(sig1, sig2)
                    else:
                        nmi = 0.0
                    nmi_matriz[(c1.id, c2.id)] = nmi

        if not nmi_matriz:
            return conceitos

        # Threshold entrópico
        nmis = sorted(nmi_matriz.values())
        threshold = nmis[len(nmis) // 2]

        # Union-Find
        clusters: Dict[int, Set[int]] = {c.id: {c.id} for c in conceitos}
        conceito_por_id = {c.id: c for c in conceitos}

        for (id1, id2), nmi in nmi_matriz.items():
            if nmi > threshold:
                cl1 = self._encontrar_cluster_id(clusters, id1)
                cl2 = self._encontrar_cluster_id(clusters, id2)
                if cl1 != cl2:
                    clusters[cl1] = clusters[cl1] | clusters[cl2]
                    del clusters[cl2]

        # Criar conceitos de nível superior
        conceitos_superiores = []
        for _, ids in clusters.items():
            # Agregar palavras e distribuições
            todas_palavras: Set[str] = set()
            dist_agregada: Dict[str, int] = defaultdict(int)

            for cid in ids:
                c = conceito_por_id[cid]
                todas_palavras |= c.palavras
                for a, v in c.distribuicao.items():
                    dist_agregada[a] += int(v * 1000)

            total = sum(dist_agregada.values()) or 1
            dist_norm = {a: c / total for a, c in dist_agregada.items()}

            conceito_sup = Conceito(todas_palavras, dist_norm, nivel=nivel)

            # Adicionar filhos
            for cid in ids:
                conceito_sup.filhos.append(conceito_por_id[cid])

            conceitos_superiores.append(conceito_sup)

        return conceitos_superiores

    @staticmethod
    def _encontrar_cluster_id(clusters: Dict[int, Set[int]], cid: int) -> int:
        for chave, ids in clusters.items():
            if cid in ids:
                return chave
        return cid

    # ═══════════════════════════════════════════════════════════════
    # 3. ABSTRAIR — converter texto em conceitos
    # ═══════════════════════════════════════════════════════════════

    def abstrair(self, texto: str) -> Dict[str, Any]:
        """Converte texto em representação conceitual.

        Cada palavra do texto é mapeada para seu conceito.
        O resultado é uma lista de conceitos + distribuição agregada.

        Returns:
            dict com 'conceitos' (lista de nomes), 'distribuicao',
            'palavras_desconhecidas', 'cobertura'
        """
        if not self._construido:
            self.construir_hierarquia()

        palavras = re.findall(r'[a-zà-ÿ0-9]{2,}', texto.lower())

        conceitos_encontrados: List[str] = []
        palavras_conhecidas: List[str] = []
        palavras_desconhecidas: List[str] = []
        dist_agregada: Dict[str, float] = defaultdict(float)

        for p in palavras:
            conceito = self._indice_palavra_conceito.get(p)
            if conceito:
                conceitos_encontrados.append(conceito.nome)
                palavras_conhecidas.append(p)
                for a, v in conceito.distribuicao.items():
                    dist_agregada[a] += v
            else:
                # Palavra nova: tentar generalizar
                conceito_gen = self.generalizar(p)
                if conceito_gen:
                    conceitos_encontrados.append(conceito_gen.nome)
                    palavras_conhecidas.append(p)
                    for a, v in conceito_gen.distribuicao.items():
                        dist_agregada[a] += v
                else:
                    palavras_desconhecidas.append(p)

        # Normalizar distribuição
        total = sum(dist_agregada.values())
        if total > 0:
            dist_norm = {a: v / total for a, v in dist_agregada.items()}
        else:
            dist_norm = {}

        cobertura = len(palavras_conhecidas) / max(len(palavras), 1)

        return {
            'texto': texto,
            'conceitos': conceitos_encontrados,
            'n_conceitos': len(set(conceitos_encontrados)),
            'distribuicao': dict(sorted(
                dist_norm.items(), key=lambda x: -x[1]
            )[:5]),
            'palavras_conhecidas': palavras_conhecidas,
            'palavras_desconhecidas': palavras_desconhecidas,
            'cobertura': round(cobertura, 4),
        }

    # ═══════════════════════════════════════════════════════════════
    # 4. DECIDIR EM CONCEITO — generaliza para palavras novas
    # ═══════════════════════════════════════════════════════════════

    def decidir_em_conceito(self, texto: str) -> Tuple[str, float]:
        """Decide a ação via conceitos (não tokens).

        Vantagem: generaliza para palavras nunca vistas. Se "fabrique"
        não está no vocabulário mas é similar a "criar/gerar/fazer"
        (mesmo conceito), herda a distribuição do conceito.

        Returns:
            (acao, confianca)
        """
        abstracao = self.abstrair(texto)
        dist = abstracao['distribuicao']

        if not dist:
            # Fallback: decidir via coupling normal
            return self._coupling.decidir(texto, (None, 0.0))

        melhor = max(dist, key=dist.get)
        conf = dist[melhor]

        return melhor, conf

    # ═══════════════════════════════════════════════════════════════
    # 5. GENERALIZAR — atribuir palavra nova a conceito
    # ═══════════════════════════════════════════════════════════════

    def generalizar(self, palavra_nova: str) -> Optional[Conceito]:
        """Atribui uma palavra nova ao conceito mais próximo.

        Usa NMI entre a assinatura da palavra nova e as assinaturas
        das palavras conhecidas. A palavra nova herda a distribuição
        do conceito mais próximo.

        Returns:
            Conceito mais próximo, ou None se não há dados.
        """
        if not self._conceitos:
            return None

        # Se a palavra já está no índice, retornar seu conceito
        if palavra_nova in self._indice_palavra_conceito:
            return self._indice_palavra_conceito[palavra_nova]

        # Calcular assinatura da palavra nova
        sig_nova = self._coupling._assinatura_palavra(palavra_nova)

        if sig_nova:
            # NMI direta com cada conceito
            melhor_conceito = None
            melhor_nmi = -1

            for conceito in self._conceitos:
                # Assinatura do conceito = agregada
                sig_conceito = {
                    a: int(v * 1000) for a, v in conceito.distribuicao.items()
                }
                if sig_conceito:
                    nmi = self._coupling._nmi(sig_nova, sig_conceito)
                    if nmi > melhor_nmi:
                        melhor_nmi = nmi
                        melhor_conceito = conceito

            if melhor_conceito and melhor_nmi > 0.01:
                return melhor_conceito

        # Fallback: similaridade por features sublexicais
        # (bigramas, trigramas compartilhados)
        melhor_conceito = None
        melhor_sim = -1

        for palavra_conhecida, conceito in self._indice_palavra_conceito.items():
            # Similaridade por bigramas compartilhados
            big_nova = set(palavra_nova[i:i+2] for i in range(len(palavra_nova) - 1))
            big_conh = set(palavra_conhecida[i:i+2] for i in range(len(palavra_conhecida) - 1))

            if big_nova and big_conh:
                inter = len(big_nova & big_conh)
                uniao = len(big_nova | big_conh)
                sim = inter / uniao if uniao > 0 else 0

                if sim > melhor_sim:
                    melhor_sim = sim
                    melhor_conceito = conceito

        if melhor_conceito and melhor_sim > 0.2:
            return melhor_conceito

        return None

    # ═══════════════════════════════════════════════════════════════
    # ANÁLISE
    # ═══════════════════════════════════════════════════════════════

    def obter_conceito(self, palavra: str) -> Optional[Conceito]:
        """Retorna o conceito de uma palavra."""
        if not self._construido:
            self.construir_hierarquia()
        return self._indice_palavra_conceito.get(palavra)

    def listar_conceitos(self, nivel: int = 1) -> List[Conceito]:
        """Lista conceitos de um nível específico."""
        if not self._construido:
            self.construir_hierarquia()
        return self._hierarquia.get(nivel, [])

    def profundidade_hierarquia(self) -> int:
        """Retorna o número de níveis da hierarquia."""
        if not self._construido:
            return 0
        return max(self._hierarquia.keys()) if self._hierarquia else 0

    def estatisticas(self) -> Dict[str, Any]:
        """Estatísticas da abstração."""
        if not self._construido:
            self.construir_hierarquia()

        n_palavras_total = sum(len(c.palavras) for c in self._conceitos)
        tamanho_medio = n_palavras_total / max(len(self._conceitos), 1)

        return {
            'n_conceitos': len(self._conceitos),
            'n_palavras_total': n_palavras_total,
            'tamanho_medio_conceito': round(tamanho_medio, 2),
            'profundidade': self.profundidade_hierarquia(),
            'niveis': {
                n: len(conceitos) for n, conceitos in self._hierarquia.items()
            },
            'conceitos_top': [
                c.estatisticas() for c in
                sorted(self._conceitos, key=lambda x: -len(x.palavras))[:5]
            ],
        }
