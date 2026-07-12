#!/usr/bin/env python3
"""
mcr.mcr_sprite_motor — Motor multi-nivel para sprites com SQLite + N-adaptativo.

Segue EXATAMENTE o padrao do MCRMotor (prototypes/mcr-universal/emergence/motor.py):
  3 niveis em PARALELO: byte, palavra, token.
  SQLite backend (sem RAM blowup).
  N-adaptativo ate 30 (igual mcr_adapt.py).
  Batch learning nativo.
  
Nao define o que e 'palavra' ou 'token' — MCRMetaNivel descobre.
"""
import sys, math, random, numpy as np, os
from collections import Counter, defaultdict
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, r'E:\MCR')
sys.path.insert(0, r'E:\MCR\prototypes\mcr-universal')

from mcr.mcr_sqlite import MCRSQLite
from devia.kernel.mcr_kernel.engine import MCR, compose_state, compor_contexto
from devia.kernel.mcr_kernel.decisor import MCRDecisor, MCREntropia, MCRPesoNota
from devia.kernel.mcr_kernel.meta import MCRMetaNivel
from mcr.sprite_corpus import carregar_categoria, extrair_grid_papel
from mcr.tokenizador_hierarquico import extrair_regioes, ordenar_regioes


class MCRSpriteMotor:
    """Motor multi-nivel para sprites (byte + palavra + token) com SQLite.

    Igual ao MCRMotor para codigo, mas com:
      mk_byte:     B:ff → B:00 (bytes RGBA)
      mk_palavra:  B_12-14 → L_15-20 (regioes)
      mk_token:    B → L (papeis)
    
    SQLite backend: sem RAM blowup, N-adaptativo ate 30.
    """

    _DB_DIR = Path(r'E:\MCR\poc_output\mcr_db')
    _DB_DIR.mkdir(parents=True, exist_ok=True)

    def __init__(self, nome: str = 'sprite'):
        # 4 niveis em paralelo (byte + palavra + token + cor)
        self.mk_byte = MCRSQLite(
            str(self._DB_DIR / f'{nome}_byte.db'), identidade='byte', n_max=8)
        self.mk_palavra = MCRSQLite(
            str(self._DB_DIR / f'{nome}_palavra.db'), identidade='palavra', n_max=8)
        self.mk_token = MCRSQLite(
            str(self._DB_DIR / f'{nome}_token.db'), identidade='token', n_max=3)
        self.mk_cor = MCRSQLite(
            str(self._DB_DIR / f'{nome}_cor.db'), identidade='cor', n_max=8)

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
        """Treina os 3 niveis em PARALELO com batch learning.

        Coleta TODOS os tokens primeiro, depois 3 threads paralelas
        para aprender_batch em cada nivel (byte/palavra/token).
        """
        bytes_list = []
        palavras_list = []
        tokens_list = []
        cores_list = []

        for arr in sprites:
            bytes_data = arr.tobytes()
            gp, gc = extrair_grid_papel(arr)
            regioes = extrair_regioes(gp, modo='papel')
            regioes = ordenar_regioes(regioes)

            bytes_tokens = [f"B:{b:02x}" for b in bytes_data]
            bytes_list.append(bytes_tokens)

            tokens_regiao = []
            cores_regiao = []
            
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

                # Cor media da regiao
                cores = [gc[py][px] for px, py in r['pixels']]
                r_med = sum(c[0] for c in cores) // len(cores)
                g_med = sum(c[1] for c in cores) // len(cores)
                b_med = sum(c[2] for c in cores) // len(cores)
                
                # Quantizar cor para 4 bits (16 niveis)
                def q(v): return min(v // 16, 15)
                cor_tok = 'C%x%x%x' % (q(r_med), q(g_med), q(b_med))
                
                # Token com contexto via compose_state (igual codigo: return|em_bloco:metodo)
                ctx_token = compose_state(cor_tok, {
                    'papel': r['papel'],
                    'px': str(cx // 4),
                    'py': str(cy // 4),
                })
                cores_regiao.append(ctx_token)

                self._regioes_banco.append({
                    'token': token, 'pixels': r['pixels'],
                    'papel': r['papel'], 'cx': cx, 'cy': cy,
                    'area': area, 'bw': bw, 'bh': bh,
                    'cor': cor_tok,
                })

            if len(tokens_regiao) > 1:
                palavras_list.append(tokens_regiao)
                tokens_list.append([r['papel'] for r in regioes])
                cores_list.append(cores_regiao)

        # Batch learning PARALELO — 4 threads, 4 DBs diferentes
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = {}
            if bytes_list:
                futures['byte'] = ex.submit(self.mk_byte.aprender_batch, bytes_list)
            if palavras_list:
                futures['palavra'] = ex.submit(self.mk_palavra.aprender_batch, palavras_list)
            if tokens_list:
                futures['token'] = ex.submit(self.mk_token.aprender_batch, tokens_list)
            if cores_list:
                futures['cor'] = ex.submit(self.mk_cor.aprender_batch, cores_list)

            for nome, fut in futures.items():
                try:
                    fut.result(timeout=60)
                except Exception as e:
                    print(f'[sprite_motor] Erro treino {nome}: {e}')

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

    def gerar(self, n: int = 3, temperatura: float = 0.6) -> List[Dict]:
        """Gera N sprites com temperatura e cor.

        Retorna lista de dicts: {'regioes': [...], 'cores': [...]}
        'regioes': tokens de estrutura (B_12-14...)
        'cores': tokens de cor com contexto (Cxxx|papel:B|px:3|py:7)
        """
        resultado = []

        for _ in range(n):
            tokens_regiao = []
            tokens_cor = []

            semente = 'F'
            cur = self.mk_palavra.conn.execute(
                "SELECT key FROM freq ORDER BY total DESC LIMIT 10")
            rows = cur.fetchall()
            if rows:
                partes = random.choice(rows)[0].split('|')
                if len(partes) > 1:
                    semente = random.choice(partes[1:])

            atual = semente

            for passo in range(30):
                prox = self._predizer_com_temperatura(self.mk_palavra, atual, temperatura)
                if prox is None:
                    prox = self._predizer_com_temperatura(self.mk_token, atual, temperatura)
                if prox is None:
                    prox = self._predizer_com_temperatura(self.mk_byte, atual, temperatura)
                if prox is None:
                    break

                atual = prox
                tokens_regiao.append(atual)

                # Cor: buscar no banco a regiao mais proxima
                try:
                    melhor = self._encontrar_regiao(atual)
                    cor_tok = melhor.get('cor', 'C888') if melhor else 'C888'
                except Exception:
                    cor_tok = 'C888'
                tokens_cor.append(cor_tok)

            if tokens_regiao:
                resultado.append({'regioes': tokens_regiao, 'cores': tokens_cor})

        return resultado

    @staticmethod
    def _predizer_com_temperatura(mcr, ctx: str, temp: float = 0.6) -> Optional[str]:
        """Prediz com temperatura: amostra da distribuicao, nao o maximo."""
        import random as _rnd
        ctx_str = str(ctx)
        for depth in range(min(mcr.n_max, len(ctx_str.split('|')) if '|' in ctx_str else 1), 0, -1):
            partes = ctx_str.split('|') if '|' in ctx_str else [ctx_str]
            chave = f"{mcr.identidade}|{'|'.join(partes[-depth:])}"
            cur = mcr.conn.execute(
                "SELECT t.next, t.count, COALESCE(f.total, 0) "
                "FROM trans t LEFT JOIN freq f ON t.key = f.key "
                "WHERE t.key = ? ORDER BY t.count DESC LIMIT 20",
                (chave,))
            rows = cur.fetchall()
            if rows:
                total = max(rows[0][2], 1)
                if temp > 0:
                    probs = [(r[0], (r[1] / total) ** (1.0 / temp)) for r in rows]
                    total_prob = sum(p for _, p in probs)
                    r = _rnd.random() * total_prob
                    ac = 0.0
                    for tok, prob in probs:
                        ac += prob
                        if r <= ac:
                            return tok
                return rows[0][0]
        return None

    # ─── Renderizacao: tokens → pixels via banco de regioes

    def renderizar(self, dados, altura=32, largura=32) -> np.ndarray:
        """Renderiza tokens de regiao para pixels RGBA com cores.

        Args:
            dados: dict com 'regioes' (tokens) e 'cores' (tokens de cor),
                   ou lista de tokens (fallback para compatibilidade)

        Returns:
            array numpy (altura, largura, 4) uint8
        """
        from PIL import Image

        if isinstance(dados, dict):
            tokens = dados['regioes']
            cores = dados.get('cores', [])
        else:
            tokens = dados
            cores = []

        grid = [['F' for _ in range(largura)] for _ in range(altura)]
        grid_cor = [[(0, 0, 0) for _ in range(largura)] for _ in range(altura)]

        for i, token in enumerate(tokens):
            if token == 'F' or '_' not in token:
                continue

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

            dx = cx_alvo - melhor['cx']
            dy = cy_alvo - melhor['cy']

            # Usar cor gerada ou fallback para cor do banco
            if i < len(cores) and cores[i] and cores[i].startswith('C'):
                cor_tok = cores[i]
            else:
                cor_tok = melhor.get('cor', 'C888')
            
            try:
                r = int(cor_tok[1], 16) * 16 + 8
                g = int(cor_tok[2], 16) * 16 + 8
                b = int(cor_tok[3], 16) * 16 + 8
            except (IndexError, ValueError):
                r, g, b = 128, 128, 128

            for px, py in melhor['pixels']:
                nx, ny = px + dx, py + dy
                if 0 <= nx < largura and 0 <= ny < altura:
                    if grid[ny][nx] == 'F':
                        grid[ny][nx] = melhor['papel']
                        grid_cor[ny][nx] = (r, g, b)

        arr = np.zeros((altura, largura, 4), dtype=np.uint8)
        for y in range(altura):
            for x in range(largura):
                if grid[y][x] != 'F':
                    r, g, b = grid_cor[y][x]
                    arr[y, x] = [r, g, b, 255]
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

    def avaliar(self, dados) -> Dict:
        """Avalia sprite gerado com NOTA = (byte + palavra + token) x penalidade.

        Args:
            dados: dict com 'regioes' ou lista de tokens
        """
        if isinstance(dados, dict):
            tokens = dados['regioes']
        else:
            tokens = dados

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
            'cor': self.mk_cor.stats(),
            'topicos': {k: v['n_sprites'] for k, v in self._topicos.items()},
            'banco_regioes': len(self._regioes_banco),
        }
