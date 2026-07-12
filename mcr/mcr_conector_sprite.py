#!/usr/bin/env python3
"""
mcr.mcr_conector_sprite — MCR para sprites: N direcoes, expansao radial.

Cada pixel vira um token de papel (B/L/F) + cor.
N direcoes aprendem P(pixel | vizinho_na_direcao).
Geracao: expansao radial do centro.
Cada pixel: coleta votos de todas as direcoes com contexto viavel.
Entropia como bussola: direcao com menor H = maior peso.
"""
import math
import random
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


def pixel_token(r: int, g: int, b: int, a: int, bits: int = 4) -> str:
    if a < 128:
        return 'F'
    n = 1 << bits
    passo = 256 // n
    return f'P{min(r//passo,n-1):x}{min(g//passo,n-1):x}{min(b//passo,n-1):x}'


def token_para_rgba(tok: str, bits: int = 4) -> Tuple[int, int, int, int]:
    if tok == 'F':
        return (0, 0, 0, 0)
    n = 1 << bits
    passo = 256 // n
    try:
        rq, gq, bq = int(tok[1], 16), int(tok[2], 16), int(tok[3], 16)
        return (min(rq * passo + passo // 2, 255),
                min(gq * passo + passo // 2, 255),
                min(bq * passo + passo // 2, 255), 255)
    except (IndexError, ValueError):
        return (0, 0, 0, 0)


# ─── 8 direcoes: cada uma define como extrair contexto ──────

DIRS = {
    'LR':  lambda g, x, y, w, h: g[y][x-1] if x > 0 else None,
    'RL':  lambda g, x, y, w, h: g[y][x+1] if x < w-1 else None,
    'UD':  lambda g, x, y, w, h: g[y-1][x] if y > 0 else None,
    'DU':  lambda g, x, y, w, h: g[y+1][x] if y < h-1 else None,
    'NWSE':lambda g, x, y, w, h: g[y-1][x-1] if y > 0 and x > 0 else None,
    'NESW':lambda g, x, y, w, h: g[y-1][x+1] if y > 0 and x < w-1 else None,
    'SWNE':lambda g, x, y, w, h: g[y+1][x+1] if y < h-1 and x < w-1 else None,
    'SENW':lambda g, x, y, w, h: g[y+1][x-1] if y < h-1 and x > 0 else None,
}

# Direcoes que tem contexto durante geracao (expansao radial)
DIR_GERA = ['LR', 'UD', 'NWSE', 'NESW']


class MCRSpriteConector:
    """MCR N-direcoes para geracao de sprites.

    Cada direcao aprende P(pixel | contexto_na_direcao).
    Geracao: expansao radial, combinacao ponderada por entropia.
    """

    def __init__(self, nome: str = 'sprite', bits: int = 4):
        self.nome = nome
        self.bits = bits

        # Transicoes de estrutura (papel B/L/F)
        self.trans: Dict[str, Dict[str, Dict[str, int]]] = {}
        self.freq: Dict[str, Dict[str, int]] = {}
        for d in DIRS:
            self.trans[d] = {}
            self.freq[d] = {}

        # Transicoes de cor (por papel)
        self.trans_cor: Dict[str, Dict[str, Dict[str, int]]] = {}
        self.freq_cor: Dict[str, Dict[str, int]] = {}
        for d in DIRS:
            self.trans_cor[d] = {}
            self.freq_cor[d] = {}

        self._entropias: Dict[str, float] = {}
        self._entropias_cor: Dict[str, float] = {}

    def _extrair_papel(self, arr: np.ndarray) -> Tuple[List[List[str]], List[List[Tuple]]]:
        """Extrai papel (B/L/F) e cor de sprite RGBA."""
        from mcr.sprite_corpus import extrair_grid_papel
        return extrair_grid_papel(arr)

    def treinar(self, sprites: List[np.ndarray]):
        """Treina N direcoes para estrutura (papel) E cor."""
        for arr in sprites:
            gp, gc = self._extrair_papel(arr)
            h, w = len(gp), len(gp[0])

            for nome_dir, ctx_fn in DIRS.items():
                for y in range(h):
                    for x in range(w):
                        # Estrutura (papel)
                        ctx = ctx_fn(gp, x, y, w, h)
                        if ctx is None:
                            continue
                        tok = gp[y][x]
                        if ctx not in self.trans[nome_dir]:
                            self.trans[nome_dir][ctx] = {}
                            self.freq[nome_dir][ctx] = 0
                        self.trans[nome_dir][ctx][tok] = self.trans[nome_dir][ctx].get(tok, 0) + 1
                        self.freq[nome_dir][ctx] += 1

                        # Cor (se pixel nao-F)
                        if gp[y][x] == 'F':
                            continue
                        r, g, b = gc[y][x]
                        cor_tok = pixel_token(r, g, b, 255, self.bits)

                        # Contexto de cor na direcao
                        ctx_neighbor = ctx_fn(gc if hasattr(gc[0][0], '__getitem__') else gc, x, y, w, h)
                        # Simplificado: contexto = papel_do_vizinho + cor_do_vizinho
                        if ctx is not None and ctx != 'F':
                            nr, ng, nb = (0, 0, 0)
                            # Extrair cor do vizinho
                            if ctx_fn == DIRS['LR'] and x > 0:
                                nr, ng, nb = gc[y][x-1]
                            elif ctx_fn == DIRS['RL'] and x < w-1:
                                nr, ng, nb = gc[y][x+1]
                            elif ctx_fn == DIRS['UD'] and y > 0:
                                nr, ng, nb = gc[y-1][x]
                            elif ctx_fn == DIRS['DU'] and y < h-1:
                                nr, ng, nb = gc[y+1][x]
                            elif ctx_fn == DIRS['NWSE'] and y > 0 and x > 0:
                                nr, ng, nb = gc[y-1][x-1]
                            elif ctx_fn == DIRS['NESW'] and y > 0 and x < w-1:
                                nr, ng, nb = gc[y-1][x+1]
                            elif ctx_fn == DIRS['SWNE'] and y < h-1 and x < w-1:
                                nr, ng, nb = gc[y+1][x+1]
                            elif ctx_fn == DIRS['SENW'] and y < h-1 and x > 0:
                                nr, ng, nb = gc[y+1][x-1]
                            ctx_cor = pixel_token(nr, ng, nb, 255, self.bits)
                            chave = f'{ctx}|{ctx_cor}'
                        else:
                            chave = f'{ctx}|F'

                        if chave not in self.trans_cor[nome_dir]:
                            self.trans_cor[nome_dir][chave] = {}
                            self.freq_cor[nome_dir][chave] = 0
                        self.trans_cor[nome_dir][chave][cor_tok] = self.trans_cor[nome_dir][chave].get(cor_tok, 0) + 1
                        self.freq_cor[nome_dir][chave] += 1

        # Calcular entropia media por direcao (estrutura)
        for d in DIRS:
            hs = []
            for ctx, probs in self.trans[d].items():
                total = self.freq[d].get(ctx, 1)
                if total > 0:
                    h = -sum((c/total)*math.log2(c/total) for c in probs.values())
                    hs.append(h)
            self._entropias[d] = sum(hs) / len(hs) if hs else 1.0

        # Calcular entropia media por direcao (cor)
        for d in DIRS:
            hs = []
            for ctx, probs in self.trans_cor[d].items():
                total = self.freq_cor[d].get(ctx, 1)
                if total > 0:
                    h = -sum((c/total)*math.log2(c/total) for c in probs.values())
                    hs.append(h)
            self._entropias_cor[d] = sum(hs) / len(hs) if hs else 1.0

    def entropias(self) -> Dict[str, float]:
        return dict(self._entropias)

    def stats(self) -> dict:
        total_est = sum(len(t) for t in self.trans.values())
        total_trans = sum(sum(len(p) for p in t.values()) for t in self.trans.values())
        total_est_cor = sum(len(t) for t in self.trans_cor.values())
        total_trans_cor = sum(sum(len(p) for p in t.values()) for t in self.trans_cor.values())
        return {
            'estados': total_est,
            'transicoes': total_trans,
            'entropias': dict(self._entropias),
            'estados_cor': total_est_cor,
            'transicoes_cor': total_trans_cor,
            'entropias_cor': dict(self._entropias_cor),
        }

    @staticmethod
    def _ordem_radial(h: int, w: int) -> List[Tuple[int, int]]:
        """Ordem de expansao radial a partir do centro."""
        cx, cy = w // 2, h // 2
        ordem = [(cy, cx)]
        visit = {(cy, cx)}
        for d in range(1, max(w, h)):
            for dx in range(-d, d + 1):
                for dy in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) != d:
                        continue
                    x, y = cx + dx, cy + dy
                    if 0 <= x < w and 0 <= y < h and (y, x) not in visit:
                        ordem.append((y, x))
                        visit.add((y, x))
        return ordem

    def _amostrar(self, probs: Dict[str, int], total: int, temp: float) -> str:
        if total <= 0 or not probs:
            return 'F'
        if temp > 0:
            inv = 1.0 / max(temp, 0.01)
            probs_t = {t: (c / total) ** inv for t, c in probs.items()}
            total_t = sum(probs_t.values())
        else:
            probs_t = probs
            total_t = total
        if total_t <= 0:
            return 'F'
        r = random.random() * total_t
        ac = 0.0
        for t, p in sorted(probs_t.items(), key=lambda x: -x[1]):
            ac += p
            if r <= ac:
                return t
        return 'F'

    def gerar(
        self,
        n: int = 1,
        altura: int = 32,
        largura: int = 32,
        temperatura: float = 0.8,
        temp_cor: float = 0.6,
    ) -> List[np.ndarray]:
        """Gera N sprites por expansao radial com N direcoes.

        Passo 1: Estrutura (B/L/F) via cada direcao ponderada por entropia.
        Passo 2: Cor via cada direcao ponderada por entropia.

        Args:
            n: numero de sprites
            temperatura: criatividade da forma (0.8 = bom)
            temp_cor: criatividade das cores (0.6 = fiel ao corpus)

        Returns:
            lista de arrays (altura, largura, 4) uint8
        """
        if not self.trans:
            return []

        ordem = self._ordem_radial(altura, largura)
        resultado = []

        for _ in range(n):
            gp = [['F' for _ in range(largura)] for _ in range(altura)]

            # Passo 1: Estrutura
            for y, x in ordem:
                dist: Dict[str, float] = {}
                peso_total = 0.0

                for d in DIR_GERA:
                    ctx_fn = DIRS[d]
                    ctx = ctx_fn(gp, x, y, largura, altura)
                    if ctx is None or ctx not in self.trans[d]:
                        continue

                    probs = self.trans[d][ctx]
                    total = self.freq[d].get(ctx, 0)
                    if total <= 0:
                        continue

                    peso = 1.0 / max(self._entropias.get(d, 1.0), 0.01)
                    for tok, count in probs.items():
                        dist[tok] = dist.get(tok, 0.0) + (count / total) * peso
                        peso_total += (count / total) * peso

                if peso_total > 0:
                    gp[y][x] = self._amostrar(dist, peso_total, temperatura)

            # Passo 2: Cor
            gc = [[(0, 0, 0) for _ in range(largura)] for _ in range(altura)]

            for y, x in ordem:
                if gp[y][x] == 'F':
                    continue

                dist_cor: Dict[str, float] = {}
                peso_total_cor = 0.0

                for d in DIR_GERA:
                    ctx_fn = DIRS[d]
                    ctx_papel = ctx_fn(gp, x, y, largura, altura)
                    if ctx_papel is None:
                        continue

                    # Obter cor do vizinho na direcao
                    ctx_cor = 'F'
                    if ctx_papel != 'F':
                        ny, nx = y, x
                        if d == 'LR' and x > 0: ny, nx = y, x-1
                        elif d == 'RL' and x < largura-1: ny, nx = y, x+1
                        elif d == 'UD' and y > 0: ny, nx = y-1, x
                        elif d == 'NWSE' and y > 0 and x > 0: ny, nx = y-1, x-1
                        elif d == 'NESW' and y > 0 and x < largura-1: ny, nx = y-1, x+1
                        nr, ng, nb = gc[ny][nx]
                        ctx_cor = pixel_token(nr, ng, nb, 255, self.bits)

                    chave = f'{ctx_papel}|{ctx_cor}'
                    if chave not in self.trans_cor[d]:
                        continue

                    probs = self.trans_cor[d][chave]
                    total = self.freq_cor[d].get(chave, 0)
                    if total <= 0:
                        continue

                    peso = 1.0 / max(self._entropias_cor.get(d, 1.0), 0.01)
                    for tok, count in probs.items():
                        dist_cor[tok] = dist_cor.get(tok, 0.0) + (count / total) * peso
                        peso_total_cor += (count / total) * peso

                if peso_total_cor > 0:
                    cor_tok = self._amostrar(dist_cor, peso_total_cor, temp_cor)
                    r, g, b, _ = token_para_rgba(cor_tok, self.bits)
                    gc[y][x] = (r, g, b)
                else:
                    gc[y][x] = (100, 100, 100)  # fallback cinza

            # Montar RGBA
            arr = np.zeros((altura, largura, 4), dtype=np.uint8)
            for y in range(altura):
                for x in range(largura):
                    if gp[y][x] != 'F':
                        r, g, b = gc[y][x]
                        arr[y, x] = [r, g, b, 255]
            resultado.append(arr)

        return resultado
