#!/usr/bin/env python3
"""
teste_regioes_orc — Validação do extrator de regiões anatômicas nos 4 orcs.
Visualiza bounding boxes sobrepostas ao sprite original.
"""
import os
from collections import Counter, defaultdict
from PIL import Image, ImageDraw, ImageFont

from mcr.regioes_anatomicas import (
    cortar_em_regioes, projetar_densidade, encontrar_vales,
    alinhar_regioes, resumir_regioes, fingerprint_regiao, comparar_regioes,
)

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

OUT_DIR = os.path.join(_BASE, 'poc_output', 'regioes_orc')
os.makedirs(OUT_DIR, exist_ok=True)

# ─── Tokenização em papel ───────────────────────────────────

def tokenizar_papel(img):
    if img.mode != 'RGBA': img = img.convert('RGBA')
    w, h = 32, 32; p = img.load(); MAGENTA = (255, 0, 255)
    am = []
    for x in range(w):
        if p[x, 0][3] > 128: am.append(p[x, 0][:3])
        if p[x, h-1][3] > 128: am.append(p[x, h-1][:3])
    for y in range(h):
        if p[0, y][3] > 128: am.append(p[0, y][:3])
        if p[w-1, y][3] > 128: am.append(p[w-1, y][:3])
    bg = Counter(am).most_common(1)[0][0] if am else MAGENTA
    grid_papel = [['F']*w for _ in range(h)]
    grid_cor = [[(0,0,0)]*w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r, g, b, a = p[x, y]
            if a < 128 or (r, g, b) == MAGENTA or (r, g, b) == bg:
                grid_papel[y][x] = 'F'; continue
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


# ─── Visualização ───────────────────────────────────────────

CORES_REGIOES = [
    (255, 50, 50),   # vermelho
    (50, 255, 50),   # verde
    (50, 50, 255),   # azul
    (255, 255, 50),  # amarelo
    (255, 50, 255),  # rosa
    (50, 255, 255),  # ciano
    (255, 128, 50),  # laranja
    (128, 50, 255),  # roxo
    (50, 255, 128),  # verde agua
    (255, 128, 128), # rosa claro
]


def visualizar_regioes(img, regioes, nome, vales_x=None, vales_y=None):
    """Salva imagem com bounding boxes das regiões sobrepostas ao sprite."""
    # Escalar 4x para visualização
    escala = 8
    w, h = img.size
    img_big = img.resize((w*escala, h*escala), Image.NEAREST)
    
    draw = ImageDraw.Draw(img_big)
    
    # Desenhar vales como linhas tracejadas
    if vales_x:
        for vx in vales_x:
            x_px = vx * escala + escala//2
            for y_px in range(0, h*escala, 6):
                draw.line([(x_px, y_px), (x_px, min(y_px+3, h*escala-1))],
                         fill=(255, 255, 255), width=1)
    
    if vales_y:
        for vy in vales_y:
            y_px = vy * escala + escala//2
            for x_px in range(0, w*escala, 6):
                draw.line([(x_px, y_px), (min(x_px+3, w*escala-1), y_px)],
                         fill=(255, 255, 255), width=1)
    
    # Desenhar bounding boxes
    for i, reg in enumerate(regioes):
        cor = CORES_REGIOES[i % len(CORES_REGIOES)]
        x1, y1, x2, y2 = reg['bbox']
        # Bounding box
        for t in range(2):  # borda grossa
            draw.rectangle([
                (x1*escala - t, y1*escala - t),
                ((x2+1)*escala + t, (y2+1)*escala + t)
            ], outline=cor)
        # Label
        label = f"R{reg['id']}"
        draw.text((x1*escala + 2, y1*escala + 2), label, fill=cor)
    
    caminho = os.path.join(OUT_DIR, f'{nome}_regioes.png')
    img_big.save(caminho)
    return caminho


def visualizar_densidade(dens_x, dens_y, nome):
    """Salva gráfico da densidade de projeção."""
    w_img = max(len(dens_y) * 20, 400)
    h_img = max(len(dens_x) * 20, 400)
    
    img = Image.new('RGB', (w_img + 100, h_img + 100), (20, 20, 30))
    draw = ImageDraw.Draw(img)
    
    max_dx = max(dens_x) if dens_x else 1
    max_dy = max(dens_y) if dens_y else 1
    
    # Densidade Y (horizontal, eixo X)
    for x, d in enumerate(dens_y):
        bar_h = int(d / max_dy * (h_img // 2 - 10))
        x_px = 50 + x * 20
        y_base = 50 + h_img // 2
        draw.rectangle([x_px, y_base - bar_h, x_px + 16, y_base], fill=(100, 150, 255))
    
    # Densidade X (vertical, eixo Y)
    for y, d in enumerate(dens_x):
        bar_w = int(d / max_dx * (w_img // 2 - 10))
        y_px = 50 + y * 20
        x_base = 50
        draw.rectangle([x_base, y_px, x_base + bar_w, y_px + 16], fill=(255, 150, 100))
    
    caminho = os.path.join(OUT_DIR, f'{nome}_densidade.png')
    img.save(caminho)
    return caminho


# ============================================================
# MAIN
# ============================================================
print('=' * 60)
print('VALIDACAO: Extrator de Regioes nos 4 Orcs')
print('=' * 60)

# 1. Carregar orcs
print('\n--- 1. Carregando orcs ---')
orc_paths = [
    ('orc_dir0', os.path.join(_BASE, 'poc_output', 'orc_hue_ref_0.png')),
    ('orc_dir1', os.path.join(_BASE, 'poc_output', 'orc_hue_ref_1.png')),
    ('orc_ref', os.path.join(_BASE, 'poc_output', 'orc_nitido_ref.png')),
    ('orc_ref_big', os.path.join(_BASE, 'poc_output', 'orc_nitido_ref_big.png')),
]

dados = []
for nome, path in orc_paths:
    if not os.path.exists(path):
        print(f'  {nome}: NAO ENCONTRADO')
        continue
    img = Image.open(path).convert('RGBA')
    if img.size != (32, 32):
        img = img.resize((32, 32), Image.NEAREST)
    gp, gc = tokenizar_papel(img)
    dados.append({'nome': nome, 'img': img, 'grid_papel': gp, 'grid_cor': gc})
    opacos = sum(1 for row in gp for t in row if t != 'F')
    print(f'  {nome}: {opacos} opacos')

print(f'  Total: {len(dados)} orcs')

# 2. Extrair regiões de cada
print('\n--- 2. Extraindo regioes ---')
todas_regioes = []
for d in dados:
    regioes = cortar_em_regioes(d['grid_papel'], d['grid_cor'])
    d['regioes'] = regioes
    todas_regioes.append(regioes)
    print(f'  {d["nome"]}: {resumir_regioes(regioes)}')

# 3. Projeção de densidade e vales
print('\n--- 3. Projecao de densidade ---')
for d in dados:
    dens_x, dens_y = projetar_densidade(d['grid_papel'])
    vales_y = encontrar_vales(dens_x, suavizacao=2, min_pico=2)
    vales_x = encontrar_vales(dens_y, suavizacao=2, min_pico=2)
    print(f'  {d["nome"]}: vales_y={vales_y} vales_x={vales_x}')
    d['dens_x'] = dens_x
    d['dens_y'] = dens_y
    d['vales_x'] = vales_x
    d['vales_y'] = vales_y

# 4. Visualizar regiões
print('\n--- 4. Visualizando regioes ---')
for d in dados:
    caminho = visualizar_regioes(
        d['img'], d['regioes'], d['nome'],
        vales_x=d['vales_x'], vales_y=d['vales_y']
    )
    print(f'  {d["nome"]}: {caminho}')

# 5. Visualizar densidade
print('\n--- 5. Visualizando densidade ---')
for d in dados:
    caminho = visualizar_densidade(d['dens_x'], d['dens_y'], d['nome'])
    print(f'  {d["nome"]}: {caminho}')

# 6. Alinhar regiões e verificar invariância
print('\n--- 6. Invariancia entre regioes ---')
regioes_alinhadas = alinhar_regioes(todas_regioes)

# Comparar regiões correspondentes entre sprites
if all(len(r) > 0 for r in regioes_alinhadas):
    n_reg = min(len(r) for r in regioes_alinhadas)
    print(f'  Regioes por sprite: {[len(r) for r in regioes_alinhadas]}')
    print(f'  Comparando {n_reg} regioes correspondentes:')
    
    for i in range(n_reg):
        scores = []
        for j in range(1, len(regioes_alinhadas)):
            s = comparar_regioes(regioes_alinhadas[0][i], regioes_alinhadas[j][i])
            scores.append(s)
        media = sum(scores) / len(scores) if scores else 0
        r0 = regioes_alinhadas[0][i]
        print(f'    R{i}: prop_b={r0["prop_b"]:.2f} area={r0["area"]} '
              f'WxH={r0["largura"]}x{r0["altura"]} '
              f'similaridade={media:.3f}')
else:
    print('  Regioes nao alinhadas (numeros diferentes)')

# 7. Fingerprints
print('\n--- 7. Fingerprints das regioes ---')
for d in dados:
    fps = [fingerprint_regiao(r) for r in d['regioes']]
    print(f'  {d["nome"]}: {fps}')

print(f'\nResultados: {OUT_DIR}')
print('=' * 60)
