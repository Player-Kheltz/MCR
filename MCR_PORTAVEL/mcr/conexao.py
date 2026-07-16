"""conexao.py — Pontes entre tópicos Markov.

Princípio MCR:
  Dados dois tópicos (cadeias Markov treinadas separadamente),
  encontra a palavra-ponte que maximiza: divergência × especificidade × profundidade.

Uso:
  c = MCRConexao()
  ponte = c.conectar(mk_npc, mk_monstro)
  → palavra que melhor conecta os dois domínios
"""
import math
from collections import Counter
from typing import Dict, List, Tuple, Optional


class MCRConexao:
    """Encontra pontes entre tópicos Markov independentes."""

    def conectar(self, mk_a, mk_b, topico_a: str = '', topico_b: str = '') -> Optional[str]:
        """Encontra a melhor palavra-ponte entre dois tópicos.

        Retorna a palavra que maximiza:
          divergência × especificidade × profundidade
        """
        # Palavras que aparecem em AMBOS os tópicos
        palavras_a = set()
        palavras_b = set()
        for est in mk_a.transicoes:
            palavras_a.update(mk_a.transicoes[est].keys())
        for est in mk_b.transicoes:
            palavras_b.update(mk_b.transicoes[est].keys())
        comuns = palavras_a & palavras_b
        if not comuns:
            return None

        # Total de transições em cada tópico
        total_a = mk_a.total or 1
        total_b = mk_b.total or 1

        melhor = None
        melhor_score = 0

        for palavra in comuns:
            freq_a = sum(
                c for est in mk_a.transicoes
                for p, c in mk_a.transicoes[est].items() if p == palavra)
            freq_b = sum(
                c for est in mk_b.transicoes
                for p, c in mk_b.transicoes[est].items() if p == palavra)

            # Especificidade: quao rara é a palavra no repertorio
            espec = 1.0 - (freq_a / total_a + freq_b / total_b) / 2

            # Divergência: quao diferentes sao as distribuições
            # da palavra nos dois tópicos
            trans_a = Counter()
            trans_b = Counter()
            for est in mk_a.transicoes:
                if palavra in mk_a.transicoes[est]:
                    trans_a[est] += mk_a.transicoes[est][palavra]
            for est in mk_b.transicoes:
                if palavra in mk_b.transicoes[est]:
                    trans_b[est] += mk_b.transicoes[est][palavra]
            uniao = set(trans_a.keys()) | set(trans_b.keys())
            if not uniao:
                div = 0.0
            else:
                div = len(trans_a.keys() ^ trans_b.keys()) / len(uniao)

            score = espec * 2 + div * 1
            if score > melhor_score:
                melhor_score = score
                melhor = palavra

        return melhor

    def estatisticas(self) -> Dict:
        return {'tipo': 'ponte_otima'}
