"""mcr.teoria_da_mente — Teoria da mente: modelar outros agentes.

O MCR agora modela o que OUTROS agentes sabem, acreditam e fariam.
É a capacidade cognitiva de atribuir estados mentais (crenças,
desejos, intenções) a outros — fundamental para colaboração,
negociação e previsão de comportamento.

Base: Markov + NMI. Cada "agente" é um MCRCoupling com conhecimento
próprio (subset do mundo). O MCR principal simula esses agentes
para prever suas ações.

Teste clássico de ToM (Sally-Anne):
- Sally coloca bola na cesta. Sai.
- Anne move bola para caixa.
- Sally volta. Onde Sally vai procurar?
- Resposta ToM: cesta (Sally acredita que está lá, mesmo estando na caixa).

5 capacidades:
1. Modelar agente — criar agente simulado com conhecimento próprio
2. Predizer ação — o que o agente faria dado seu conhecimento?
3. Atribuir crenças — o que o agente acredita sobre o mundo?
4. Crença falsa — agente com conhecimento desatualizado/errado
5. Perspectiva — comparar perspectiva do agente vs realidade

Tudo Markov + entropia. Zero GPU, zero dependências.
"""
import math
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Optional, Any

from mcr.coupling import MCRCoupling


class AgenteMental:
    """Um agente simulado com seu próprio conhecimento.

    Cada agente tem seu próprio MCRCoupling (subset do conhecimento
    do mundo). Isso permite simular agentes que sabem menos, sabem
    coisas diferentes, ou têm crenças desatualizadas.
    """

    def __init__(self, nome: str, coupling: MCRCoupling):
        self.nome = nome
        self._coupling = coupling
        # Crenças explícitas (opcional — pode ter conhecimento via coupling)
        self._crencas: Dict[str, str] = {}  # fato -> valor_acreditado
        # Intenções (objetivos)
        self._intencao: Optional[str] = None

    def acredita(self, fato: str, valor: str) -> None:
        """Registra uma crença explícita do agente."""
        self._crencas[fato] = valor

    def obter_crenca(self, fato: str) -> Optional[str]:
        """Retorna o que o agente acredita sobre um fato."""
        return self._crencas.get(fato)

    def definir_intencao(self, intencao: str) -> None:
        """Define a intenção (objetivo) atual do agente."""
        self._intencao = intencao

    @property
    def intencao(self) -> Optional[str]:
        return self._intencao

    @property
    def crenca_count(self) -> int:
        return len(self._crencas)

    def que_acao_faria(self, estado: str) -> Tuple[str, float]:
        """Prediz que ação o agente faria dado o estado.

        Usa o coupling PRÓPRIO do agente (não o do MCR principal).
        """
        return self._coupling.decidir(estado, (None, 0.0))


