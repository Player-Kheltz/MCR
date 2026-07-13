#!/usr/bin/env python3
"""
pipeline_completa — Pipeline de 5 estágios para geração de sprites.

Estágio 1: SILHUETA   — Markov gera estrutura B/L/F (pipeline_orc_mcr)
Estágio 2: CONTORNOS  — Extrai só bordas, remove interior
Estágio 3: DETALHES   — Preenche com textura por pixel
Estágio 4: RECOLOR    — Simplifica paleta via CIELAB clustering
Estágio 5: NÍTIDO     — CIELAB hue rotation por pixel (pipeline_nitido)

Uso:
    python pipeline_completa.py
"""
import os, sys, math, random
from collections import Counter, defaultdict
from PIL import Image
import numpy as np

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcr.cielab import rgb_para_lab, lab_para_rgb, delta_e76, clusterizar_lab, detectar_picos
from mcr.meus_olhos import MCRDiscriminador

OUT_BASE = os.path.join(_BASE, 'poc_output', 'pipeline_completa')
REF_DIR = os.path.join(_BASE, 'poc_output')

# ─── Referências ─────────────────────────────────────────────
ORC_REFS = [
    os.path.join(REF_DIR, 'orc_hue_ref_0.png'),
    os.path.join(REF_DIR, 'orc_hue_ref_1.png'),
    os.path.join(REF_DIR, 'orc_nitido_ref.png'),
    os.path.join(REF_DIR, 'orc_nitido_ref_big.png'),
]


# ═══════════════════════════════════════════════════════════════
# TOKENIZAÇÃO (compartilhada entre estágios)
# ═══════════════════════════════════════════════════════════════

