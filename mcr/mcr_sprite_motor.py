#!/usr/bin/env python3
"""
mcr.mcr_sprite_motor — Motor multi-nivel para sprites.

Segue EXATAMENTE o padrao do MCRMotor (prototypes/mcr-universal/emergence/motor.py):
  3 niveis em PARALELO: byte, palavra, token.
  Treino simultaneo nos 3 niveis.
  Geracao com MCRDecisor escolhendo nivel.
  Validacao via NOTA = (byte + palavra + token) x penalidade.

Nao define o que e "palavra" ou "token" — MCRMetaNivel descobre.
"""
import sys, math, random, numpy as np
from collections import Counter, defaultdict
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, r'E:\MCR')
sys.path.insert(0, r'E:\MCR\prototypes\mcr-universal')

from devia.kernel.mcr_kernel.engine import MCR, compose_state, compor_contexto
from devia.kernel.mcr_kernel.decisor import MCRDecisor, MCREntropia, MCRPesoNota
from devia.kernel.mcr_kernel.signature import MCRSignature, MCRFingerprint
from devia.kernel.mcr_kernel.meta import MCRMetaNivel
from mcr_universal.core.signature import MCRSignatureExpansiva
from mcr.sprite_corpus import carregar_categoria, extrair_grid_papel
from mcr.tokenizador_hierarquico import extrair_regioes, ordenar_regioes


