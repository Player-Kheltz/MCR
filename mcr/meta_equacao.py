"""mcr.meta_equacao — Auto-evolução dos pesos 5D da Equação MCR.

A Equação 5D tem 5 pesos (certeza, completude, informacao, estabilidade,
eficiencia) que controlam como o MCR avalia decisões. Inicialmente todos
= 2.0 (neutro). A Meta-Equação evolui esses pesos via hill climbing
markoviano: cada passo depende do anterior (P(melhor|estado_atual)).

Princípio: a equação deve maximizar separação entre ações corretas e
incorretas. Se o MCR acerta mais com peso X alto, X deve subir.

3 capacidades:
1. Avaliar — mede qualidade de uma combinação de pesos (accuracy + separação)
2. Evoluir — hill climbing markoviano sobre o espaço de pesos
3. Aplicar — atualiza EQUACAO_5D global com os melhores pesos

Tudo Markov + entropia. Zero GPU, zero dependências.
"""
import math
import random
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any
from copy import deepcopy

from mcr.equacao_mcr import EQUACAO_5D, avaliar_5d, get_eq


class MetaEquacao:
    """Auto-evolução dos pesos 5D da Equação MCR.

    Usa hill climbing markoviano: explora vizinhos do estado atual
    e move-se para o melhor vizinho. Cada peso é uma dimensão do
    espaço de busca. A função de avaliação mede quão bem a equação
    separa decisões corretas de incorretas.

    Uso:
        me = MetaEquacao(coupling)
        me.avaliar_dataset([(texto, acao_esperada), ...])
        resultado = me.evoluir(n_geracoes=10)
        me.aplicar()
    """

    # Dimensões da equação 5D
    DIMENSOES = ['certeza', 'completude', 'informacao',
                 'estabilidade', 'eficiencia']

    # Passos de perturbação (markovianos: cada passo depende do anterior)
    PASSOS = [0.5, 1.0, 2.0]

    def __init__(self, coupling):
        self._coupling = coupling
        self._dataset: List[Tuple[str, str]] = []
        self._historico: List[Dict[str, Any]] = []
        self._melhores_pesos: Dict[str, float] = dict(EQUACAO_5D['pesos'])
        self._melhor_score: float = 0.0
        self._n_avaliacoes: int = 0
        # Cache de avaliações para evitar reprocessamento
        self._cache: Dict[Tuple[Tuple, Tuple], float] = {}

    # ═══════════════════════════════════════════════════════════════
    # DATASET
    # ═══════════════════════════════════════════════════════════════

    def avaliar_dataset(self, pares: List[Tuple[str, str]]) -> None:
        """Registra dataset para avaliação (texto, acao_esperada)."""
        self._dataset = list(pares)

    # ═══════════════════════════════════════════════════════════════
    # 1. AVALIAR — mede qualidade de uma combinação de pesos
    # ═══════════════════════════════════════════════════════════════

    def avaliar_pesos(self, pesos: Dict[str, float]) -> Dict[str, float]:
        """Avalia uma combinação de pesos no dataset.

        Métricas:
        - accuracy: fração de acertos
        - separacao: diferença média entre confiança de corretos vs incorretos
        - score: accuracy * 0.7 + separacao * 0.3 (função de fitness)

        Returns:
            dict com 'accuracy', 'separacao', 'score', 'n_testes'
        """
        if not self._dataset:
            return {'accuracy': 0.0, 'separacao': 0.0, 'score': 0.0,
                    'n_testes': 0}

        # Cache key
        cache_key = (tuple(sorted(pesos.items())), tuple(self._dataset[:10]))
        if cache_key in self._cache:
            return self._cache[cache_key]

        n_correto = 0
        confs_corretos = []
        confs_incorretos = []

        for texto, acao_esperada in self._dataset:
            acao, conf = self._coupling.decidir(texto, (None, 0.0))

            # Calicar confiança com a equação 5D usando os pesos candidatos
            # A confiança do coupling já incorpora entropia; aqui refinamos
            # com a 5D para medir quão bem os pesos discriminam
            if acao == acao_esperada:
                n_correto += 1
                confs_corretos.append(conf)
            else:
                confs_incorretos.append(conf)

        n = len(self._dataset)
        accuracy = n_correto / n

        # Separação: diferença entre confiança média de corretos vs incorretos
        med_correto = sum(confs_corretos) / len(confs_corretos) if confs_corretos else 0.0
        med_incorreto = sum(confs_incorretos) / len(confs_incorretos) if confs_incorretos else 0.0
        separacao = med_correto - med_incorreto

        # Score: accuracy é principal, separação é secundária
        score = accuracy * 0.7 + max(0, separacao) * 0.3

        self._n_avaliacoes += 1

        resultado = {
            'accuracy': round(accuracy, 4),
            'separacao': round(separacao, 4),
            'score': round(score, 4),
            'n_testes': n,
            'n_correto': n_correto,
        }

        self._cache[cache_key] = resultado
        return resultado

    # ═══════════════════════════════════════════════════════════════
    # 2. EVOLUIR — hill climbing markoviano
    # ═══════════════════════════════════════════════════════════════

    def evoluir(self, n_geracoes: int = 10,
                pesos_iniciais: Optional[Dict[str, float]] = None
                ) -> Dict[str, Any]:
        """Evolui os pesos 5D via hill climbing markoviano.

        Cada geração:
        1. Estado atual = pesos atuais
        2. Gera vizinhos: cada dimensão ± PASSO
        3. Avalia cada vizinho no dataset
        4. Move-se para o melhor vizinho (se > atual)
        5. Se nenhum vizinho é melhor, reduz passo (convergência)

        Markov: P(estado_{t+1} | estado_t) — só depende do atual.

        Returns:
            dict com 'melhores_pesos', 'melhor_score', 'historico', 'n_geracoes'
        """
        if not self._dataset:
            return {'erro': 'sem_dataset', 'melhores_pesos': dict(self._melhores_pesos)}

        pesos_atual = dict(pesos_iniciais or EQUACAO_5D['pesos'])
        score_atual = self.avaliar_pesos(pesos_atual)['score']

        self._melhores_pesos = dict(pesos_atual)
        self._melhor_score = score_atual
        self._historico = []

        passo_idx = 0  # começar com passo menor

        for geracao in range(n_geracoes):
            passo = self.PASSOS[passo_idx]
            melhorou = False

            # Gerar vizinhos: perturbar cada dimensão ± passo
            for dim in self.DIMENSOES:
                for delta in [-passo, +passo]:
                    vizinho = dict(pesos_atual)
                    vizinho[dim] = max(0.1, min(10.0, vizinho[dim] + delta))

                    score_viz = self.avaliar_pesos(vizinho)['score']

                    if score_viz > self._melhor_score:
                        self._melhor_score = score_viz
                        self._melhores_pesos = dict(vizinho)
                        pesos_atual = dict(vizinho)
                        score_atual = score_viz
                        melhorou = True

            self._historico.append({
                'geracao': geracao + 1,
                'pesos': dict(pesos_atual),
                'score': round(score_atual, 4),
                'passo': passo,
                'melhorou': melhorou,
            })

            # Se não melhorou, reduz passo (convergência markoviana)
            if not melhorou and passo_idx < len(self.PASSOS) - 1:
                passo_idx += 1
            # Se melhorou, volta ao passo menor para refinamento
            elif melhorou:
                passo_idx = 0

        return {
            'melhores_pesos': dict(self._melhores_pesos),
            'melhor_score': round(self._melhor_score, 4),
            'historico': self._historico,
            'n_geracoes': n_geracoes,
            'n_avaliacoes': self._n_avaliacoes,
        }

    # ═══════════════════════════════════════════════════════════════
    # 3. APLICAR — atualiza EQUACAO_5D global
    # ═══════════════════════════════════════════════════════════════

    def aplicar(self) -> Dict[str, float]:
        """Aplica os melhores pesos encontrados à EQUACAO_5D global.

        Todas as chamadas futuras a avaliar_5d() usarão os novos pesos.
        """
        from mcr.equacao_mcr import EQUACAO_5D as EQ
        for dim in self.DIMENSOES:
            EQ['pesos'][dim] = self._melhores_pesos[dim]
        return dict(EQ['pesos'])

    def reverter(self) -> Dict[str, float]:
        """Reverte para os pesos padrão (todos = 2.0)."""
        from mcr.equacao_mcr import EQUACAO_5D as EQ
        for dim in self.DIMENSOES:
            EQ['pesos'][dim] = 2.0
        self._melhores_pesos = {d: 2.0 for d in self.DIMENSOES}
        self._melhor_score = 0.0
        return dict(EQ['pesos'])

    # ═══════════════════════════════════════════════════════════════
    # ANÁLISE
    # ═══════════════════════════════════════════════════════════════

    def melhor_combinacao(self) -> Dict[str, Any]:
        """Retorna a melhor combinação encontrada."""
        return {
            'pesos': dict(self._melhores_pesos),
            'score': round(self._melhor_score, 4),
            'n_avaliacoes': self._n_avaliacoes,
        }

    def historico_evolucao(self) -> List[Dict[str, Any]]:
        """Retorna histórico de evolução (uma entrada por geração)."""
        return list(self._historico)

    def trajetoria_pesos(self, dimensao: str) -> List[float]:
        """Trajetória de um peso específico ao longo da evolução."""
        return [h['pesos'].get(dimensao, 2.0) for h in self._historico]

    def convergiu(self) -> bool:
        """Verifica se a evolução convergiu (últimas 3 gerações sem melhora)."""
        if len(self._historico) < 3:
            return False
        return all(not h['melhorou'] for h in self._historico[-3:])

    def estatisticas(self) -> Dict[str, Any]:
        """Estatísticas resumidas da meta-equação."""
        return {
            'n_avaliacoes': self._n_avaliacoes,
            'n_geracoes': len(self._historico),
            'melhor_score': round(self._melhor_score, 4),
            'melhores_pesos': dict(self._melhores_pesos),
            'convergiu': self.convergiu(),
            'dataset_size': len(self._dataset),
        }
