#!/usr/bin/env python3
"""Teste do Tokenizador Hierárquico no sprite_0 (item: 651 opacos, 63 cores)."""
import math, os, sys
from collections import Counter, defaultdict

from mcr.cielab import rgb_para_lab, delta_e76, clusterizar_lab, detectar_picos
from mcr.template_entropico import entropia_shannon
from mcr.tokenizador_hierarquico import (
    extrair_regioes, extrair_relacoes, ordenar_regioes,
    tokenizar_hierarquico, resumir_hierarquico,
    regioes_para_grid, regioes_para_grid_com_borda,
)
from PIL import Image

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

OUT_DIR = os.path.join(_BASE, 'poc_output', 'resultado')
os.makedirs(OUT_DIR, exist_ok=True)


def tokenizar_para_grid(img):
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
    lums, labs, rgbs, pos = [], [], [], []
    for y in range(h):
        for x in range(w):
            r, g, b, a = p[x, y]
            if a > 128 and (r, g, b) != MAGENTA and (r, g, b) != bg:
                lums.append(int(0.299*r + 0.587*g + 0.114*b))
                labs.append(rgb_para_lab(r, g, b))
                rgbs.append((r, g, b))
                pos.append((y, x))
    if len(lums) < 3:
        return [['F']*w for _ in range(h)], {}
    BINS_L = 12
    hist_l = [0]*BINS_L
    for l in lums: hist_l[min(l*BINS_L//256, BINS_L-1)] += 1
    picos_l = detectar_picos(hist_l, BINS_L)
    clusters = clusterizar_lab(labs, 20.0)
    centros = {}
    for cid, memb in clusters.items():
        if memb: centros[cid] = (sum(m[0] for m in memb)/len(memb), sum(m[1] for m in memb)/len(memb), sum(m[2] for m in memb)/len(memb))
    cids_ord = sorted(centros.keys(), key=lambda c: centros[c][0])
    mapa_centro = {old: new for new, old in enumerate(cids_ord)}
    grid = [['F']*w for _ in range(h)]
    paleta = defaultdict(list)
    for idx, (y, x) in enumerate(pos):
        r, g, b = rgbs[idx]; lab = labs[idx]; lum = lums[idx]
        eh_borda = any(0 <= x+dx < w and 0 <= y+dy < h and (
            p[x+dx, y+dy][3] < 128 or p[x+dx, y+dy][:3] == MAGENTA or p[x+dx, y+dy][:3] == bg
        ) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)])
        if eh_borda:
            grid[y][x] = 'B'; paleta['B'].append((r, g, b)); continue
        mn = min(range(len(picos_l)), key=lambda i: abs(lum - picos_l[i]*256//BINS_L))
        mc = 0; md = 9999
        for co, centro in centros.items():
            d = delta_e76(lab, centro)
            if d < md: md = d; mc = mapa_centro[co]
        tok = f'L{mn}C{mc}'
        grid[y][x] = tok; paleta[tok].append((r, g, b))
    return grid, dict(paleta)


# ============================================================
print('=' * 60)
print('TESTE: Tokenizador Hierárquico no sprite_0 (ITEM)')
print('=' * 60)

# 1. Carregar sprite_0
path = os.path.join(_BASE, 'poc_output', 'sprite_0.png')
if not os.path.exists(path):
    print(f'  ERRO: {path} não encontrado')
    sys.exit(1)

img = Image.open(path).convert('RGBA')
print(f'\n--- 1. Sprite carregado ---')
print(f'  sprite_0.png: {img.size}')

# 2. Tokenizar
grid, paleta = tokenizar_para_grid(img)
opacos = sum(1 for row in grid for t in row if t != 'F')
tokens_unicos = set(t for row in grid for t in row if t != 'F')
print(f'\n--- 2. Tokenização ---')
print(f'  Opacos: {opacos}')
print(f'  Tokens únicos: {len(tokens_unicos)}')
print(f'  Paleta: {len(paleta)} cores')

# 3. Extrair regiões em modo 'papel'
print(f'\n--- 3. Regiões (modo papel) ---')
regioes = extrair_regioes(grid, modo='papel')
reg_ord = ordenar_regioes(regioes)
papeis = Counter(r['papel'] for r in reg_ord)
print(f'  Total: {len(reg_ord)} regiões')
print(f'  Papeis: {dict(papeis)}')
for r in reg_ord:
    print(f'    [{r["id"]}] papel={r["papel"]} area={r["area"]} centroide=({r["centroide"][0]:.0f},{r["centroide"][1]:.0f})')

# 4. Extrair regiões em modo 'token'
print(f'\n--- 4. Regiões (modo token - textura) ---')
regioes_token = extrair_regioes(grid, modo='token')
papeis_t = Counter(r['papel'] for r in regioes_token)
print(f'  Total: {len(regioes_token)} regiões')
print(f'  Papeis: {dict(papeis_t)}')

# 5. Relações
relacoes = extrair_relacoes(reg_ord)
tipos = Counter(r['tipo_adj'] for r in relacoes)
print(f'\n--- 5. Relações ---')
print(f'  Total: {len(relacoes)}')
print(f'  Tipos: {dict(tipos)}')

# 6. Visualizar grid de regiões
print(f'\n--- 6. Mapa de regiões ---')
papeis_grid = [['F']*32 for _ in range(32)]
for reg in reg_ord:
    for (x, y) in reg['pixels']:
        if 0 <= x < 32 and 0 <= y < 32:
            papel_char = 'L' if reg['papel'] == 'L' else 'B'
            papeis_grid[y][x] = papel_char

for y in range(32):
    row = ''.join(papeis_grid[y])
    print(f'{y:02d} {row}')

# 7. Reconstruir e salvar
print(f'\n--- 7. Reconstrução ---')
grid_reconstruido = regioes_para_grid(reg_ord, 32, 32)
opacos_rec = sum(1 for row in grid_reconstruido for t in row if t != 'F')
print(f'  Opacos reconstruídos: {opacos_rec}/{opacos}')

grid_borda = regioes_para_grid_com_borda(reg_ord, 32, 32)
img_out = Image.new('RGBA', (32, 32))
pixels = []
for y in range(32):
    for x in range(32):
        tok = grid_borda[y][x]
        if tok == 'F':
            pixels.append((0, 0, 0, 0))
        elif tok == 'B':
            pixels.append((100, 100, 100, 255))
        elif tok == 'D':
            pixels.append((200, 200, 100, 255))
        else:
            pixels.append((150, 150, 200, 255))
img_out.putdata(pixels)
rec_path = os.path.join(OUT_DIR, 'sprite0_regioes.png')
img_out.save(rec_path)
print(f'  Mapa de regiões salvo: {rec_path}')

print(f'\n--- FIM ---')
print(f'  Hierarquia: N0={opacos}px N1={len(reg_ord)}regiões N2={len(relacoes)}relações')
