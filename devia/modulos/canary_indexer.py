"""modulos.canary_indexer — Indice de scripts do Canary."""
import os
from pathlib import Path


class CanaryIndexer:
    def __init__(self, base_dir=None):
        self._base = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent.parent / 'server'
        self._indice = {}

    def indexar(self, sub_dir='data-otservbr-global'):
        caminho = self._base / sub_dir
        if not caminho.exists():
            return 0
        count = 0
        for root, dirs, files in os.walk(caminho):
            for f in files:
                if f.endswith('.lua'):
                    fp = os.path.join(root, f)
                    self._indice[f] = fp
                    count += 1
        return count

    def buscar(self, nome):
        return self._indice.get(nome)
