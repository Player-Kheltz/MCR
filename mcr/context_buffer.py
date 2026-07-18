"""ContextBuffer — Buffer temporal com recency weighting.

Mantém um sliding window dos últimos N tokens observados.
Cada token tem peso decrescente por idade: token mais recente = peso 1.0,
mais antigo na janela = peso ~0.1.

Uso:
    buf = ContextBuffer(max_size=128)
    buf.adicionar("criar monstro")
    buf.adicionar("dragao vermelho")
    pesos = buf.obter()  # [("dragao", 1.0), ("vermelho", 0.9), ("criar", 0.7), ("monstro", 0.6)]
"""
from collections import defaultdict
from typing import List, Tuple


class ContextBuffer:

    def __init__(self, max_size: int = 128):
        self._max_size = max_size
        self._tokens: List[str] = []

    def adicionar(self, texto: str) -> None:
        import re
        tokens = re.findall(r'[a-zà-ÿ0-9]{3,}', texto.lower())
        self._tokens.extend(tokens)
        if len(self._tokens) > self._max_size:
            self._tokens = self._tokens[-self._max_size:]

    def obter(self) -> List[Tuple[str, float]]:
        if not self._tokens:
            return []
        n = len(self._tokens)
        pesos = []
        for i, token in enumerate(self._tokens):
            idade = n - 1 - i
            peso = 2.0 ** (-idade / max(n * 0.2, 1))
            pesos.append((token, max(peso, 0.05)))
        return pesos

    def limpar(self) -> None:
        self._tokens = []

    def __len__(self) -> int:
        return len(self._tokens)