class TeoriaDaMente:
    """MCR que modela outros agentes (teoria da mente).

    Cria agentes simulados com conhecimento próprio, prediz suas
    ações, atribui crenças, e detecta crenças falsas.

    Uso:
        tom = TeoriaDaMente(coupling_principal)
        sally = tom.criar_agente("sally", corpus_sally)
        acao = tom.predizer_acao(sally, "buscar bola")
        # Sally buscaria na cesta (onde ela acredita que está)
    """

    def __init__(self, coupling: MCRCoupling):
        self._coupling = coupling  # MCR principal (realidade)
        self._agentes: Dict[str, AgenteMental] = {}

    # ═══════════════════════════════════════════════════════════════
    # 1. MODELAR AGENTE — criar agente simulado
    # ═══════════════════════════════════════════════════════════════

    def criar_agente(self, nome: str,
                     corpus: List[Tuple[str, str]] = None,
                     conhecimento_compartilhado: bool = False
                     ) -> AgenteMental:
        """Cria um agente simulado com conhecimento próprio.

        Args:
            nome: identificador do agente
            corpus: lista de (texto, acao) que o agente conhece.
                    Se None e conhecimento_compartilhado=True, usa
                    o corpus do MCR principal.
            conhecimento_compartilhado: se True, agente conhece tudo
                    que o MCR principal conhece.

        Returns:
            AgenteMental instanciado.
        """
        coupling_agente = MCRCoupling()

        if conhecimento_compartilhado and corpus is None:
            # Copiar conhecimento do MCR principal
            for palavra, dist in self._coupling._palavra_acao.items():
                for acao, count in dist.items():
                    coupling_agente._palavra_acao[palavra][acao] = count
            for pa, dist in self._coupling._transicao_palavra.items():
                for pb, count in dist.items():
                    coupling_agente._transicao_palavra[pa][pb] = count
        elif corpus:
            for texto, acao in corpus:
                coupling_agente.alimentar(texto, acao)

        agente = AgenteMental(nome, coupling_agente)
        self._agentes[nome] = agente
        return agente

    def obter_agente(self, nome: str) -> Optional[AgenteMental]:
        """Retorna um agente existente."""
        return self._agentes.get(nome)

    def listar_agentes(self) -> List[str]:
        """Lista nomes de todos os agentes modelados."""
        return list(self._agentes.keys())

    # ═══════════════════════════════════════════════════════════════
    # 2. PREDIZER AÇÃO — o que o agente faria?
    # ═══════════════════════════════════════════════════════════════

    def predizer_acao(self, agente: AgenteMental,
                      estado: str) -> Dict[str, Any]:
        """Prediz que ação o agente faria dado o estado.

        Usa o coupling PRÓPRIO do agente — não o do MCR principal.
        Compara com o que o MCR principal faria (realidade).

        Returns:
            dict com:
            - acao_agente: o que o agente faria
            - confianca_agente: confiança do agente
            - acao_realidade: o que o MCR principal faria
            - confianca_realidade: confiança do MCR principal
            - concordam: se ambos fariam o mesmo
        """
        acao_agente, conf_agente = agente.que_acao_faria(estado)
        acao_realidade, conf_realidade = self._coupling.decidir(
            estado, (None, 0.0)
        )

        return {
            'agente': agente.nome,
            'estado': estado,
            'acao_agente': acao_agente,
            'confianca_agente': round(conf_agente, 4),
            'acao_realidade': acao_realidade,
            'confianca_realidade': round(conf_realidade, 4),
            'concordam': acao_agente == acao_realidade,
            'divergencia': round(
                abs(conf_agente - conf_realidade), 4
            ),
        }

    # ═══════════════════════════════════════════════════════════════
    # 3. ATRIBUIR CRENÇAS — o que o agente acredita?
    # ═══════════════════════════════════════════════════════════════

    def atribuir_crenca(self, agente: AgenteMental,
                        fato: str, valor: str) -> None:
        """Atribui uma crença ao agente.

        "Sally acredita que a bola está na cesta."
        """
        agente.acredita(fato, valor)

    def inferir_crenca(self, agente: AgenteMental,
                       estado: str) -> Dict[str, Any]:
        """Infere o que o agente provavelmente acredita dado seu conhecimento.

        Usa o coupling do agente para determinar que palavras/ações
        ele conhece — isso reflete sua "visão de mundo".

        Returns:
            dict com 'palavras_conhecidas', 'acoes_conhecidas',
            'cobertura_estado', 'visao_de_mundo'
        """
        palavras = estado.lower().split()
        palavras_conhecidas = [
            p for p in palavras if p in agente._coupling._palavra_acao
        ]
        cobertura = len(palavras_conhecidas) / max(len(palavras), 1)

        # Visão de mundo: que ações o agente conhece
        acoes_conhecidas = list(agente._coupling._freq_acao.keys())

        # Crenças explícitas
        crencas = dict(agente._crencas) if agente._crencas else {}

        return {
            'agente': agente.nome,
            'palavras_conhecidas': palavras_conhecidas,
            'palavras_desconhecidas': [
                p for p in palavras if p not in palavras_conhecidas
            ],
            'cobertura': round(cobertura, 4),
            'acoes_conhecidas': acoes_conhecidas,
            'crencas_explicitas': crencas,
            'n_crencas': len(crencas),
        }

    # ═══════════════════════════════════════════════════════════════
    # 4. CRENÇA FALSA — agente com conhecimento errado
    # ═══════════════════════════════════════════════════════════════

    def teste_crenca_falsa(self, agente: AgenteMental,
                           estado: str,
                           realidade: str) -> Dict[str, Any]:
        """Teste de crença falsa (Sally-Anne).

        O agente tem conhecimento desatualizado. O que ele faria?
        E o que a realidade diz?

        Args:
            agente: agente com conhecimento potencialmente errado
            estado: situação atual
            realidade: descrição da realidade (pode diferir do que
                       o agente sabe)

        Returns:
            dict com 'acao_agente', 'acao_realidade', 'tem_crenca_falsa',
            'explicacao'
        """
        # O que o agente faria (com seu conhecimento limitado)
        acao_agente, conf_agente = agente.que_acao_faria(estado)

        # O que o MCR principal faria (com conhecimento completo)
        acao_realidade, conf_realidade = self._coupling.decidir(
            estado, (None, 0.0)
        )

        tem_crenca_falsa = acao_agente != acao_realidade

        # Verificar cobertura do agente vs realidade
        palavras = estado.lower().split()
        cob_agente = sum(
            1 for p in palavras if p in agente._coupling._palavra_acao
        ) / max(len(palavras), 1)

        if tem_crenca_falsa:
            explicacao = (
                f"{agente.nome} agiria '{acao_agente}' (conf={conf_agente:.2f}), "
                f"mas a realidade é '{acao_realidade}' (conf={conf_realidade:.2f}). "
                f"{agente.nome} tem crença falsa — cobertura={cob_agente:.2f}"
            )
        else:
            explicacao = (
                f"{agente.nome} e realidade concordam: '{acao_agente}' "
                f"(conf={conf_agente:.2f}). Sem crença falsa."
            )

        return {
            'agente': agente.nome,
            'estado': estado,
            'realidade': realidade,
            'acao_agente': acao_agente,
            'confianca_agente': round(conf_agente, 4),
            'acao_realidade': acao_realidade,
            'confianca_realidade': round(conf_realidade, 4),
            'tem_crenca_falsa': tem_crenca_falsa,
            'cobertura_agente': round(cob_agente, 4),
            'explicacao': explicacao,
        }

    # ═══════════════════════════════════════════════════════════════
    # 5. PERSPECTIVA — comparar visões de múltiplos agentes
    # ═══════════════════════════════════════════════════════════════

    def comparar_perspectivas(self, estado: str,
                              nomes_agentes: List[str] = None
                              ) -> Dict[str, Any]:
        """Compara como diferentes agentes vêem o mesmo estado.

        "Sally vê X, Anne vê Y, realidade é Z."

        Returns:
            dict com 'perspectivas' (lista), 'consenso', 'divergencia_max'
        """
        if nomes_agentes is None:
            nomes_agentes = list(self._agentes.keys())

        perspectivas = []
        acoes = []

        # Perspectiva da realidade (MCR principal)
        acao_real, conf_real = self._coupling.decidir(estado, (None, 0.0))
        perspectivas.append({
            'agente': 'realidade',
            'acao': acao_real,
            'confianca': round(conf_real, 4),
        })
        acoes.append(acao_real)

        # Perspectiva de cada agente
        for nome in nomes_agentes:
            agente = self._agentes.get(nome)
            if agente is None:
                continue
            acao, conf = agente.que_acao_faria(estado)
            perspectivas.append({
                'agente': nome,
                'acao': acao,
                'confianca': round(conf, 4),
            })
            acoes.append(acao)

        # Consenso: ação mais frequente
        dist_acoes = defaultdict(int)
        for a in acoes:
            dist_acoes[a] += 1
        consenso = max(dist_acoes, key=dist_acoes.get)
        n_concordam = dist_acoes[consenso]
        taxa_consenso = n_concordam / len(acoes) if acoes else 0

        # Divergência máxima: maior diferença de confiança
        confs = [p['confianca'] for p in perspectivas]
        divergencia_max = max(confs) - min(confs) if confs else 0

        return {
            'estado': estado,
            'perspectivas': perspectivas,
            'consenso': consenso,
            'taxa_consenso': round(taxa_consenso, 4),
            'divergencia_max': round(divergencia_max, 4),
            'n_perspectivas': len(perspectivas),
        }

    def predizer_interacao(self, agente_a: AgenteMental,
                           agente_b: AgenteMental,
                           estado: str) -> Dict[str, Any]:
        """Prediz como dois agentes interagiriam dado um estado.

        "Se A fizer X, o que B faria em resposta?"

        Returns:
            dict com 'acao_a', 'acao_b', 'concordam', 'dinamica'
        """
        acao_a, conf_a = agente_a.que_acao_faria(estado)

        # B responde ao estado + ação de A
        estado_b = estado + ' ' + acao_a
        acao_b, conf_b = agente_b.que_acao_faria(estado_b)

        concordam = acao_a == acao_b

        if concordam:
            dinamica = 'cooperacao'
        elif conf_a > 0.5 and conf_b > 0.5:
            dinamica = 'conflito'
        else:
            dinamica = 'independencia'

        return {
            'agente_a': agente_a.nome,
            'agente_b': agente_b.nome,
            'estado': estado,
            'acao_a': acao_a,
            'confianca_a': round(conf_a, 4),
            'acao_b': acao_b,
            'confianca_b': round(conf_b, 4),
            'concordam': concordam,
            'dinamica': dinamica,
        }

    # ═══════════════════════════════════════════════════════════════
    # ESTATÍSTICAS
    # ═══════════════════════════════════════════════════════════════

    def estatisticas(self) -> Dict[str, Any]:
        """Estatísticas da teoria da mente."""
        return {
            'n_agentes': len(self._agentes),
            'agentes': list(self._agentes.keys()),
            'vocabulario_realidade': len(self._coupling._palavra_acao),
        }