def tokenizar_papel(img):
    """Converte sprite RGBA para grid de papel (B/L/F) + grid de cor."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    w, h = 32, 32
    p = img.load()
    MAGENTA = (255, 0, 255)

    am = []
    for x in range(w):
        if p[x, 0][3] > 128:
            am.append(p[x, 0][:3])
        if p[x, h-1][3] > 128:
            am.append(p[x, h-1][:3])
    for y in range(h):
        if p[0, y][3] > 128:
            am.append(p[0, y][:3])
        if p[w-1, y][3] > 128:
            am.append(p[w-1, y][:3])
    bg = Counter(am).most_common(1)[0][0] if am else MAGENTA

    grid_papel = [['F'] * w for _ in range(h)]
    grid_cor = [[(0, 0, 0)] * w for _ in range(h)]

    for y in range(h):
        for x in range(w):
            r, g, b, a = p[x, y]
            if a < 128 or (r, g, b) == MAGENTA or (r, g, b) == bg:
                grid_papel[y][x] = 'F'
                continue
            eh_borda = any(
                0 <= x+dx < w and 0 <= y+dy < h and (
                    p[x+dx, y+dy][3] < 128 or
                    p[x+dx, y+dy][:3] == MAGENTA or
                    p[x+dx, y+dy][:3] == bg
                )
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
            )
            grid_papel[y][x] = 'B' if eh_borda else 'L'
            grid_cor[y][x] = (r, g, b)

    return grid_papel, grid_cor


def extrair_paleta(grid_cor, grid_papel):
    """Extrai cor média de cada papel."""
    paleta = defaultdict(list)
    for y in range(len(grid_cor)):
        for x in range(len(grid_cor[0])):
            papel = grid_papel[y][x]
            if papel != 'F':
                paleta[papel].append(grid_cor[y][x])
    media = {}
    for papel, cores in paleta.items():
        if cores:
            media[papel] = (
                sum(c[0] for c in cores) // len(cores),
                sum(c[1] for c in cores) // len(cores),
                sum(c[2] for c in cores) // len(cores),
            )
    return dict(media)


def grid_para_imagem(grid_papel, paleta, angulo_hue=0.0, variacao=5):
    """Converte grid B/L/F + paleta em imagem RGBA."""
    h = len(grid_papel)
    w = len(grid_papel[0])
    img = Image.new('RGBA', (w, h))
    pixels = []

    for y in range(h):
        for x in range(w):
            papel = grid_papel[y][x]
            if papel == 'F':
                pixels.append((0, 0, 0, 0))
                continue
            r, g, b = paleta.get(papel, (128, 128, 128))
            L, a, bl = rgb_para_lab(r, g, b)
            raio = math.sqrt(a*a + bl*bl)
            if raio < 3:
                raio = 6
            novo_a = raio * math.cos(angulo_hue)
            novo_b = raio * math.sin(angulo_hue)
            novo_L = L + random.randint(-variacao, variacao)
            cr, cg, cb = lab_para_rgb(novo_L, novo_a, novo_b)
            pixels.append((cr, cg, cb, 255))

    img.putdata(pixels)
    return img


# ═══════════════════════════════════════════════════════════════
# ESTÁGIO 1: SILHUETA (Markov)
# ═══════════════════════════════════════════════════════════════

class MCRGerador:
    """Markov 1ªordem para grids 2D de papeis (B/L/F)."""

    def __init__(self):
        self.transicoes = defaultdict(Counter)
        self.marginal_esq = Counter()
        self.marginal_cima = Counter()
        self.todos_papeis = set()

    def treinar(self, grids_papel):
        for grid in grids_papel:
            h, w = len(grid), len(grid[0])
            for y in range(h):
                for x in range(w):
                    tok = grid[y][x]
                    if tok == 'F':
                        continue
                    self.todos_papeis.add(tok)
                    ctx_esq = grid[y][x-1] if x > 0 else 'F'
                    ctx_cima = grid[y-1][x] if y > 0 else 'F'
                    self.transicoes[(ctx_esq, ctx_cima)][tok] += 1
                    self.marginal_esq[ctx_esq] += 1
                    self.marginal_cima[ctx_cima] += 1

    def _prob(self, ctx_esq, ctx_cima, papel):
        total_ctx = sum(self.transicoes[(ctx_esq, ctx_cima)].values())
        if total_ctx == 0:
            total_marg = sum(self.marginal_cima.values())
            return self.marginal_cima.get(papel, 0) / max(total_marg, 1)
        return self.transicoes[(ctx_esq, ctx_cima)][papel] / total_ctx

    def gerar_grid_da_referencia(self, grid_ref, temperatura=0.5, variacao=0.3):
        h = len(grid_ref)
        w = len(grid_ref[0])
        grid_novo = [['F'] * w for _ in range(h)]
        papeis = list(self.todos_papeis)

        for y in range(h):
            for x in range(w):
                ref = grid_ref[y][x]
                ctx_esq = grid_novo[y][x-1] if x > 0 else 'F'
                ctx_cima = grid_novo[y-1][x] if y > 0 else 'F'

                if random.random() < variacao:
                    probs = {}
                    for p in papeis:
                        probs[p] = self._prob(ctx_esq, ctx_cima, p)
                    probs_temp = {p: pr ** (1.0/max(temperatura, 0.01))
                                  for p, pr in probs.items()}
                    total = sum(probs_temp.values())
                    if total > 0:
                        r = random.random() * total
                        acum = 0.0
                        for p, prob in probs_temp.items():
                            acum += prob
                            if r <= acum:
                                grid_novo[y][x] = p
                                break
                    else:
                        grid_novo[y][x] = ref
                else:
                    grid_novo[y][x] = ref

        return grid_novo


def estagio1_silhueta(grids_papel, n_gerados=20):
    """Estágio 1: Markov gera silhuetas novas."""
    print('  [1] Treinando Markov...')
    mcr = MCRGerador()
    mcr.treinar(grids_papel)

    disc = MCRDiscriminador()
    disc.treinar(grids_papel)

    paleta = extrair_paleta(
        [grid_cor for _, grid_cor in []],
        grids_papel
    ) if grids_papel else {}

    resultados = []
    random.seed(42)
    for g in range(n_gerados):
        temp = 0.5 + random.random() * 0.5
        var = 0.1 + random.random() * 0.4
        angulo = random.random() * 2 * math.pi

        grid_ref = grids_papel[g % len(grids_papel)]
        grid_novo = mcr.gerar_grid_da_referencia(grid_ref, temperatura=temp, variacao=var)

        opacos = sum(1 for row in grid_novo for t in row if t != 'F')
        resultado = disc.avaliar(grid_novo)

        resultados.append({
            'grid_papel': grid_novo,
            'score': resultado['score'],
            'opacos': opacos,
            'angulo': angulo,
        })

    return resultados


# ═══════════════════════════════════════════════════════════════
# ESTÁGIO 2: CONTORNOS
# ═══════════════════════════════════════════════════════════════

def estagio2_contornos(grid_papel):
    """Estágio 2: Extrai só bordas (B), remove interior (L).

    Baseado na análise: orc_lab tem 353 pixels (vs 604),
    significando que só as bordas são mantidas.
    """
    h = len(grid_papel)
    w = len(grid_papel[0])
    grid_contorno = [['F'] * w for _ in range(h)]

    for y in range(h):
        for x in range(w):
            if grid_papel[y][x] == 'B':
                grid_contorno[y][x] = 'B'
            elif grid_papel[y][x] == 'L':
                # L vira B se está adjacente a F no grid ORIGINAL
                eh_borda = any(
                    0 <= x+dx < w and 0 <= y+dy < h and
                    grid_papel[y+dy][x+dx] == 'F'
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                )
                if eh_borda:
                    grid_contorno[y][x] = 'B'
                # Senão, vira F (interior removido)

    return grid_contorno


# ═══════════════════════════════════════════════════════════════
# ESTÁGIO 3: DETALHES
# ═══════════════════════════════════════════════════════════════

def estagio3_detalhes(grid_contorno, grid_cor_orig):
    """Estágio 3: Preenche contornos com textura por pixel.

    Baseado na análise: orc_hd tem 132-164 cores (vs 42 do ref),
    significando que cada pixel recebe uma cor ligeiramente diferente.
    """
    h = len(grid_contorno)
    w = len(grid_contorno[0])
    grid_detalhes = [['F'] * w for _ in range(h)]

    # Encontrar centro da silhueta
    centros = []
    for y in range(h):
        for x in range(w):
            if grid_contorno[y][x] != 'F':
                centros.append((x, y))
    if not centros:
        return grid_contorno

    cx = sum(p[0] for p in centros) / len(centros)
    cy = sum(p[1] for p in centros) / len(centros)
    raio_max = max(math.sqrt((x-cx)**2 + (y-cy)**2) for x, y in centros) or 1

    for y in range(h):
        for x in range(w):
            if grid_contorno[y][x] == 'F':
                continue

            # Cor base do contorno
            r, g, b = grid_cor_orig[y][x] if grid_cor_orig[y][x] != (0, 0, 0) else (100, 80, 60)

            # Converter para Lab*
            L, a, bl = rgb_para_lab(r, g, b)

            # Variação baseada na distância ao centro
            dist = math.sqrt((x - cx)**2 + (y - cy)**2) / raio_max
            var_L = int(15 * dist * math.sin(x * 0.8 + y * 0.6))
            var_a = int(10 * dist * math.cos(x * 0.5 - y * 0.7))
            var_bl = int(10 * dist * math.sin(x * 0.3 + y * 0.4))

            novo_L = max(0, min(100, L + var_L))
            novo_a = max(-128, min(127, a + var_a))
            novo_bl = max(-128, min(127, bl + var_bl))

            cr, cg, cb = lab_para_rgb(novo_L, novo_a, novo_bl)
            grid_detalhes[y][x] = (cr, cg, cb)

    return grid_detalhes


# ═══════════════════════════════════════════════════════════════
# ESTÁGIO 4: RECOLOR
# ═══════════════════════════════════════════════════════════════

def estagio4_recolor(grid_detalhes, limiar=25.0):
    """Estágio 4: Simplifica paleta via clustering CIELAB.

    Baseado na análise: orc_pronto tem 84 cores (vs 132 do hd),
    significando que as cores são agrupadas em clusters.
    """
    h = len(grid_detalhes)
    w = len(grid_detalhes[0])

    # Coletar todos os pixels não-F
    pixels_lab = []
    posicoes = []
    for y in range(h):
        for x in range(w):
            if grid_detalhes[y][x] != 'F':
                rgb = grid_detalhes[y][x]
                lab = rgb_para_lab(*rgb)
                pixels_lab.append(lab)
                posicoes.append((x, y))

    if not pixels_lab:
        return grid_detalhes

    # Clusterizar (retorna dict {cluster_id: [(L,a,b), ...]})
    clusters = clusterizar_lab(pixels_lab, limiar=limiar)

    # Calcular cor média de cada cluster em RGB
    cores_finais = {}
    for cid, membros in clusters.items():
        L_med = int(sum(m[0] for m in membros) / len(membros))
        a_med = int(sum(m[1] for m in membros) / len(membros))
        b_med = int(sum(m[2] for m in membros) / len(membros))
        cores_finais[cid] = lab_para_rgb(L_med, a_med, b_med)

    # Mapear cada pixel para o cluster mais próximo
    grid_recolor = [['F'] * w for _ in range(h)]
    for i, (x, y) in enumerate(posicoes):
        lab = pixels_lab[i]
        # Encontrar cluster mais próximo
        melhor_cid = 0
        melhor_dist = float('inf')
        for cid, membros in clusters.items():
            centro = (sum(m[0] for m in membros)/len(membros),
                      sum(m[1] for m in membros)/len(membros),
                      sum(m[2] for m in membros)/len(membros))
            d = delta_e76(lab, centro)
            if d < melhor_dist:
                melhor_dist = d
                melhor_cid = cid
        grid_recolor[y][x] = cores_finais[melhor_cid]

    return grid_recolor


# ═══════════════════════════════════════════════════════════════
# ESTÁGIO 5: NÍTIDO
# ═══════════════════════════════════════════════════════════════

def estagio5_nitido(grid_papel, angulo_hue=0.0, variacao=5):
    """Estágio 5: CIELAB hue rotation por pixel.

    Cada pixel vira uma cor sólida única.
    """
    h = len(grid_papel)
    w = len(grid_papel[0])
    img = Image.new('RGBA', (w, h))
    pixels = []

    for y in range(h):
        for x in range(w):
            papel = grid_papel[y][x]
            if papel == 'F':
                pixels.append((0, 0, 0, 0))
                continue

            # Para nitido, cada pixel B tem sua própria cor base
            # (vinda do estágio anterior)
            r, g, b = 128, 128, 128  # fallback

            L, a, bl = rgb_para_lab(r, g, b)
            raio = math.sqrt(a*a + bl*bl)
            if raio < 3:
                raio = 6
            novo_a = raio * math.cos(angulo_hue)
            novo_b = raio * math.sin(angulo_hue)
            novo_L = L + random.randint(-variacao, variacao)
            cr, cg, cb = lab_para_rgb(novo_L, novo_a, novo_b)
            pixels.append((cr, cg, cb, 255))

    img.putdata(pixels)
    return img


# ═══════════════════════════════════════════════════════════════
# PIPELINE COMPLETA
# ═══════════════════════════════════════════════════════════════

def rodar_pipeline():
    """Executa os 5 estágios em sequência."""
    print('=' * 60)
    print('PIPELINE COMPLETA — 5 Estágios')
    print('=' * 60)

    # Criar diretórios
    dirs = {}
    for nome in ['estagio1_silhueta', 'estagio2_contornos',
                 'estagio3_detalhes', 'estagio4_recolor', 'estagio5_nitido']:
        d = os.path.join(OUT_BASE, nome)
        os.makedirs(d, exist_ok=True)
        dirs[nome] = d

    # ─── Carregar referências ────────────────────────────────
    print('\n--- Carregando 4 orcs referencia ---')
    grids_papel = []
    grids_cor = []

    for ref_path in ORC_REFS:
        if not os.path.exists(ref_path):
            continue
        img = Image.open(ref_path).convert('RGBA')
        if img.size != (32, 32):
            img = img.resize((32, 32), Image.NEAREST)
        gp, gc = tokenizar_papel(img)
        grids_papel.append(gp)
        grids_cor.append(gc)
        opacos = sum(1 for row in gp for t in row if t != 'F')
        print(f'  {os.path.basename(ref_path)}: {opacos} opacos')

    if not grids_papel:
        print('ERRO: Nenhuma referencia encontrada')
        return

    # ─── Estágio 1: Silhueta ─────────────────────────────────
    print('\n--- Estágio 1: Silhueta (Markov) ---')
    silhuetas = estagio1_silhueta(grids_papel, n_gerados=20)
    print(f'  {len(silhuetas)} silhuetas geradas')

    for i, s in enumerate(silhuetas[:5]):
        caminho = os.path.join(dirs['estagio1_silhueta'], f'silhueta_{i:03d}.png')
        img = grid_para_imagem(s['grid_papel'], {'B': (80, 60, 40), 'L': (120, 100, 80)})
        img.save(caminho)
        print(f'  [{i}] opacos={s["opacos"]} score={s["score"]:.3f}')

    # ─── Estágio 2: Contornos ────────────────────────────────
    print('\n--- Estágio 2: Contornos ---')
    contornos = []
    for i, s in enumerate(silhuetas):
        grid_cont = estagio2_contornos(s['grid_papel'])
        contornos.append(grid_cont)
        opacos = sum(1 for row in grid_cont for t in row if t != 'F')
        if i < 5:
            caminho = os.path.join(dirs['estagio2_contornos'], f'contorno_{i:03d}.png')
            img = grid_para_imagem(grid_cont, {'B': (80, 60, 40)})
            img.save(caminho)
            print(f'  [{i}] opacos={opacos} (antes={s["opacos"]})')

    # ─── Estágio 3: Detalhes ─────────────────────────────────
    print('\n--- Estágio 3: Detalhes ---')
    detalhes = []
    for i, (grid_cont, s) in enumerate(zip(contornos, silhuetas)):
        # Usar cor original da referência como base
        ref_idx = i % len(grids_cor)
        grid_det = estagio3_detalhes(grid_cont, grids_cor[ref_idx])
        detalhes.append(grid_det)
        cores = len(set(tuple(c) for row in grid_det for c in row if c != 'F'))
        if i < 5:
            caminho = os.path.join(dirs['estagio3_detalhes'], f'detalhe_{i:03d}.png')
            # Converter grid de cores para imagem
            h = len(grid_det)
            w = len(grid_det[0])
            img = Image.new('RGBA', (w, h))
            pixels = []
            for y in range(h):
                for x in range(w):
                    c = grid_det[y][x]
                    if c == 'F':
                        pixels.append((0, 0, 0, 0))
                    else:
                        pixels.append((*c, 255))
            img.putdata(pixels)
            img.save(caminho)
            print(f'  [{i}] cores={cores}')

    # ─── Estágio 4: Recolor ──────────────────────────────────
    print('\n--- Estágio 4: Recolor ---')
    recolors = []
    for i, grid_det in enumerate(detalhes):
        grid_rec = estagio4_recolor(grid_det, limiar=25.0)
        recolors.append(grid_rec)
        cores = len(set(tuple(c) for row in grid_rec for c in row if c != 'F'))
        if i < 5:
            caminho = os.path.join(dirs['estagio4_recolor'], f'recolor_{i:03d}.png')
            h = len(grid_rec)
            w = len(grid_rec[0])
            img = Image.new('RGBA', (w, h))
            pixels = []
            for y in range(h):
                for x in range(w):
                    c = grid_rec[y][x]
                    if c == 'F':
                        pixels.append((0, 0, 0, 0))
                    else:
                        pixels.append((*c, 255))
            img.putdata(pixels)
            img.save(caminho)
            print(f'  [{i}] cores={cores}')

    # ─── Estágio 5: Nítido ───────────────────────────────────
    print('\n--- Estágio 5: Nítido ---')
    finais = []
    disc = MCRDiscriminador()
    disc.treinar(grids_papel)

    random.seed(42)
    for i, grid_rec in enumerate(recolors):
        angulo = random.random() * 2 * math.pi
        var_cor = random.randint(2, 8)

        # Converter grid de cores para grid de papel para o nitido
        h = len(grid_rec)
        w = len(grid_rec[0])
        grid_para_nitido = [['F'] * w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                if grid_rec[y][x] != 'F':
                    grid_para_nitido[y][x] = 'B'

        # Gerar nitido usando as cores do recolor como paleta
        img = Image.new('RGBA', (w, h))
        pixels = []
        for y in range(h):
            for x in range(w):
                c = grid_rec[y][x]
                if c == 'F':
                    pixels.append((0, 0, 0, 0))
                    continue
                r, g, b = c
                L, a, bl = rgb_para_lab(r, g, b)
                raio = math.sqrt(a*a + bl*bl)
                if raio < 3:
                    raio = 6
                novo_a = raio * math.cos(angulo)
                novo_b = raio * math.sin(angulo)
                novo_L = L + random.randint(-var_cor, var_cor)
                cr, cg, cb = lab_para_rgb(novo_L, novo_a, novo_b)
                pixels.append((cr, cg, cb, 255))
        img.putdata(pixels)

        resultado = disc.avaliar(grid_para_nitido)
        caminho = os.path.join(dirs['estagio5_nitido'], f'nitido_{i:03d}.png')
        img.save(caminho)
        finais.append({'score': resultado['score'], 'idx': i})

        if i < 5:
            print(f'  [{i}] score={resultado["score"]:.3f} angulo={angulo:.2f}')

    # ─── Avaliação Final ─────────────────────────────────────
    print('\n--- Avaliação Final ---')
    scores = [f['score'] for f in finais]
    print(f'  Score médio: {sum(scores)/len(scores):.3f}')
    print(f'  Score min: {min(scores):.3f}')
    print(f'  Score max: {max(scores):.3f}')
    print(f'  Aceitáveis (>0.5): {sum(1 for s in scores if s > 0.5)}/{len(scores)}')

    melhor = max(finais, key=lambda r: r['score'])
    print(f'\n  Melhor: [{melhor["idx"]}] score={melhor["score"]:.3f}')

    print(f'\nResultados: {OUT_BASE}')
    print('=' * 60)


if __name__ == '__main__':
    rodar_pipeline()
