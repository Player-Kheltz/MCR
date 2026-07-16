#!/usr/bin/env python3
"""Gera novos spell icons a partir de grupos com mascaras identicas na sheet de 187 icons."""
import os, math, random as _rnd
from collections import Counter, defaultdict

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

from mcr.cielab import rgb_para_lab, lab_para_rgb, delta_e76, clusterizar_lab, detectar_picos
from mcr.template_entropico import extrair_template_entropico, gerar_do_template, resumir_template
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

OUT_DIR = os.path.join(_ROOT, 'poc_output')
os.makedirs(OUT_DIR, exist_ok=True)


def variar(cor, q=3):
    return tuple(max(0, min(255, c + _rnd.randint(-q, q))) for c in cor)


def mascara_hash(img):
    if img.mode != 'RGBA': img = img.convert('RGBA')
    p = img.load()
    bits = []
    for y in range(32):
        for x in range(32):
            r, g, b, a = p[x, y]
            bits.append('1' if a > 128 and (r, g, b) != (255, 0, 255) else '0')
    return ''.join(bits)


def tokenizar(img):
    if img.mode != 'RGBA': img = img.convert('RGBA')
    w, h = 32, 32; p = img.load(); MAGENTA = (255, 0, 255)

    lums, labs, rgbs, pos = [], [], [], []
    for y in range(h):
        for x in range(w):
            r, g, b, a = p[x, y]
            if a > 128 and (r, g, b) != MAGENTA:
                lums.append(int(0.299*r + 0.587*g + 0.114*b))
                labs.append(rgb_para_lab(r, g, b)); rgbs.append((r, g, b)); pos.append((y, x))

    if len(lums) < 3:
        toks = []
        for y in range(h): toks.append(f'R{y}'); toks.extend(['F']*w)
        return toks, {}

    BINS_L = 12
    hist_l = [0]*BINS_L
    for l in lums: hist_l[min(l*BINS_L//256, BINS_L-1)] += 1
    picos_l = detectar_picos(hist_l, BINS_L)

    clusters = clusterizar_lab(labs, 20.0)
    centros = {}
    for cid, memb in clusters.items():
        if memb: centros[cid] = (sum(m[0] for m in memb)/len(memb), sum(m[1] for m in memb)/len(memb), sum(m[2] for m in memb)/len(memb))
    cids_ord = sorted(centros.keys(), key=lambda c: centros[c][0])
    mapa = {old: new for new, old in enumerate(cids_ord)}

    toks_list = []; grid_tok = [['F']*w for _ in range(h)]; paleta = defaultdict(list)

    for idx, (y, x) in enumerate(pos):
        r, g, b = rgbs[idx]; lab = labs[idx]; lum = lums[idx]
        if any(0<=x+dx<w and 0<=y+dy<h and (p[x+dx, y+dy][3]<128 or p[x+dx, y+dy][:3]==MAGENTA) for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]):
            grid_tok[y][x] = 'B'; paleta['B'].append((r, g, b)); continue
        mn = min(range(len(picos_l)), key=lambda i: abs(lum - picos_l[i]*256//BINS_L))
        mc = 0; md = 9999
        for co, centro in centros.items():
            d = delta_e76(lab, centro)
            if d < md: md = d; mc = mapa[co]
        tok = f'L{mn}C{mc}'
        grid_tok[y][x] = tok; paleta[tok].append((r, g, b))

    toks = []
    for y in range(h):
        toks.append(f'R{y}')
        for x in range(w): toks.append(grid_tok[y][x])
    return toks, dict(paleta)


def renderizar(tokens, paleta_cores, largura=32):
    pal = {'F':(0,0,0,0)}
    for tok, cores in paleta_cores.items():
        if not cores: continue
        if isinstance(cores, tuple) and len(cores)>=3 and isinstance(cores[0], int):
            pal[tok] = (cores[0], cores[1], cores[2], 255)
        elif isinstance(cores, list) and cores and isinstance(cores[0], tuple):
            pal[tok] = (sum(c[0] for c in cores)//len(cores), sum(c[1] for c in cores)//len(cores), sum(c[2] for c in cores)//len(cores), 255)

    grid = [['F']*largura for _ in range(largura)]
    y = x = 0
    for t in tokens:
        if t.startswith('R'):
            try: y=int(t[1:]); x=0
            except Exception: pass
        elif t in pal and y<largura and x<largura: grid[y][x]=t; x+=1

    pixels = []
    for y in range(largura):
        for x in range(largura):
            tok = grid[y][x]
            if tok == 'F': pixels.append((0,0,0,0)); continue
            cor = pal.get(tok, (100,100,100))[:3]
            if _rnd.random() < 0.1: cor = variar(cor, 3)
            pixels.append((cor[0], cor[1], cor[2], 255))
    img = Image.new('RGBA', (largura, largura))
    img.putdata(pixels)
    return img


# ============================================================
# MAIN
# ============================================================
print('-'*60)
print('SPELL ICONS: grupos por mascara -> template -> CIELAB')
print('-'*60)

# 1. Carregar sheet
sheet = Image.open(os.path.join(_ROOT, 'client', 'data', 'images', 'game', 'spells', 'spell-icons-32x32.png'))
todos_icons = [sheet.crop((i*32, 0, i*32+32, 32)).convert('RGBA') for i in range(187)]
print(f'Total icons: {len(todos_icons)}')

# 2. Agrupar por mascara (detectando bg = azul escuro do sheet)
def get_mask(img):
    p = img.load()
    bits = []
    # Detectar bg: amostrar pixel (0,0) como bg
    bg = p[0, 0][:3]
    for y in range(32):
        for x in range(32):
            r, g, b, a = p[x, y]
            bits.append('1' if a > 128 and (r, g, b) != bg and (r, g, b) != (255, 0, 255) else '0')
    return ''.join(bits)

grupos = defaultdict(list)
for i, icon in enumerate(todos_icons):
    mask = get_mask(icon)
    grupos[mask].append(i)

# Filtrar grupos com 3+
grupos_3 = {k: [todos_icons[i] for i in v] for k, v in grupos.items() if len(v) >= 3}
print(f'Mascaras unicas: {len(grupos)}')
print(f'Grupos com 3+: {len(grupos_3)}')
for mask, icons in sorted(grupos_3.items(), key=lambda x: -len(x[1]))[:10]:
    op = sum(1 for b in mask if b == '1')
    pct = 100*op/1024
    print(f'  {len(icons)} icons, {op} opacos ({pct:.0f}% preenchido)')

# 3. Para cada grupo, tokenizar + template + CIELAB
print(f'\nGerando novos spell icons...')
total_gerados = 0
for gidx, (mask, icons) in enumerate(sorted(grupos_3.items(), key=lambda x: -len(x[1]))[:15]):
    if len(icons) < 3: continue
    
    op = sum(1 for b in mask if b == '1')
    
    # Tokenizar
    todos_tokens = []; paleta_comb = defaultdict(list)
    for icon in icons:
        toks, pal = tokenizar(icon)
        todos_tokens.append(toks)
        for tok, cores in pal.items(): paleta_comb[tok].extend(cores)
    
    # Paleta media
    pal_media = {}
    for tok, cores in paleta_comb.items():
        if cores: pal_media[tok] = (sum(c[0] for c in cores)//len(cores), sum(c[1] for c in cores)//len(cores), sum(c[2] for c in cores)//len(cores))
    
    # Template
    if len(todos_tokens) >= 3:
        tmpl = extrair_template_entropico(todos_tokens, 0.5)
        fixas = sum(1 for t, v, h in tmpl if t == 'fixo')
        pct_fixas = 100*fixas/len(tmpl)
    else:
        tmpl = None; pct_fixas = 0
    
    # Gerar
    n_tokens = len([t for t in pal_media if t not in ('F','B')])
    print(f'\nGrupo {gidx}: {len(icons)} icons, {op}op, {pct_fixas:.0f}% fixas, {n_tokens} tokens')
    
    for j in range(5):
        if tmpl and pct_fixas >= 40:
            seq = gerar_do_template(tmpl, temperatura=0.85)
        else:
            seq = todos_tokens[0]
        
        # CIELAB global
        angulo = _rnd.random() * 2 * math.pi
        pal_nova = {'F':(0,0,0,0), 'B':(0,0,0,255)}
        for tok, cor in pal_media.items():
            if isinstance(cor, (tuple, list)) and len(cor) >= 3:
                r, g, b = cor[0], cor[1], cor[2]
                L, a, bl = rgb_para_lab(r, g, b)
                raio = math.sqrt(a*a + bl*bl)
                if raio < 3: raio = 6
                novo_a = raio * math.cos(angulo + 0.3)
                novo_b = raio * math.sin(angulo + 0.3)
                novo_L = L + _rnd.randint(-2, 2)
                cr, cg, cb = lab_para_rgb(novo_L, novo_a, novo_b)
                pal_nova[tok] = (cr, cg, cb, 255)
            elif isinstance(cor, tuple) and len(cor) >= 3:
                pal_nova[tok] = (*cor, 255)
        
        img_out = renderizar(seq, pal_nova, 32)
        opacos = sum(1 for px in img_out.getdata() if px[3] > 128)
        caminho = os.path.join(OUT_DIR, f'spell_{gidx:03d}_{j}.png')
        img_out.save(caminho)
        total_gerados += 1
        
        if j == 0:
            cores_resumo = ', '.join(f'{t}={pal_nova.get(t,(0,0,0,0))[:3]}' for t in sorted(pal_nova.keys()) if t not in ('F','B') and t in pal_media)
            print(f'  [{j}] {opacos}px | {cores_resumo[:120]}')
        else:
            print(f'  [{j}] {opacos}px')

    # Salvar referencia
    icons[0].save(os.path.join(OUT_DIR, f'spell_{gidx:03d}_ref.png'))

print(f'\nTotal: {total_gerados} novos spell icons gerados')
print(f'Resultados: {OUT_DIR}')
print('-'*60)
