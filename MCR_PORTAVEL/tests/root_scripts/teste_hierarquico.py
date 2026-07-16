#!/usr/bin/env python3
"""Teste do Tokenizador Hierárquico nos 9 shields e sprite_0 (item)."""
import math, os
from collections import Counter, defaultdict

from mcr.cielab import rgb_para_lab, delta_e76, clusterizar_lab, detectar_picos
from mcr.template_entropico import entropia_shannon, extrair_template_entropico, gerar_do_template, resumir_template
from mcr.tokenizador_hierarquico import (
    extrair_regioes, extrair_relacoes, propriedades_para_vetor,
    token_linear_para_grid, tokenizar_hierarquico, resumir_hierarquico
)
from PIL import Image

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

OUT_DIR = os.path.join(_BASE, 'poc_output')


def tokenizar_para_grid(img):
    """Tokeniza sprite e retorna grid 2D + paleta."""
    if img.mode != 'RGBA': img = img.convert('RGBA')
    w, h = 32, 32; p = img.load()
    MAGENTA = (255, 0, 255)

    # Detectar bg dos pixels da borda
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
        if memb:
            centros[cid] = (
                sum(m[0] for m in memb)/len(memb),
                sum(m[1] for m in memb)/len(memb),
                sum(m[2] for m in memb)/len(memb),
            )
    cids_ord = sorted(centros.keys(), key=lambda c: centros[c][0])
    mapa_centro = {old: new for new, old in enumerate(cids_ord)}

    grid = [['F']*w for _ in range(h)]
    paleta = defaultdict(list)

    for idx, (y, x) in enumerate(pos):
        r, g, b = rgbs[idx]
        lab = labs[idx]
        lum = lums[idx]

        eh_borda = any(
            0 <= x+dx < w and 0 <= y+dy < h and (
                p[x+dx, y+dy][3] < 128 or
                p[x+dx, y+dy][:3] == MAGENTA or
                p[x+dx, y+dy][:3] == bg
            )
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
        )
        if eh_borda:
            grid[y][x] = 'B'
            paleta['B'].append((r, g, b))
            continue

        mn = min(range(len(picos_l)), key=lambda i: abs(lum - picos_l[i]*256//BINS_L))
        mc = 0; md = 9999
        for co, centro in centros.items():
            d = delta_e76(lab, centro)
            if d < md:
                md = d
                mc = mapa_centro[co]
        tok = f'L{mn}C{mc}'
        grid[y][x] = tok
        paleta[tok].append((r, g, b))

    return grid, dict(paleta)


# ============================================================
# TESTE PRINCIPAL
# ============================================================
print('=' * 60)
print('TESTE: Tokenizador Hierárquico nos 9 Shields')
print('=' * 60)

# 1. Carregar os 9 shields
print('\n--- 1. Carregando shields ---')
shields = []
for i in range(9):
    path = os.path.join(OUT_DIR, f'shield_ref_{i}.png')
    if os.path.exists(path):
        img = Image.open(path).convert('RGBA')
        shields.append(img)
        print(f'  shield_ref_{i}.png: {img.size}')

print(f'  Total: {len(shields)} shields')
if len(shields) < 3:
    # Fallback: carregar original_00..08
    print('  Fallback: tentando original_00..08')
    for i in range(9):
        path = os.path.join(OUT_DIR, f'original_{i:02d}.png')
        if os.path.exists(path):
            img = Image.open(path).convert('RGBA')
            shields.append(img)
            print(f'  original_{i:02d}.png: {img.size}')

if len(shields) < 3:
    print('  ERRO: Menos de 3 shields encontrados!')
    print('  Tentando sprite_0.png como fallback...')
    path = os.path.join(OUT_DIR, 'sprite_0.png')
    if os.path.exists(path):
        shields = [Image.open(path).convert('RGBA')]
        print(f'  sprite_0.png: {len(shields)} amostra')

# 2. Tokenizar cada shield
print(f'\n--- 2. Tokenizando {len(shields)} sprites ---')
todos_grids = []
todas_paletas = []
for i, img in enumerate(shields):
    grid, pal = tokenizar_para_grid(img)
    todos_grids.append(grid)
    todas_paletas.append(pal)
    
    opacos = sum(1 for row in grid for t in row if t != 'F')
    tokens_unicos = set(t for row in grid for t in row if t != 'F')
    print(f'  Sprite {i}: {opacos}px opacos, {len(tokens_unicos)} tokens unicos, paleta={len(pal)} cores')

# 3. Extrair regiões de cada shield
print(f'\n--- 3. Extraindo regiões (Nível 1) ---')
todas_regioes = []
todas_props = []
for i, grid in enumerate(todos_grids):
    h = tokenizar_hierarquico(grid)
    todas_regioes.append(h['nivel1']['regioes'])
    todas_props.append(h['nivel1']['propriedades'])
    print(f'  Sprite {i}: {resumir_hierarquico(h)}')

# 4. Extrair relações (Nível 2)
print(f'\n--- 4. Extraindo relações (Nível 2) ---')
todas_relacoes = []
for i, grid in enumerate(todos_grids):
    h = tokenizar_hierarquico(grid)
    todas_relacoes.append(h['nivel2']['relacoes'])
    n2 = h['nivel2']['total']
    tipos = Counter(r['tipo_adj'] for r in h['nivel2']['relacoes'])
    print(f'  Sprite {i}: {n2} relacoes ({dict(tipos)})')

# 5. Calcular entropia das propriedades entre sprites
print(f'\n--- 5. Entropia das propriedades entre sprites ---')
if len(todas_props) >= 2:
    # Para cada propriedade, coletar vetores
    props_nomes = ['area', 'orientacao', 'centroide_x', 'centroide_y', 'bbox_w', 'bbox_h']
    
    for prop_name in props_nomes:
        # Coletar valores da propriedade para cada região, em cada sprite
        # Primeiro, precisamos alinhar regiões por papel
        valores_por_papel = defaultdict(list)
        for props in todas_props:
            papeis = props['papel']
            valores = props[prop_name]
            for papel, val in zip(papeis, valores):
                valores_por_papel[papel].append(val)
        
        for papel, vals in sorted(valores_por_papel.items()):
            if len(vals) >= 3:
                # Bucketizar para entropia discreta
                if all(isinstance(v, (int, float)) and v >= 0 for v in vals):
                    h = entropia_shannon(vals)
                    media = sum(vals) / len(vals)
                    print(f'  {prop_name} ({papel}): H={h:.3f} media={media:.1f} n={len(vals)}')
                else:
                    # Orientação pode ser -1 (circular)
                    vals_filt = [v for v in vals if v >= 0]
                    if len(vals_filt) >= 3:
                        h = entropia_shannon(vals_filt)
                        print(f'  {prop_name} ({papel}): H={h:.3f} n={len(vals_filt)} (filtrado)')
                    else:
                        print(f'  {prop_name} ({papel}): -1 (circular/todos N/A)')
else:
    print('  Menos de 2 sprites — pulando análise de entropia')

# 6. Verificar template entrópico nas propriedades
print(f'\n--- 6. Template entrópico nas propriedades ---')
if len(todos_grids) >= 3:
    for prop_name in props_nomes:
        # Para cada sprite, pegar a lista de valores da propriedade (ordenada por papel)
        sequencias = []
        for props in todas_props:
            seq = [(p, v) for p, v in zip(props['papel'], props[prop_name])]
            # Ordenar por papel para alinhamento
            seq.sort(key=lambda x: x[0])
            sequencias.append(seq)
        
        # Aplicar template na sequência de pares (papel, valor)
        seqs_flat = []
        for seq in sequencias:
            flat = []
            for papel, val in seq:
                flat.append(f'{papel}_{val}')
            seqs_flat.append(flat)
        
        if len(seqs_flat) >= 3:
            tmpl = extrair_template_entropico(seqs_flat, 0.5)
            fixas = sum(1 for t, v, h in tmpl if t == 'fixo')
            pct = 100 * fixas / len(tmpl) if tmpl else 0
            print(f'  {prop_name}: {fixas}/{len(tmpl)} fixas ({pct:.0f}%) | {resumir_template(tmpl)}')
else:
    print('  Menos de 3 sprites — pulando template entrópico')

print(f'\n--- FIM ---')
print(f'Tokenizador Hierárquico implementado em mcr/tokenizador_hierarquico.py')
print(f'Todas as funções: extrair_regioes, extrair_relacoes, tokenizar_hierarquico')
