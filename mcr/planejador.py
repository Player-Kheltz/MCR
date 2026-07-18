"""mcr.planejador — Planejamento: MCR planeja antes de agir.

O MCR simula múltiplos futuros possíveis e escolhe o plano de ação
com maior valor esperado segundo a Equação 5D. É como MCTS (Monte
Carlo Tree Search) mas markoviano e com 5D como função de valor.

Pilar 5: fecha o loop — planejar → executar → observar → replanejar.

5 capacidades:
1. Simular — dado estado + ação, prever próximos N estados (Markov)
2. Planejar — busca em árvore sobre sequências de ações, escolhe melhor
3. Avaliar plano — score de um plano via Equação 5D
4. Replanificar — adapta plano quando estado muda inesperadamente
5. Heurística — poda por NMI/entropia (estados de baixa informação)

Tudo Markov + entropia + 5D. Zero GPU, zero dependências.
"""
import math
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Optional, Any

try:
    from mcr.equacao_mcr import avaliar_5d
except ImportError:
    from equacao_mcr import avaliar_5d


class Planejador:
    """MCR que planeja antes de agir.

    Simula futuros possíveis via transições markovianas e avalia
    cada caminho com a Equação 5D. Escolhe o plano com maior valor
    esperado.

    Uso:
        plan = Planejador(coupling)
        plano = plan.planejar("criar monstro dragao", profundidade=3)
        # plano = {acoes: [criar, gerar, ...], score: 0.85, ...}
    """

    def __init__(self, coupling, max_acoes: int = 8):
        self._coupling = coupling
        self._max_acoes = max_acoes  # número máximo de ações a considerar
        self._cache_planos: Dict[Tuple[str, int], Dict] = {}

    # ═══════════════════════════════════════════════════════════════
    # 1. SIMULAR — prever próximos N estados
    # ═══════════════════════════════════════════════════════════════

    def simular(self, estado: str, acao: str,
                n_passos: int = 3) -> List[Dict[str, Any]]:
        """Simula o que acontece se ação for tomada no estado.

        Usa transições markovianas: P(acao_t+1 | acao_t).
        A cada passo, prevê a próxima ação mais provável e sua confiança.

        Returns:
            Lista de {passo, acao, confianca, entropia} para cada passo.
        """
        trajetoria = []
        acao_atual = acao
        estado_atual = estado
        conf_anterior = 0.0

        for passo in range(n_passos):
            # Prever próxima ação via decidir
            pred, conf = self._coupling.decidir(
                estado_atual, (acao_atual, conf_anterior)
            )

            # Entropia da distribuição de ações possíveis
            dist = self._dist_acoes_estado(estado_atual)
            h = self._entropia_dist(dist)

            trajetoria.append({
                'passo': passo + 1,
                'acao': pred,
                'confianca': round(conf, 4),
                'entropia': round(h, 4),
                'estado': estado_atual[:50],
            })

            # Atualizar estado: adicionar ação à sequência
            estado_atual = estado_atual + ' ' + pred
            acao_atual = pred
            conf_anterior = conf

        return trajetoria

    def _dist_acoes_estado(self, estado: str) -> Dict[str, float]:
        """Distribuição de ações para um estado (via decidir interno)."""
        # Usar _dist_palavras + _dist_features para obter distribuição
        dist_palavras = self._coupling._dist_palavras(estado)
        if dist_palavras:
            total = sum(dist_palavras.values()) or 1.0
            return {a: v / total for a, v in dist_palavras.items()}

        # Fallback: distribuição uniforme das ações conhecidas
        acoes = list(self._coupling._freq_acao.keys())
        if not acoes:
            return {'responder': 1.0}
        p = 1.0 / len(acoes)
        return {a: p for a in acoes}

    # ═══════════════════════════════════════════════════════════════
    # 2. PLANEJAR — busca em árvore sobre sequências de ações
    # ═══════════════════════════════════════════════════════════════

    def planejar(self, estado: str, profundidade: int = 3,
                 top_k: int = 3) -> Dict[str, Any]:
        """Planeja a melhor sequência de ações.

        Busca em árvore: a cada nível, expande top_k ações mais prováveis.
        Avalia cada caminho completo com Equação 5D.
        Retorna o caminho com maior score.

        Args:
            estado: estado inicial (input do usuário)
            profundidade: número de passos a planejar
            top_k: ações a considerar por passo (beam width)

        Returns:
            dict com 'plano' (lista de ações), 'score', 'alternativas'
        """
        # Obter ações candidatas iniciais
        candidatos_iniciais = self._acoes_candidatas(estado, top_k)

        if not candidatos_iniciais:
            return {
                'plano': [],
                'score': 0.0,
                'alternativas': [],
                'estado_inicial': estado,
                'profundidade': profundidade,
            }

        # Busca em árvore (beam search markoviana)
        caminhos = [(acao, conf) for acao, conf in candidatos_iniciais]
        todos_caminhos = []

        for profundidade_atual in range(profundidade):
            novos_caminhos = []

            for caminho in caminhos:
                # caminho = lista de (acao, conf) até agora
                acoes_seq = [a for a, _ in caminho] if isinstance(caminho, list) else [caminho[0]]
                estado_sim = estado + ' ' + ' '.join(acoes_seq)

                if profundidade_atual < profundidade - 1:
                    # Expandir: obter próximas ações candidatas
                    proximos = self._acoes_candidatas(estado_sim, top_k)
                    for prox_acao, prox_conf in proximos:
                        novo_caminho = list(caminho) if isinstance(caminho, list) else [caminho]
                        novo_caminho.append((prox_acao, prox_conf))
                        novos_caminhos.append(novo_caminho)
                else:
                    # Folha: caminho completo
                    todos_caminhos.append(
                        caminho if isinstance(caminho, list) else [caminho]
                    )

            if novos_caminhos:
                # Podar: manter apenas top_k caminhos por score parcial
                novos_caminhos.sort(
                    key=lambda c: sum(conf for _, conf in c) / len(c),
                    reverse=True
                )
                caminhos = novos_caminhos[:top_k * 2]
            elif not todos_caminhos:
                # Caminhos curtos (não conseguiu expandir)
                for c in caminhos:
                    todos_caminhos.append(
                        c if isinstance(c, list) else [c]
                    )

        # Avaliar todos os caminhos completos com 5D
        melhores = []
        for caminho in todos_caminhos:
            score = self.avaliar_plano(estado, caminho)
            acoes = [a for a, _ in caminho]
            melhores.append({
                'acoes': acoes,
                'score': round(score, 4),
                'confiancas': [round(c, 4) for _, c in caminho],
            })

        melhores.sort(key=lambda x: -x['score'])

        # Melhor plano
        melhor = melhores[0] if melhores else {'acoes': [], 'score': 0.0}

        return {
            'plano': melhor['acoes'],
            'score': melhor['score'],
            'confiancas': melhor.get('confiancas', []),
            'alternativas': melhores[1:3],  # top 3 alternativas
            'estado_inicial': estado,
            'profundidade': profundidade,
            'n_caminhos_avaliados': len(melhores),
        }

    # ═══════════════════════════════════════════════════════════════
    # 3. AVALIAR PLANO — score via Equação 5D
    # ═══════════════════════════════════════════════════════════════

    def avaliar_plano(self, estado_inicial: str,
                      caminho: List[Tuple[str, float]]) -> float:
        """Avalia um plano (sequência de ações) com Equação 5D.

        5 dimensões:
        - CERTEZA: confiança média das ações do plano
        - COMPLETUDE: fração de passos com confiança > threshold
        - INFORMACAO: entropia média das decisões (diversidade)
        - ESTABILIDADE: variância baixa = plano consistente
        - EFICIENCIA: 1/log2(n_acoes+1) (recompensa simplicidade)
        """
        if not caminho:
            return 0.0

        confiancas = [c for _, c in caminho]
        acoes = [a for a, _ in caminho]

        # CERTEZA: confiança média
        certeza = sum(confiancas) / len(confiancas) if confiancas else 0.0

        # COMPLETUDE: fração com confiança > 0.3
        completude = sum(1 for c in confiancas if c > 0.3) / len(confiancas)

        # INFORMACAO: entropia da distribuição de ações no plano
        dist_acoes = defaultdict(int)
        for a in acoes:
            dist_acoes[a] += 1
        informacao = self._entropia_dist(dict(dist_acoes))

        # ESTABILIDADE: baixa variância = estável
        if len(confiancas) > 1:
            media = sum(confiancas) / len(confiancas)
            var = sum((c - media) ** 2 for c in confiancas) / len(confiancas)
            dp = math.sqrt(var)
            estabilidade = math.exp(-dp * 2)  # dp=0 -> 1, dp=0.5 -> 0.37
        else:
            estabilidade = 1.0

        # EFICIENCIA: planos curtos são mais eficientes
        eficiencia = 1.0 / math.log2(max(len(acoes) + 1, 2))

        return avaliar_5d(certeza, completude, informacao,
                          estabilidade, eficiencia)

    # ═══════════════════════════════════════════════════════════════
    # 4. REPLANIFICAR — adapta plano quando estado muda
    # ═══════════════════════════════════════════════════════════════

    def replanificar(self, estado_anterior: str,
                     estado_novo: str,
                     plano_anterior: List[str],
                     profundidade: int = 3) -> Dict[str, Any]:
        """Replaneja quando o estado muda inesperadamente.

        Compara o plano anterior com o novo estado. Se o plano
        ainda é válido (ações compatíveis), mantém. Senão, replaneja.

        Returns:
            dict com 'novo_plano', 'mudou', 'razao'
        """
        # Verificar se o plano anterior ainda é válido
        acoes_novo_estado = self._acoes_candidatas(estado_novo, top_k=5)
        acoes_validas = {a for a, _ in acoes_novo_estado}

        # Se a primeira ação do plano anterior ainda é válida
        if plano_anterior and plano_anterior[0] in acoes_validas:
            # Plano parcialmente válido — manter e completar
            novo_plano = self.planejar(estado_novo, profundidade)
            # Verificar sobreposição
            sobreposicao = 0
            for i, a in enumerate(plano_anterior):
                if i < len(novo_plano['plano']) and novo_plano['plano'][i] == a:
                    sobreposicao += 1
                else:
                    break

            return {
                'novo_plano': novo_plano['plano'],
                'score': novo_plano['score'],
                'mudou': sobreposicao < len(plano_anterior) / 2,
                'sobreposicao': sobreposicao,
                'razao': f'plano_anterior {sobreposicao}/{len(plano_anterior)} acoes preservadas',
            }
        else:
            # Plano completamente inválido — replanejar do zero
            novo_plano = self.planejar(estado_novo, profundidade)
            return {
                'novo_plano': novo_plano['plano'],
                'score': novo_plano['score'],
                'mudou': True,
                'sobreposicao': 0,
                'razao': 'estado mudou significativamente — replanejamento completo',
            }

    # ═══════════════════════════════════════════════════════════════
    # 5. HEURÍSTICA — poda por NMI/entropia
    # ═══════════════════════════════════════════════════════════════

    def heuristicas(self, estado: str) -> Dict[str, float]:
        """Calcula heurísticas do estado para guiar a busca.

        - diversidade: entropia das ações possíveis (alta = explorar)
        - familiaridade: cobertura de features (alta = explotar)
        - coerncia: NMI média entre palavras do estado
        """
        palavras = estado.lower().split()
        dist = self._dist_acoes_estado(estado)
        h = self._entropia_dist(dist)

        # Familiaridade: fração de palavras conhecidas
        conhecidas = sum(1 for p in palavras if p in self._coupling._palavra_acao)
        familiaridade = conhecidas / max(len(palavras), 1)

        # Coerência: NMI média entre pares de palavras
        nmi_sum = 0.0
        n_pares = 0
        for i in range(len(palavras)):
            for j in range(i + 1, min(i + 3, len(palavras))):
                sig_i = self._coupling._assinatura_palavra(palavras[i])
                sig_j = self._coupling._assinatura_palavra(palavras[j])
                if sig_i and sig_j:
                    nmi_sum += self._coupling._nmi(sig_i, sig_j)
                    n_pares += 1
        coerencia = nmi_sum / max(n_pares, 1)

        return {
            'diversidade': round(h, 4),
            'familiaridade': round(familiaridade, 4),
            'coerencia': round(coerencia, 4),
        }

    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _acoes_candidatas(self, estado: str,
                          top_k: int) -> List[Tuple[str, float]]:
        """Retorna as top_k ações mais prováveis para o estado.

        Usa decidir() internamente mas retorna múltiplas opções
        em vez de apenas a melhor.
        """
        # Obter distribuição combinada via decidir
        acao, conf = self._coupling.decidir(estado, (None, 0.0))

        # Obter distribuição mais ampla via _dist_palavras
        dist = self._coupling._dist_palavras(estado)
        if not dist:
            return [(acao, conf)] if acao else []

        total = sum(dist.values()) or 1.0
        candidatos = [(a, c / total) for a, c in dist.items()]
        candidatos.sort(key=lambda x: -x[1])

        return candidatos[:top_k]

    @staticmethod
    def _entropia_dist(dist: Dict[str, float]) -> float:
        """Entropia Shannon normalizada [0, 1]."""
        total = sum(dist.values()) if dist else 0
        if total <= 0 or len(dist) <= 1:
            return 0.0
        h = 0.0
        for v in dist.values():
            pr = v / total
            if pr > 0:
                h -= pr * math.log2(pr)
        max_h = math.log2(len(dist))
        return h / max_h if max_h > 0 else 0.0

    # ═══════════════════════════════════════════════════════════════
    # ESTATÍSTICAS
    # ═══════════════════════════════════════════════════════════════

    def estatisticas(self) -> Dict[str, Any]:
        """Estatísticas do planejador."""
        return {
            'cache_planos': len(self._cache_planos),
            'max_acoes': self._max_acoes,
            'vocabulario': len(self._coupling._palavra_acao),
            'acoes_conhecidas': len(self._coupling._freq_acao),
        }
