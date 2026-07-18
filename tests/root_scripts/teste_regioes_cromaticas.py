#!/usr/bin/env python3
"""
teste_regioes_cromaticas — Validação do extrator de regiões cromáticas.

Carrega 4 orcs + 9 shields, extrai regiões por CIELAB clustering,
visualiza bounding boxes, e mede invariância/discriminação.
"""
import os, sys, math
from collections import Counter, defaultdict
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcr.regioes_anatomicas import (
    extrair_regioes_cromaticas, fingerprint_cromatico,
    comparar_regioes_cromaticas, resumir_regioes,
)
from mcr.cielab import rgb_para_lab, delta_e76

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

OUT_DIR = os.path.join(_BASE, 'poc_output', 'regioes_cromaticas')
os.makedirs(OUT_DIR, exist_ok=True)


# ─── Helpers ─────────────────────────────────────────────────

def img_para_grid_cor(img):
    """Converte PIL Image para grid 2D de cores RGB."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    img = img.resize((32, 32), Image.NEAREST)
    p = img.load()
    w, h = img.size
    return [[p[x, y][:3] for x in range(w)] for y in range(h)]


def img_para_grid_papel(img):
    """Converte PIL Image para grid 2D de papéis F/B/L."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    img = img.resize((32, 32), Image.NEAREST)
    w, h = 32, 32
    p = img.load()
    MAGENTA = (255, 0, 255)

    # Detectar fundo
    am = []
    for x in range(w):
        if p[x, 0][3] > 128:
            am.append(p[x, 0][:3])
        if p[x, h - 1][3] > 128:
            am.append(p[x, h - 1][:3])
    for y in range(h):
        if p[0, y][3] > 128:
            am.append(p[0, y][:3])
        if p[w - 1, y][3] > 128:
            am.append(p[w - 1, y][:3])
    bg = Counter(am).most_common(1)[0][0] if am else MAGENTA

    grid = [['F'] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r, g, b, a = p[x, y]
            if a < 128 or (r, g, b) == MAGENTA or (r, g, b) == bg:
                grid[y][x] = 'F'
                continue
            eh_borda = any(
                0 <= x + dx < w and 0 <= y + dy < h and (
                    p[x + dx, y + dy][3] < 128 or
                    p[x + dx, y + dy][:3] == MAGENTA or
                    p[x + dx, y + dy][:3] == bg
                )
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
            )
            grid[y][x] = 'B' if eh_borda else 'L'
    return grid


CORES_DEBUG = [
    (255, 50, 50), (50, 255, 50), (50, 50, 255),
    (255, 255, 50), (255, 50, 255), (50, 255, 255),
    (255, 128, 50), (128, 50, 255), (50, 255, 128),
    (255, 128, 128), (128, 255, 128), (128, 128, 255),
]


def visualizar_regioes(img, regioes, nome):
    """Salva PNG com bounding boxes coloridas sobre o sprite."""
    escala = 8
    w, h = img.size
    img_big = img.resize((w * escala, h * escala), Image.NEAREST)
    draw = ImageDraw.Draw(img_big)

    for i, reg in enumerate(regioes):
        cor = CORES_DEBUG[i % len(CORES_DEBUG)]
        x1, y1, x2, y2 = reg['bbox']
        for t in range(2):
            draw.rectangle([
                (x1 * escala - t, y1 * escala - t),
                ((x2 + 1) * escala + t, (y2 + 1) * escala + t)
            ], outline=cor)
        label = f"R{reg['id']}"
        draw.text((x1 * escala + 2, y1 * escala + 2), label, fill=cor)

    caminho = os.path.join(OUT_DIR, f'{nome}_regioes.png')
    img_big.save(caminho)
    return caminho


# ============================================================
# MAIN
# ============================================================
print('=' * 60)
print('VALIDACAO: Extrator de Regioes Cromaticas')
print('=' * 60)

# 1. Carregar sprites
print('\n--- 1. Carregando sprites ---')
sprites = []

# 4 orcs
orc_paths = [
    ('orc_dir0', os.path.join(_BASE, 'poc_output', 'orc_hue_ref_0.png')),
    ('orc_dir1', os.path.join(_BASE, 'poc_output', 'orc_hue_ref_1.png')),
    ('orc_ref', os.path.join(_BASE, 'poc_output', 'orc_nitido_ref.png')),
    ('orc_ref_big', os.path.join(_BASE, 'poc_output', 'orc_nitido_ref_big.png')),
]
for nome, path in orc_paths:
    if os.path.exists(path):
        img = Image.open(path)
        sprites.append({'nome': nome, 'img': img, 'tipo': 'orc'})
        print(f'  {nome}: OK')

# 9 shields (usando shield_original que são os 9 shields de referência)
shield_dir = os.path.join(_BASE, 'poc_output')
for i in range(9):
    path = os.path.join(shield_dir, f'shield_original_{i}.png')
    if os.path.exists(path):
        img = Image.open(path)
        sprites.append({'nome': f'shield_{i}', 'img': img, 'tipo': 'shield'})
        print(f'  shield_{i}: OK')

print(f'  Total: {len(sprites)} sprites')

# 2. Extrair regiões de cada
print('\n--- 2. Extraindo regioes cromaticas ---')
for s in sprites:
    grid_cor = img_para_grid_cor(s['img'])
    grid_papel = img_para_grid_papel(s['img'])
    regioes = extrair_regioes_cromaticas(grid_cor, grid_papel, area_minima=5)
    s['regioes'] = regioes
    s['grid_cor'] = grid_cor
    s['grid_papel'] = grid_papel
    fps = [fingerprint_cromatico(r) for r in regioes]
    print(f'  {s["nome"]}: {len(regioes)} regioes | {", ".join(fps[:5])}{"..." if len(fps) > 5 else ""}')

# 3. Visualizar
print('\n--- 3. Visualizando regioes ---')
for s in sprites:
    caminho = visualizar_regioes(s['img'], s['regioes'], s['nome'])
    print(f'  {s["nome"]}: {caminho}')

# 4. Invariância entre orcs similares
print('\n--- 4. Invariancia entre orcs similares ---')
orcs_similares = [s for s in sprites if s['nome'] in ('orc_dir1', 'orc_ref', 'orc_ref_big')]
orc_diferente = [s for s in sprites if s['nome'] == 'orc_dir0']

if orcs_similares:
    n_reg_similar = [len(s['regioes']) for s in orcs_similares]
    print(f'  Orcs similares: {n_reg_similar} regioes')
    if orc_diferente:
        n_reg_diff = len(orc_diferente[0]['regioes'])
        print(f'  Orc diferente: {n_reg_diff} regioes')

    # Comparar regiões correspondentes
    if all(len(s['regioes']) > 0 for s in orcs_similares):
        n_reg = min(len(s['regioes']) for s in orcs_similares)
        scores = []
        for i in range(n_reg):
            for j in range(1, len(orcs_similares)):
                s = comparar_regioes_cromaticas(
                    orcs_similares[0]['regioes'][i],
                    orcs_similares[j]['regioes'][i]
                )
                scores.append(s)
        media = sum(scores) / len(scores) if scores else 0
        print(f'  Similaridade media: {media:.3f}')

# 5. Invariância entre shields
print('\n--- 5. Invariancia entre shields ---')
shields = [s for s in sprites if s['tipo'] == 'shield']
if shields:
    n_reg_shields = [len(s['regioes']) for s in shields]
    print(f'  Shields: {n_reg_shields} regioes')

    # Comparar regiões correspondentes entre shields
    if all(len(s['regioes']) > 0 for s in shields):
        n_reg = min(len(s['regioes']) for s in shields)
        scores_cor = []
        scores_geom = []
        for i in range(n_reg):
            for j in range(1, len(shields)):
                s = comparar_regioes_cromaticas(
                    shields[0]['regioes'][i],
                    shields[j]['regioes'][i]
                )
                scores_cor.append(s)

                # Propriedades geométricas (área, centroide, excentricidade)
                r1, r2 = shields[0]['regioes'][i], shields[j]['regioes'][i]
                d_area = abs(r1['area'] - r2['area']) / max(r1['area'], r2['area'], 1)
                d_excc = abs(r1['excentricidade'] - r2['excentricidade']) / max(r1['excentricidade'], r2['excentricidade'], 1)
                scores_geom.append(1.0 - (d_area * 0.5 + d_excc * 0.5))

        media_cor = sum(scores_cor) / len(scores_cor) if scores_cor else 0
        media_geom = sum(scores_geom) / len(scores_geom) if scores_geom else 0
        print(f'  Similaridade cromatica: {media_cor:.3f}')
        print(f'  Similaridade geometrica: {media_geom:.3f}')

# 6. Resumo estatístico
print('\n--- 6. Resumo estatistico ---')
for s in sprites:
    regioes = s['regioes']
    if not regioes:
        print(f'  {s["nome"]}: 0 regioes')
        continue
    areas = [r['area'] for r in regioes]
    exccs = [r['excentricidade'] for r in regioes]
    labs = [r['cor_media_lab'] for r in regioes]
    print(f'  {s["nome"]}: {len(regioes)}reg areas={areas} excc={[f"{e:.1f}" for e in exccs]}')

print(f'\nResultados: {OUT_DIR}')
print('=' * 60)
