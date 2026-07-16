"""hiperesfera.py — Auto-descoberta de dimensões Markov.

Princípio MCR:
  O MCR descobre seus próprios níveis — MCRMetaNivel.auto_expandir()
  Entropia revela quais dimensões são estruturadas (H baixa = útil) vs ruído (H alta).

Dado um conjunto de dados, a hiperesfera testa múltiplas tokenizações e
descobre quais produzem as transições Markov mais estruturadas (menor entropia).
"""
import math
from collections import Counter
from typing import List, Dict, Tuple, Optional


class MCRHiperesfera:
    """Descobre dimensões Markov automaticamente por entropia."""

    def __init__(self):
        self._dimensoes: List[str] = []
        self._entropias: Dict[str, float] = {}

    def descobrir(self, dados, candidatos: Dict[str, callable] = None) -> List[str]:
        """Testa tokenizações candidatas e retorna as melhores dimensões.

        Args:
            dados: qualquer sequência (texto, bytes, lista)
            candidatos: {nome: fn_tokenizar} — se None, usa padrões
        Returns:
            lista de nomes de dimensões ordenadas por entropia (menor primeiro)
        """
        if candidatos is None:
            candidatos = self._candidatos_padrao()

        resultados = {}
        for nome, tokenizar in candidatos.items():
            try:
                tokens = tokenizar(dados)
                if not tokens or len(tokens) < 2:
                    continue
                h = self._entropia_sequencia(tokens)
                resultados[nome] = h
            except Exception:
                pass

        self._dimensoes = sorted(resultados, key=resultados.get)
        self._entropias = resultados
        return self._dimensoes

    def _candidatos_padrao(self) -> Dict[str, callable]:
        """Tokenizações padrão — universal, zero hardcode de domínio."""
        return {
            'byte': lambda d: list(d.encode() if isinstance(d, str) else d),
            'palavra': lambda d: d.split() if isinstance(d, str) else [],
            'token_tipo': lambda d: [
                'L' if c.isalpha() else 'N' if c.isdigit() else 'S'
                for c in (d if isinstance(d, str) else '')
            ] if isinstance(d, str) else [],
            'bigrama': lambda d: [
                d[i:i+2] for i in range(len(d)-1)
            ] if isinstance(d, str) and len(d) > 1 else [],
            'trigrama': lambda d: [
                d[i:i+3] for i in range(len(d)-2)
            ] if isinstance(d, str) and len(d) > 2 else [],
        }

    def _entropia_sequencia(self, tokens: list) -> float:
        """Entropia Shannon normalizada de uma sequência de tokens."""
        if not tokens:
            return 1.0
        c = Counter(tokens)
        n = len(tokens)
        h = 0.0
        for v in c.values():
            p = v / n
            if p > 0: h -= p * math.log2(p)
        max_h = math.log2(max(len(c), 2))
        return h / max_h if max_h > 0 else 1.0

    def melhor_dimensao(self) -> Optional[str]:
        """Retorna a dimensão com menor entropia (mais estruturada)."""
        return self._dimensoes[0] if self._dimensoes else None

    def estatisticas(self) -> Dict:
        return {
            'dimensoes': self._dimensoes[:5],
            'entropias': {k: round(v, 3) for k, v in
                         sorted(self._entropias.items(), key=lambda x: x[1])[:5]},
        }
