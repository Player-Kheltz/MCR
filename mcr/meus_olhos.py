"""
mcr.meus_olhos — Discriminador MCR: avalia qualidade de sprites gerados.

Treina MCR com sprites reais (nível papel: B, L, F).
Avalia sprites gerados via P(token | ctx) normalizado.
Score > 0.5 = aceitável. Score < 0.5 = rejeitar.
"""
import math
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional


def _papel(tok: str) -> str:
    if tok == 'F': return 'F'
    if tok == 'B': return 'B'
    if tok.startswith('L'): return 'L'
    if tok == 'D': return 'D'
    return tok


class MCRDiscriminador:
    """Avalia sprites gerados vs distribuição de sprites reais."""

    def __init__(self):
        self.transicoes = Counter()
        self.total = 0
        self.papeis_contados = Counter()

    def treinar(self, grids: List[List[List[str]]]):
        """Treina com grids 2D de tokens."""
        for grid in grids:
            h, w = len(grid), len(grid[0])
            for y in range(h):
                for x in range(w):
                    tok = grid[y][x]
                    if tok == 'F':
                        continue
                    papel = _papel(tok)
                    ctx_esq = _papel(grid[y][x-1]) if x > 0 else 'F'
                    ctx_cima = _papel(grid[y-1][x]) if y > 0 else 'F'
                    self.transicoes[(ctx_esq, ctx_cima, papel)] += 1
                    self.papeis_contados[papel] += 1
                    self.total += 1

    def _prob(self, ctx_esq: str, ctx_cima: str, papel: str) -> float:
        count_ctx_token = self.transicoes.get((ctx_esq, ctx_cima, papel), 0)
        count_ctx = sum(
            self.transicoes.get((ctx_esq, ctx_cima, p), 0)
            for p in self.papeis_contados.keys()
        )
        return count_ctx_token / max(count_ctx, 1)

    def avaliar(self, grid: List[List[str]]) -> Dict:
        """Avalia um grid 2D de tokens."""
        h, w = len(grid), len(grid[0])
        scores = []
        detalhes = defaultdict(list)

        for y in range(h):
            for x in range(w):
                tok = grid[y][x]
                if tok == 'F':
                    continue
                papel = _papel(tok)
                ctx_esq = _papel(grid[y][x-1]) if x > 0 else 'F'
                ctx_cima = _papel(grid[y-1][x]) if y > 0 else 'F'
                prob = self._prob(ctx_esq, ctx_cima, papel)
                scores.append(prob)
                detalhes[papel].append(prob)

        if not scores:
            return {'score': 0.0, 'detalhes': {}, 'ok': False}

        score_medio = sum(scores) / len(scores)
        score_min = min(scores)
        score_max = max(scores)

        resumo_detalhes = {}
        for papel, probs in detalhes.items():
            resumo_detalhes[papel] = {
                'media': sum(probs)/len(probs),
                'n': len(probs),
            }

        return {
            'score': score_medio,
            'score_min': score_min,
            'score_max': score_max,
            'n_pixels': len(scores),
            'detalhes': resumo_detalhes,
            'ok': score_medio > 0.5,
        }

    def diagnostico(self, resultado: Dict) -> str:
        """Diagnóstico textual do resultado."""
        s = resultado['score']
        if s > 0.7:
            txt = 'EXCELENTE'
        elif s > 0.5:
            txt = 'BOM'
        elif s > 0.3:
            txt = 'ACEITAVEL'
        else:
            txt = 'FRACO'

        linhas = [
            f'Score: {s:.3f} ({txt})',
            f'Range: {resultado["score_min"]:.3f}-{resultado["score_max"]:.3f}',
            f'Pixels: {resultado["n_pixels"]}',
        ]
        for papel, info in resultado['detalhes'].items():
            linhas.append(f'  {papel}: media={info["media"]:.3f} n={info["n"]}')

        return '\n'.join(linhas)
