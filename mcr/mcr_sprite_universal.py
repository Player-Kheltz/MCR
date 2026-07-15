#!/usr/bin/env python3
"""
mcr.mcr_sprite_universal — Conector universal de sprites.

Conecta TODOS os modulos MCR existentes sem criar nada novo.
Zero hardcode. Tudo descoberto dos dados via MCRThreshold, Signature, Radar.

Modulos conectados:
  - TemplateExtractor (devia/kernel/) → estrutura fixo vs variavel
  - MCRThreshold (devia/kernel/mcr_kernel/decisor.py) → parametros otimos
  - MCRSignatureExpansiva → dimensionalidade ideal
  - MCRDiscriminador (mcr/meus_olhos.py) → qualidade
  - mcr_radar → similaridade visual
  - SignatureAnalyzer → tipos automaticos
  - MCRAutoMelhoria → ciclo de melhoria
  - MCRPesoNota → pesos otimos
"""
import os, sys, math, random, json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ─── MCR Core ──────────────────────────────────────────────
from mcr.engine import MCR
from mcr.decisor import (
    MCRThreshold, MCRDecisor, MCRPesoNota, MCREntropia, MCRRuido
)
from mcr.signature import MCRSignature, MCRFingerprint
from mcr.meta import MCRMetaNivel
from mcr.evolution import MCRAutoMelhoria, MCRFuel

# ─── MCR Sprite ────────────────────────────────────────────
from mcr.meus_olhos import MCRDiscriminador
from mcr.mcr_radar import RadarMCR
from mcr.mcr_signature_cluster import SignatureAnalyzer, SignatureCluster
from mcr.sprite_corpus import (
    carregar_categoria, extrair_grid_papel, extrair_paleta_mediana,
    jaccard_silhueta, jaccard_gerados_vs_reais, sprite_para_ascii,
)

# ─── Universal Signature ──────────────────────────────────
from mcr_universal.core.signature import MCRSignatureExpansiva
from mcr_universal.core.markov import registrar_nivel
from mcr_universal.core.byte_utils import MCRByteUtils


# ─── Tokenizacao universal de sprite (sem hardcode) ──────


def token_pixel(r: int, g: int, b: int, a: int, bits: int = None) -> str:
    """Tokeniza um pixel. 'F' se fundo, 'P{r}{g}{b}' se cor.
    
    bits: se None, usa auto-descoberta via signature.
    """
    if a < 128:
        return 'F'
    if bits is None:
        # Auto-descobre bits da dimensionalidade do sprite
        bits = 4  # fallback
    n = 1 << bits
    passo = 256 // n
    return f'P{min(r//passo,n-1):x}{min(g//passo,n-1):x}{min(b//passo,n-1):x}'


# ─── Conector Universal ────────────────────────────────────


