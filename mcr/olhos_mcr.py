"""
mcr.olhos_mcr -- Olhos do MCR: representacao ASCII rica de sprites.

Converte sprites RGBA em representacoes ASCII multi-camada:
  - Camada 1: Papel B/L/F (estrutura)
  - Camada 2: Luminancia L* 0-9 (claridade/escuro)
  - Camada 3: Matiz R/Y/G/C/B/M (identidade cromatica)
  - Perfil colunar: sumario 1D da forma (como barrinhas do som)
  - Diagnostico: score, paleta, metricas

Filosofia: Input -> Tokenizador -> MCR -> Output
Este modulo e o TOKENIZADOR UNIVERSAL PARA O DOMINIO VISUAL.
"""
import math
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import Counter

from mcr.cielab import rgb_para_lab


def _luminancia_para_char(L):
    """Converte L* (0-100) para caractere 0-9."""
    nivel = min(9, max(0, int(L / 100 * 10)))
    return str(nivel)


def _hue_para_char(a, b):
    """Converte a*b* em banda de matiz: R/Y/G/C/B/M."""
    raio = math.sqrt(a * a + b * b)
    if raio < 3:
        return ' '
    angulo = math.degrees(math.atan2(b, a))
    if angulo < 0:
        angulo += 360
    if angulo < 30:
        return 'R'
    elif angulo < 90:
        return 'Y'
    elif angulo < 150:
        return 'G'
    elif angulo < 210:
        return 'C'
    elif angulo < 270:
        return 'B'
    elif angulo < 330:
        return 'M'
    else:
        return 'R'