class MCRSpriteMotor:
    """Motor multi-nivel para sprites (byte + palavra + token).

    Igual ao MCRMotor para codigo:
      mk_byte:     B:ff → B:00 (bytes RGBA)
      mk_palavra:  B_12-14 → L_15-20 (regioes)
      mk_token:    B → L (papeis)
    
    Geracao: MCRDecisor decide qual nivel andar.
    Validacao: NOTA = (byte + palavra + token) x penalidade.
    """

    def __init__(self):
        # 3 niveis em paralelo (igual MCRMotor)
        self.mk_byte = MCR('sprite_byte')
        self.mk_palavra = MCR('sprite_palavra')
        self.mk_token = MCR('sprite_token')

        # Decisor (escolhe nivel durante geracao)
        self.decisor = MCRDecisor('sprite_decisor')
        self.entropia = MCREntropia('sprite_entropia')
        self.peso_nota = MCRPesoNota('sprite_peso_nota')

        # MetaNivel (descobre niveis automaticamente)
        self.meta_nivel = MCRMetaNivel()

        # Dados de treino
        self._topicos: Dict[str, dict] = {}
        self._regioes_banco: List[dict] = []

        random.seed(42)

    # ─── Treino: 3 niveis em paralelo ─────────────────────

    def treinar(self, sprites: List[np.ndarray], categoria: str = ''):
        """Treina os 3 niveis em paralelo no sprite.

        Igual MCRMotor.alimentar():
          byte:    bytes RGBA (B:ff → B:00)
          palavra: regioes conectadas (B_12-14 → L_15-20)
          token:   papeis (B → L)
        """
        for arr in sprites:
            bytes_data = arr.tobytes()
            gp, gc = extrair_grid_papel(arr)
            regioes = extrair_regioes(gp, modo='papel')
            regioes = ordenar_regioes(regioes)

            # Nivel byte: bytes RGBA brutos (igual MCRMotor)
            for i in range(len(bytes_data) - 1):
                self.mk_byte.aprender(
                    f"B:{bytes_data[i]:02x}",
                    f"B:{bytes_data[i+1]:02x}"
                )

            # Nivel palavra: regioes como tokens
            tokens_regiao = []
            for r in regioes:
                cx = int(r['centroide'][0])
                cy = int(r['centroide'][1])
                area = r['area']
                bw = r['bbox'][2] - r['bbox'][0] + 1
                bh = r['bbox'][3] - r['bbox'][1] + 1
                orient = int(r['orientacao']) if r['orientacao'] >= 0 else 0
                token = '%s_%d-%d_%d_%dx%d_%d' % (
                    r['papel'], cx, cy, area, bw, bh, orient)
                tokens_regiao.append(token)

                # Armazenar pixels da regiao para renderizacao
                self._regioes_banco.append({
                    'token': token,
                    'pixels': r['pixels'],
                    'papel': r['papel'],
                    'cx': cx, 'cy': cy,
                    'area': area, 'bw': bw, 'bh': bh,
                })

            for i in range(len(tokens_regiao) - 1):
                self.mk_palavra.aprender(tokens_regiao[i], tokens_regiao[i + 1])

            # Nivel token: papel B/L/F (igual MCRMotor: primeira letra)
            papeis = [r['papel'] for r in regioes]
            for i in range(len(papeis) - 1):
                self.mk_token.aprender(papeis[i], papeis[i + 1])

        # Alimentar MetaNivel para descobrir niveis
        try:
            for arr in sprites[:3]:
                self.meta_nivel.alimentar(arr.tobytes())
        except Exception:
            pass

        self._topicos[categoria] = {
            'n_sprites': len(sprites),
            'n_regioes': sum(len(extrair_regioes(extrair_grid_papel(s)[0])) for s in sprites) // max(len(sprites), 1),
        }

    # ─── Geracao: MCRDecisor escolhe nivel ────────────────

    def gerar(self, n: int = 3) -> List[List[str]]:
        """Gera N sprites. Decisor escolhe qual nivel andar.

        Igual MCRMotor + MCRCadeia: tenta palavra, se loop → byte,
        se byte caotico → token.
        """
        resultado = []

        for _ in range(n):
            tokens_gerados = []
            nivel_atual = 'palavra'  # comeca no nivel mais alto

            # Semente: token mais comum do nivel palavra
            semente = 'F'
            if self.mk_palavra.freq:
                semente = max(self.mk_palavra.freq, key=self.mk_palavra.freq.get)

            atual = semente
            ctx = {}

            for passo in range(30):  # max 30 regioes por sprite
                # Decisor escolhe nivel
                if self.entropia.esta_em_loop():
                    nivel_atual = self.decisor.decidir(f'nivel_loop', 'byte')
                else:
                    nivel_atual = self.decisor.decidir(f'nivel', nivel_atual)

                # Andar no nivel escolhido
                if nivel_atual == 'byte':
                    prox, conf = self.mk_byte.predizer(atual)
                    if prox is None or conf < 0.01:
                        prox = 'B:00'
                    atual = prox
                    tokens_gerados.append(atual)

                elif nivel_atual == 'token':
                    prox, conf = self.mk_token.predizer(atual)
                    if prox is None or conf < 0.01:
                        break
                    atual = prox
                    tokens_gerados.append(atual)

                else:  # palavra
                    prox, conf = self.mk_palavra.predizer(atual)
                    if prox is None or conf < 0.01:
                        # Fallback: tentar token
                        prox, conf = self.mk_token.predizer(atual)
                        if prox is None or conf < 0.01:
                            break
                    atual = prox

                    # Compor estado com contexto (igual compose_state)
                    estado = compose_state(atual, ctx)
                    ctx = compor_contexto([atual], ctx)
                    tokens_gerados.append(atual)

                # Alimentar entropia
                self.entropia.alimentar(atual)

            if tokens_gerados:
                resultado.append(tokens_gerados)

        return resultado

    # ─── Renderizacao: tokens → pixels via banco de regioes

    def renderizar(self, tokens: List[str], altura=32, largura=32) -> np.ndarray:
        """Renderiza tokens de regiao para pixels RGBA.

        Usa o banco de regioes reais para reconstruir formas exatas.
        """
        from PIL import Image

        grid = [['F' for _ in range(largura)] for _ in range(altura)]
        paleta = {'B': (80, 80, 80), 'L': (180, 180, 180)}

        for token in tokens:
            if token == 'F' or '_' not in token:
                continue

            # Encontrar regiao mais proxima no banco
            melhor = self._encontrar_regiao(token)
            if melhor is None:
                continue

            try:
                partes = token.split('_')
                cx_str = partes[1].split('-')[0]
                cy_str = partes[1].split('-')[1]
                cx_alvo = int(cx_str)
                cy_alvo = int(cy_str)
            except (IndexError, ValueError):
                continue

            # Transladar pixels da regiao original para posicao alvo
            dx = cx_alvo - melhor['cx']
            dy = cy_alvo - melhor['cy']

            for px, py in melhor['pixels']:
                nx, ny = px + dx, py + dy
                if 0 <= nx < largura and 0 <= ny < altura:
                    if grid[ny][nx] == 'F':
                        grid[ny][nx] = melhor['papel']

        # Montar RGBA
        arr = np.zeros((altura, largura, 4), dtype=np.uint8)
        for y in range(altura):
            for x in range(largura):
                p = grid[y][x]
                if p != 'F':
                    cor = paleta.get(p, (128, 128, 128))
                    arr[y, x] = [cor[0], cor[1], cor[2], 255]
        return arr

    def _encontrar_regiao(self, token_alvo: str) -> Optional[dict]:
        """Encontra a regiao mais proxima no banco."""
        if not self._regioes_banco:
            return None
        try:
            partes = token_alvo.split('_')
            papel = partes[0]
            cx_str = partes[1].split('-')[0]
            cy_str = partes[1].split('-')[1]
            cx_alvo = int(cx_str)
            cy_alvo = int(cy_str)
            area_alvo = int(partes[2])
            bw_str, bh_str = partes[3].split('x')
            bw_alvo = int(bw_str)
            bh_alvo = int(bh_str)
        except (IndexError, ValueError):
            return None

        melhor = None
        melhor_dist = float('inf')

        for r in self._regioes_banco:
            if r['papel'] != papel:
                continue
            d_cx = (r['cx'] - cx_alvo) / 32.0
            d_cy = (r['cy'] - cy_alvo) / 32.0
            d_area = (r['area'] - area_alvo) / max(r['area'], area_alvo, 1)
            d_bw = (r['bw'] - bw_alvo) / max(r['bw'], bw_alvo, 1)
            d_bh = (r['bh'] - bh_alvo) / max(r['bh'], bh_alvo, 1)
            dist = math.sqrt(d_cx**2 + d_cy**2 + d_area**2 + d_bw**2 + d_bh**2)

            if dist < melhor_dist:
                melhor_dist = dist
                melhor = r

        return melhor

    # ─── Validacao: NOTA MCR ─────────────────────────────

    def avaliar(self, tokens: List[str]) -> Dict:
        """Avalia sprite gerado com NOTA = (byte + palavra + token) x penalidade."""
        n_tokens = len(tokens)
        n_opacos = sum(1 for t in tokens if t != 'F' and '_' in t)
        papeis = Counter(t.split('_')[0] for t in tokens if '_' in t)
        n_B = papeis.get('B', 0)
        n_L = papeis.get('L', 0)

        # NOTA byte: 0-1 baseado em opacos
        nota_byte = min(1.0, n_opacos / 300)

        # NOTA palavra: 0-1 baseado em variedade de regioes
        unicos = len(set(tokens))
        nota_palavra = min(1.0, unicos / max(n_tokens, 1) * 2)

        # NOTA token: 0-1 baseado em proporcao B/L
        if n_B + n_L > 0:
            proporcao = min(n_B, n_L) / max(n_B, n_L, 1)
            nota_token = 0.3 + 0.7 * proporcao
        else:
            nota_token = 0.0

        # Penalidade: poucas regioes = penalidade alta
        if n_tokens < 3:
            penalidade = 0.9
        elif n_B == 0 or n_L == 0:
            penalidade = 0.5
        else:
            penalidade = 0.0

        # NOTA = (byte + palavra + token) x (1 - penalidade)
        nota = (nota_byte + nota_palavra + nota_token) / 3 * (1.0 - penalidade)

        return {
            'score': round(nota, 4),
            'nota_byte': round(nota_byte, 3),
            'nota_palavra': round(nota_palavra, 3),
            'nota_token': round(nota_token, 3),
            'penalidade': penalidade,
            'n_tokens': n_tokens,
            'n_opacos': n_opacos,
            'n_B': n_B,
            'n_L': n_L,
        }

    def stats(self) -> Dict:
        return {
            'byte': self.mk_byte.stats(),
            'palavra': self.mk_palavra.stats(),
            'token': self.mk_token.stats(),
            'topicos': {k: v['n_sprites'] for k, v in self._topicos.items()},
            'banco_regioes': len(self._regioes_banco),
        }