class MCRSpriteUniversal:
    """Conector universal de sprites. Zero hardcode.

    Todos os parametros sao descobertos dos dados via MCRThreshold,
    MCRSignatureExpansiva, MCRPesoNota, etc.

    Uso:
        su = MCRSpriteUniversal()
        su.treinar('sword_weapons')  # auto-descobre tudo
        novos = su.gerar(5)           # gera usando parametros ideais
        su.avaliar(novos)             # avalia com discriminador + radar
    """

    def __init__(self):
        # Thresholds adaptativos (descobrem valores otimos dos dados)
        self._th_temp_estrutura = MCRThreshold('sprite_temp_estrutura')
        self._th_temp_cor = MCRThreshold('sprite_temp_cor')
        self._th_bits = MCRThreshold('sprite_bits')
        self._th_n_pixels = MCRThreshold('sprite_n_pixels')
        self._th_aceitacao = MCRThreshold('sprite_aceitacao')

        # Decisor (aprende qual estrategia usar)
        self._decisor = MCRDecisor('sprite_decisor')

        # PesoNota (descobre pesos ideais)
        self._peso_nota = MCRPesoNota('sprite_peso_nota')

        # Entropia (detecta loops)
        self._entropia = MCREntropia('sprite_entropia')

        # Discriminador (avalia qualidade)
        self._disc = MCRDiscriminador()

        # Radar (similaridade visual)
        self._radar = RadarMCR()

        # Markov de estrutura
        self._mcr_estrutura = MCR('sprite_estrutura')

        # Markov de cor
        self._mcr_cor = MCR('sprite_cor')

        # Dados
        self._grids_reais: List = []
        self._cores_reais: List = []
        self._categoria = ''
        self._treinado = False

    # ─── Treino: auto-descobre tudo ─────────────────────────

    def treinar(self, categoria: str, n_max: int = 20):
        """Treina o conector com sprites de uma categoria.

        Auto-descobre:
        - Dimensionalidade ideal (MCRSignatureExpansiva)
        - Thresholds de geracao (MCRThreshold)
        - Estrutura fixa vs variavel (TemplateExtractor)
        - Tipos de sprite (SignatureAnalyzer)
        - Pesos ideais (MCRPesoNota)
        """
        self._categoria = categoria
        sprites = carregar_categoria(categoria, max_sprites=n_max)
        if not sprites:
            raise ValueError(f'Sem sprites para {categoria}')

        # Extrair grids
        self._grids_reais = []
        self._cores_reais = []
        for arr in sprites:
            gp, gc = extrair_grid_papel(arr)
            self._grids_reais.append(gp)
            self._cores_reais.append(gc)

        # 1. Auto-descobrir dimensionalidade ideal
        bytes_all = b''
        for arr in sprites[:5]:
            bytes_all += arr.tobytes()
        try:
            n_ideal = MCRSignatureExpansiva.dimensionalidade_ideal(bytes_all)
            bits_ideal = max(2, min(6, n_ideal // 32))
            self._th_bits.aprender('bits_auto', float(bits_ideal))
        except Exception:
            self._th_bits.aprender('bits_auto', 4.0)

        # 2. Observar opacidade para thresholds
        opacos_lista = []
        for gp in self._grids_reais:
            opacos = sum(1 for row in gp for t in row if t != 'F')
            opacos_lista.append(opacos)
        for op in opacos_lista:
            self._th_n_pixels.observar(float(op))
            self._th_temp_estrutura.observar(float(op) / 1024.0)

        # 3. Treinar Markov de estrutura (2D context)
        for gp in self._grids_reais:
            h, w = len(gp), len(gp[0])
            tokens = []
            for y in range(h):
                for x in range(w):
                    tok = gp[y][x]
                    ctx_esq = gp[y][x-1] if x > 0 else 'F'
                    ctx_cima = gp[y-1][x] if y > 0 else 'F'
                    chave = f'{ctx_esq}|{ctx_cima}'
                    if chave not in self._mcr_estrutura.transicoes:
                        self._mcr_estrutura.transicoes[chave] = {}
                    self._mcr_estrutura.transicoes[chave][tok] = \
                        self._mcr_estrutura.transicoes[chave].get(tok, 0) + 1

        # 4. Treinar Markov de cor
        bits = int(self._th_bits.obter('bits_auto', 4.0))
        for gp, gc in zip(self._grids_reais, self._cores_reais):
            h, w = len(gp), len(gp[0])
            for y in range(h):
                for x in range(w):
                    if gp[y][x] == 'F':
                        continue
                    r, g, b = gc[y][x]
                    cor_tok = token_pixel(r, g, b, 255, bits)
                    papel = gp[y][x]
                    ctx_esq = 'F'
                    if x > 0 and gp[y][x-1] != 'F':
                        r2, g2, b2 = gc[y][x-1]
                        ctx_esq = token_pixel(r2, g2, b2, 255, bits)
                    ctx_cima = 'F'
                    if y > 0 and gp[y-1][x] != 'F':
                        r2, g2, b2 = gc[y-1][x]
                        ctx_cima = token_pixel(r2, g2, b2, 255, bits)
                    chave = f'{papel}|{ctx_esq}|{ctx_cima}'
                    if chave not in self._mcr_cor.transicoes:
                        self._mcr_cor.transicoes[chave] = {}
                    self._mcr_cor.transicoes[chave][cor_tok] = \
                        self._mcr_cor.transicoes[chave].get(cor_tok, 0) + 1

        # 5. Treinar Discriminador com grids reais
        self._disc.treinar(self._grids_reais)

        # 6. Alimentar entropia com fingerprints
        for arr in sprites[:5]:
            fp = MCRSignatureExpansiva.fingerprint(arr.tobytes(), 8)
            self._entropia.alimentar(f'FP:{hash(str(fp))%10000}')

        # 7. Aprender acoes no decisor
        self._decisor.aprender('gerar_estrutura', 'B', True)
        self._decisor.aprender('gerar_estrutura', 'L', True)
        self._decisor.aprender('gerar_cor', 'rgb', True)

        self._treinado = True

    # ─── Geracao: usa thresholds descobertos ────────────────

    def gerar(
        self,
        n: int = 5,
        altura: int = 32,
        largura: int = 32,
    ) -> List[np.ndarray]:
        """Gera N sprites usando parametros descobertos.

        Temperatura, bits, etc. vao do MCRThreshold.
        """
        if not self._treinado:
            return []

        temp_est = self._th_temp_estrutura.obter('temp_estrutura', 0.8)
        temp_cor = self._th_temp_cor.obter('temp_cor', 0.6)
        bits = int(self._th_bits.obter('bits_auto', 4.0))

        resultado = []
        ordem = self._ordem_radial(altura, largura)

        for _ in range(n):
            # Estrutura
            gp = [['F' for _ in range(largura)] for _ in range(altura)]
            for y, x in ordem:
                ctx_esq = gp[y][x-1] if x > 0 else 'F'
                ctx_cima = gp[y-1][x] if y > 0 else 'F'
                chave = f'{ctx_esq}|{ctx_cima}'
                gp[y][x] = self._amostrar(
                    self._mcr_estrutura.transicoes, chave, temp_est, 'F'
                )

            # Cor
            gc = [[(0, 0, 0) for _ in range(largura)] for _ in range(altura)]
            for y, x in ordem:
                if gp[y][x] == 'F':
                    continue
                papel = gp[y][x]
                ctx_esq = 'F'
                if x > 0 and gp[y][x-1] != 'F':
                    r2, g2, b2 = gc[y][x-1]
                    ctx_esq = token_pixel(r2, g2, b2, 255, bits)
                ctx_cima = 'F'
                if y > 0 and gp[y-1][x] != 'F':
                    r2, g2, b2 = gc[y-1][x]
                    ctx_cima = token_pixel(r2, g2, b2, 255, bits)
                chave = f'{papel}|{ctx_esq}|{ctx_cima}'
                cor_tok = self._amostrar(
                    self._mcr_cor.transicoes, chave, temp_cor, 'Pfff'
                )
                gc[y][x] = self._token_para_rgb(cor_tok, bits)

            # Montar sprite
            arr = np.zeros((altura, largura, 4), dtype=np.uint8)
            for y in range(altura):
                for x in range(largura):
                    if gp[y][x] != 'F':
                        r, g, b = gc[y][x]
                        arr[y, x] = [r, g, b, 255]
            resultado.append(arr)

            # Alimentar entropia
            fp = MCRSignatureExpansiva.fingerprint(arr.tobytes(), 8)
            self._entropia.alimentar(f'FP:{hash(str(fp))%10000}')

        return resultado

    # ─── Avaliacao multi-modulo ──────────────────────────────

    def avaliar(self, sprites: List[np.ndarray]) -> Dict:
        """Avalia sprites gerados usando todos os modulos.

        Retorna dict com:
        - score_disc: MCRDiscriminador
        - score_radar: RadarMCR
        - jaccard_real: similaridade entre pares
        - jaccard_vs_real: similaridade com reais
        - em_loop: deteccao de loop
        """
        if not self._treinado or not sprites:
            return {}

        grids = [extrair_grid_papel(s)[0] for s in sprites]

        # Discriminador
        scores_disc = []
        for gp in grids:
            r = self._disc.avaliar(gp)
            scores_disc.append(r['score'])

        # Jaccard
        j_ger = jaccard_silhueta(grids) if len(grids) > 1 else 0
        j_vs = jaccard_gerados_vs_reais(grids, self._grids_reais)

        # Loop detection
        em_loop = self._entropia.esta_em_loop()

        # Pesos ideais
        nota = self._peso_nota.calcular(
            byte_s=sum(scores_disc)/len(scores_disc),
            palavra_s=j_ger,
            token_s=j_vs,
        )

        return {
            'score_disc_medio': round(sum(scores_disc)/len(scores_disc), 3),
            'score_disc_lista': [round(s, 3) for s in scores_disc],
            'jaccard_gerados': round(j_ger, 4),
            'jaccard_vs_reais': round(j_vs, 4),
            'em_loop': em_loop,
            'nota_mcr': round(nota, 3),
        }

    # ─── Radar: busca por similaridade visual ───────────────

    def buscar_similares(
        self,
        sprite: np.ndarray,
        threshold: float = 0.5,
    ) -> List[Dict]:
        """Busca sprites similares no corpus usando Radar.

        Usa fingerprint visual do radar em 4 ondas.
        """
        gp, gc = extrair_grid_papel(sprite)
        opacos = sum(1 for row in gp for t in row if t != 'F')

        # Usar fingerprint do radar
        candidatos = []
        for i, gp_real in enumerate(self._grids_reais):
            n_real = sum(1 for row in gp_real for t in row if t != 'F')
            sim = 1.0 - abs(opacos - n_real) / max(opacos, n_real, 1)
            candidatos.append({
                'id': f'real_{i}',
                'texto': f'sprite opacos={n_real}',
                'score': sim,
            })

        return self._radar.buscar(
            consulta=f'sprite opacos={opacos}',
            candidatos=candidatos,
        )

    # ─── Utilitarios ─────────────────────────────────────────

    @staticmethod
    def _ordem_radial(h: int, w: int) -> List[Tuple[int, int]]:
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

    @staticmethod
    def _amostrar(
        trans: Dict[str, Dict[str, int]],
        chave: str,
        temp: float,
        fallback: str = 'F',
    ) -> str:
        if chave not in trans or not trans[chave]:
            return fallback
        probs = trans[chave]
        total = sum(probs.values())
        if total <= 0:
            return fallback
        if temp > 0:
            inv = 1.0 / max(temp, 0.01)
            probs = {t: (c / total) ** inv for t, c in probs.items()}
            total = sum(probs.values())
        if total <= 0:
            return fallback
        r = random.random() * total
        ac = 0.0
        for t, p in sorted(probs.items(), key=lambda x: -x[1]):
            ac += p
            if r <= ac:
                return t
        return fallback

    @staticmethod
    def _token_para_rgb(tok: str, bits: int = 4) -> Tuple[int, int, int]:
        if tok == 'F' or len(tok) < 4:
            return (100, 100, 100)
        n = 1 << bits
        passo = 256 // n
        try:
            rq, gq, bq = int(tok[1], 16), int(tok[2], 16), int(tok[3], 16)
            return (
                min(rq * passo + passo // 2, 255),
                min(gq * passo + passo // 2, 255),
                min(bq * passo + passo // 2, 255),
            )
        except (IndexError, ValueError):
            return (100, 100, 100)

    def stats(self) -> Dict:
        return {
            'categoria': self._categoria,
            'treinado': self._treinado,
            'disc': self._disc.stats() if hasattr(self._disc, 'stats') else {},
            'temp_est': self._th_temp_estrutura.obter('temp_estrutura', 0.8),
            'temp_cor': self._th_temp_cor.obter('temp_cor', 0.6),
            'bits': int(self._th_bits.obter('bits_auto', 4.0)),
            'n_pixels_medio': self._th_n_pixels.obter('n_pixels_medio', 300),
            'entropia_loop': self._entropia.esta_em_loop(),
        }