def camada_luminancia(grid_papel, grid_cor):
    """Gera camada de luminancia: L* quantizado 0-9."""
    h = len(grid_papel)
    w = len(grid_papel[0]) if h else 0
    resultado = [[' ' for _ in range(w)] for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if grid_papel[y][x] == 'F':
                continue
            r, g, b = grid_cor[y][x]
            L, a, bl = rgb_para_lab(r, g, b)
            resultado[y][x] = _luminancia_para_char(L)
    return resultado


def camada_matiz(grid_papel, grid_cor):
    """Gera camada de matiz: bandas R/Y/G/C/B/M."""
    h = len(grid_papel)
    w = len(grid_papel[0]) if h else 0
    resultado = [[' ' for _ in range(w)] for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if grid_papel[y][x] == 'F':
                continue
            r, g, b = grid_cor[y][x]
            L, a, bl = rgb_para_lab(r, g, b)
            resultado[y][x] = _hue_para_char(a, bl)
    return resultado


def perfil_colunar(grid_papel, grid_cor, n_colunas=16):
    """Gera perfil colunar -- como um espectrograma de audio.

    Para cada grupo de colunas, calcula:
      - N: numero de pixels opacos
      - B/L: proporcao borda vs luz
      - L* medio
      - Hue dominante
    """
    h = len(grid_papel)
    w = len(grid_papel[0]) if h else 0
    if w == 0:
        return {}
    largura_bin = max(1, w // n_colunas)
    bins = list(range(0, w, largura_bin))
    if len(bins) > n_colunas:
        bins = bins[:n_colunas]
    resultado = {'col': [], 'n_opacos': [], 'prop_bl': [], 'l_media': [], 'hue_dom': []}
    for i, x_inicio in enumerate(bins):
        x_fim = min(x_inicio + largura_bin, w)
        n_opacos = 0
        n_borda = 0
        l_soma = 0.0
        hues = []
        for y in range(h):
            for x in range(x_inicio, x_fim):
                papel = grid_papel[y][x]
                if papel == 'F':
                    continue
                n_opacos += 1
                if papel == 'B':
                    n_borda += 1
                r, g, b = grid_cor[y][x]
                L, a, bl = rgb_para_lab(r, g, b)
                l_soma += L
                hues.append(_hue_para_char(a, bl))
        resultado['col'].append(x_inicio)
        resultado['n_opacos'].append(n_opacos)
        resultado['prop_bl'].append(round(n_borda / max(n_opacos, 1), 2))
        resultado['l_media'].append(round(l_soma / max(n_opacos, 1), 1))
        if hues:
            contagem = Counter(hues)
            dom = contagem.most_common(1)[0][0]
        else:
            dom = ' '
        resultado['hue_dom'].append(dom)
    return resultado


def _lab_para_rgb_simples(L, a, b):
    """Conversao simples L*a*b* -> RGB."""
    g_ = (L + 16) / 116
    r_ = a / 500 + g_
    b_ = g_ - b / 200
    def f_inv(t):
        return t ** 3 if t > 0.008856 else (t - 16 / 116) / 7.787
    r = max(0, min(255, int(round((1.055 * f_inv(r_) * 95.047 / 100 - 0.055) * 255))))
    g = max(0, min(255, int(round((1.055 * f_inv(g_) * 100 / 100 - 0.055) * 255))))
    bl = max(0, min(255, int(round((1.055 * f_inv(b_) * 108.883 / 100 - 0.055) * 255))))
    return r, g, bl


def resumo_diagnostico(grid_papel, grid_cor):
    """Gera diagnostico detalhado do sprite."""
    contagem = Counter()
    labs_por_papel = {}
    h = len(grid_papel)
    w = len(grid_papel[0]) if h else 0
    for y in range(h):
        for x in range(w):
            papel = grid_papel[y][x]
            if papel == 'F':
                continue
            contagem[papel] += 1
            r, g, b = grid_cor[y][x]
            L, a, bl = rgb_para_lab(r, g, b)
            if papel not in labs_por_papel:
                labs_por_papel[papel] = []
            labs_por_papel[papel].append((L, a, bl))
    paleta = {}
    stats_l = {}
    for papel, labs in labs_por_papel.items():
        Ls = sorted([l[0] for l in labs])
        as_ = sorted([l[1] for l in labs])
        bs = sorted([l[2] for l in labs])
        n = len(Ls)
        paleta[papel] = (Ls[n // 2], as_[n // 2], bs[n // 2])
        L_mean = sum(Ls) / len(Ls)
        L_dp = (sum((x - L_mean)**2 for x in Ls) / len(Ls)) ** 0.5
        stats_l[papel] = (round(L_mean, 1), round(L_dp, 1))
    paleta_rgb = {}
    for papel, (L, a, b) in paleta.items():
        paleta_rgb[papel] = _lab_para_rgb_simples(L, a, b)
    return {'contagem': dict(contagem), 'paleta_lab': paleta, 'paleta_rgb': paleta_rgb, 'stats_l': stats_l}


def _grid_para_linhas(grid):
    """Converte grid 2D para lista de strings."""
    return [''.join(row) for row in grid]


def sprite_para_ascii_rich(grid_papel, grid_cor, nome='', score=None):
    """Converte sprite em ASCII rico com 5 secoes.

    Secoes:
      1. PAPEL -- estrutura B/L/F
      2. LUMINANCE -- claridade 0-9 por pixel
      3. MATIZ -- banda R/Y/G/C/B/M por pixel
      4. PERFIL COLUNAR -- barrinhas do som
      5. DIAGNOSTICO -- paleta, contagens, score
    """
    linhas = []
    # 1. Cabecalho + papel
    titulo = '[PAPEL]' if not nome else '[PAPEL] ' + nome
    linhas.append(titulo)
    linhas.extend(_grid_para_linhas(grid_papel))
    linhas.append('')
    # 2. Luminancia
    lum = camada_luminancia(grid_papel, grid_cor)
    linhas.append('[LUMINANCE L* 0-9]')
    linhas.extend(_grid_para_linhas(lum))
    linhas.append('')
    # 3. Matiz
    mat = camada_matiz(grid_papel, grid_cor)
    linhas.append('[MATIZ R/Y/G/C/B/M]')
    linhas.extend(_grid_para_linhas(mat))
    linhas.append('')
    # 4. Perfil colunar
    perf = perfil_colunar(grid_papel, grid_cor, n_colunas=16)
    if perf:
        linhas.append('[PERFIL COLUNAR]')
        linhas.append('Col |Npx |B/L |L*  |Hue')
        linhas.append('----+----+----+----+----')
        for i in range(len(perf['col'])):
            linhas.append('%3d |%4d |%.2f|%5.1f| %s' % (
                perf['col'][i], perf['n_opacos'][i],
                perf['prop_bl'][i], perf['l_media'][i],
                perf['hue_dom'][i]))
        linhas.append('')
    # 5. Diagnostico
    diag = resumo_diagnostico(grid_papel, grid_cor)
    linhas.append('[DIAGNOSTICO]')
    for papel, rgb in diag['paleta_rgb'].items():
        lab = diag['paleta_lab'][papel]
        stats = diag['stats_l'].get(papel, (0, 0))
        linhas.append('  %s: RGB(%d,%d,%d) L*=%.0f a=%.0f b=%.0f L_med=%.0f+/-%.0f' % (
            papel, rgb[0], rgb[1], rgb[2], lab[0], lab[1], lab[2], stats[0], stats[1]))
    if score is not None:
        linhas.append('  Score: %.3f' % score)
    linhas.append('')
    n_b = sum(1 for row in grid_papel for t in row if t == 'B')
    n_l = sum(1 for row in grid_papel for t in row if t == 'L')
    n_f = sum(1 for row in grid_papel for t in row if t == 'F')
    linhas.append('  Total: B=%d L=%d F=%d opacos=%d' % (n_b, n_l, n_f, n_b + n_l))
    return '\n'.join(linhas)


def sprite_para_ascii_compacto(grid_papel, grid_cor, nome='', score=None):
    """Formato compacto: papel + lum + matiz lado a lado (4 linhas)."""
    linhas = []
    cab = nome if nome else 'sprite'
    if score is not None:
        cab += ' score=%.3f' % score
    n_b = sum(1 for row in grid_papel for t in row if t == 'B')
    n_l = sum(1 for row in grid_papel for t in row if t == 'L')
    cab += ' B=%d L=%d' % (n_b, n_l)
    linhas.append('[' + cab + ']')
    linhas.append('Papel: ' + '  '.join(_grid_para_linhas(grid_papel)))
    lum = camada_luminancia(grid_papel, grid_cor)
    linhas.append('Lum:   ' + '  '.join(_grid_para_linhas(lum)))
    mat = camada_matiz(grid_papel, grid_cor)
    linhas.append('Matiz: ' + '  '.join(_grid_para_linhas(mat)))
    return '\n'.join(linhas)


def categoria_para_ascii_rich(categoria, sprites_rgba, n=10):
    """Gera ASCII rico para N sprites de uma categoria."""
    from mcr.sprite_corpus import extrair_grid_papel
    linhas = []
    linhas.append('=' * 60)
    linhas.append('CATEGORIA: %s (%d sprites)' % (categoria, len(sprites_rgba)))
    linhas.append('=' * 60)
    for i, arr in enumerate(sprites_rgba[:n]):
        gp, gc = extrair_grid_papel(arr)
        linhas.append('')
        linhas.append('--- SPRITE %d/%d ---' % (i + 1, min(n, len(sprites_rgba))))
        linhas.append(sprite_para_ascii_rich(gp, gc, nome='%s #%d' % (categoria, i)))
    return '\n'.join(linhas)
