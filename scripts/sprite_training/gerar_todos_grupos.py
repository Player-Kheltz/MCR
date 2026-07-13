#!/usr/bin/env python3
"""Gera variacoes de TODOS os grupos de sprites com mascaras identicas."""
import os, math, pathlib, random as _rnd
from collections import Counter, defaultdict

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

from mcr.cielab import detectar_picos
from mcr.template_entropico import extrair_template_entropico, gerar_do_template
from PIL import Image

OUT_DIR = os.path.join(_ROOT, 'poc_output')
os.makedirs(OUT_DIR, exist_ok=True)


def entropia_shannon(seq):
    c = Counter(seq); n = len(seq); h = 0.0
    for v in c.values():
        p = v/n
        if p > 0: h -= p * math.log2(p)
    return h


def bins_otimos_por_entropia(valores, max_bins=30):
    if not valores: return 8
    min_v, max_v = min(valores), max(valores)
    if min_v == max_v: return 2
    faixa = max_v - min_v
    ent_por_bin = []
    for b in range(2, max_bins + 1):
        hist = [0]*b
        for v in valores:
            idx = min(int((v - min_v) * b / faixa), b - 1)
            hist[idx] += 1
        h = entropia_shannon(sum(([i]*c for i,c in enumerate(hist)), []))
        ent_por_bin.append(h / math.log2(b) if b > 1 else 0)
    for i in range(len(ent_por_bin) - 3):
        if all(abs(ent_por_bin[i+j+1] - ent_por_bin[i+j]) < 0.05 for j in range(3)):
            return max(8, (i + 2) * 2)
    return max_bins


def tokenizar(img):
    """Tokeniza um sprite qualquer com niveis de LUM x RG."""
    if img.mode != 'RGBA': img = img.convert('RGBA')
    w,h = img.size; p = img.load()
    # bg detection
    am = []
    for x in range(w):
        if p[x,0][3] > 128: am.append(p[x,0][:3])
        if p[x,h-1][3] > 128: am.append(p[x,h-1][:3])
    for y in range(h):
        if p[0,y][3] > 128: am.append(p[0,y][:3])
        if p[w-1,y][3] > 128: am.append(p[w-1,y][:3])
    bg = Counter(am).most_common(1)[0][0] if am else (255,0,255)

    lums = []; rg_vs = []
    for y in range(h):
        for x in range(w):
            r,g,b,a = p[x,y]
            if a > 128 and (r,g,b)[:3] != (255,0,255) and (r,g,b)[:3] != bg:
                lums.append(int(0.299*r + 0.587*g + 0.114*b))
                rg_vs.append((r-g)/(r+g+b+1))

    BINS_L = bins_otimos_por_entropia(lums)
    BINS_RG = bins_otimos_por_entropia(rg_vs)
    
    hist_l = [0]*BINS_L
    for l in lums: hist_l[min(l*BINS_L//256, BINS_L-1)] += 1
    picos_l = detectar_picos(hist_l, BINS_L)

    hist_rg = [0]*BINS_RG
    for v in rg_vs: hist_rg[min(int((v+1)*BINS_RG//2), BINS_RG-1)] += 1
    picos_rg = detectar_picos(hist_rg, BINS_RG)

    toks = []; paleta = defaultdict(list)

    for y in range(h):
        toks.append(f'R{y}')
        for x in range(w):
            r,g,b,a = p[x,y]
            if a < 128 or (r,g,b)[:3] == (255,0,255) or (r,g,b)[:3] == bg:
                toks.append('F'); continue
            eh_b = any(0<=x+dx<w and 0<=y+dy<h and (
                p[x+dx,y+dy][3] < 128 or p[x+dx,y+dy][:3]==(255,0,255) or p[x+dx,y+dy][:3]==bg
            ) for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)])
            if eh_b:
                toks.append('B'); paleta['B'].append((r,g,b)); continue
            lum = int(0.299*r + 0.587*g + 0.114*b)
            rg_v = (r-g)/(r+g+b+1)
            melhor_n = 0; melhor_d = 999
            for ni, pb in enumerate(picos_l):
                d = abs(lum - (pb*256//BINS_L + 256//BINS_L//2))
                if d < melhor_d: melhor_d = d; melhor_n = ni
            melhor_c = 0; melhor_dc = 999
            for ci, pr in enumerate(picos_rg):
                val_rg = (pr*2//BINS_RG + 1//BINS_RG) - 1
                d = abs(rg_v - val_rg)
                if d < melhor_dc: melhor_dc = d; melhor_c = ci
            tok = f'L{melhor_n}C{melhor_c}'
            toks.append(tok); paleta[tok].append((r,g,b))
    
    return toks, dict(paleta)


def renderizar(tokens, paleta_dist, largura=32):
    """Renderiza com suavizacao."""
    pal = {'F':[(0,0,0)]}
    for tok, cores in paleta_dist.items():
        if cores: pal[tok] = cores

    grid = [['F']*largura for _ in range(largura)]
    y = x = 0
    for t in tokens:
        if t.startswith('R'):
            try: y=int(t[1:]); x=0
            except Exception: pass
        elif t in pal and y<largura and x<largura:
            grid[y][x] = t; x += 1

    def cor_media(tok):
        cores = pal.get(tok, [(128,128,128)])
        return (sum(c[0] for c in cores)//len(cores),
                sum(c[1] for c in cores)//len(cores),
                sum(c[2] for c in cores)//len(cores))

    pixels = []
    for y in range(largura):
        for x in range(largura):
            tok = grid[y][x]
            if tok == 'F': pixels.append((0,0,0,0)); continue
            if tok == 'D':
                dist = pal.get('D', pal.get('B', [(100,0,0)]))
                cor = _rnd.choice(dist)
                pixels.append((cor[0], cor[1], cor[2], 255))
                continue

            cor = cor_media(tok)
            viz = []
            for dy in [-1,0,1]:
                for dx in [-1,0,1]:
                    ny,nx = y+dy, x+dx
                    if 0<=ny<largura and 0<=nx<largura:
                        vt = grid[ny][nx]
                        if vt in pal and vt != 'F':
                            viz.append(cor_media(vt))
            if viz:
                r = (cor[0] + sum(c[0] for c in viz)) // (len(viz)+1)
                g = (cor[1] + sum(c[1] for c in viz)) // (len(viz)+1)
                b = (cor[2] + sum(c[2] for c in viz)) // (len(viz)+1)
            else:
                r,g,b = cor
            pixels.append((r,g,b,255))

    img = Image.new('RGBA', (largura, largura))
    img.putdata(pixels)
    return img


# ============================================================
# MAIN
# ============================================================
print('-'*60)
print('GERANDO VARIACOES DE TODOS OS GRUPOS')
print('-'*60)

# 1. Carregar todos os sprites e agrupar por mascara
img_dir = pathlib.Path(_ROOT) / 'client' / 'data' / 'images'
all_pngs = list(img_dir.rglob('*.png'))

grupos = defaultdict(list)
for p in all_pngs:
    try:
        img = Image.open(p).convert('RGBA').resize((32,32), Image.NEAREST)
        px = img.load()
        bits = []
        for y in range(32):
            for x in range(32):
                bits.append('1' if px[x,y][3] > 128 else '0')
        mask = ''.join(bits)
        opacos = bits.count('1')
        if opacos > 10:
            grupos[mask].append(img)
    except Exception: pass

# Filtrar grupos com 3+
grupos_3 = {k:v for k,v in grupos.items() if len(v) >= 3}
print(f'Grupos com 3+: {len(grupos_3)}')

# 2. Para cada grupo, extrair template + paleta + gerar
total_gerados = 0
for gidx, (mask, sprites) in enumerate(sorted(grupos_3.items(), key=lambda x: -len(x[1]))):
    if gidx >= 16: break  # max 16 grupos
    
    opacos = sum(1 for b in mask if b == '1')
    print(f'\nGrupo {gidx}: {len(sprites)} sprites, {opacos} opacos')

    # Tokenizar todos
    todos_tokens = []
    todas_paletas = []
    for s in sprites:
        toks, pal = tokenizar(s)
        todos_tokens.append(toks)
        todas_paletas.append(pal)

    # Paleta combinada
    paleta_final = defaultdict(list)
    for pal in todas_paletas:
        for tok, cores in pal.items():
            paleta_final[tok].extend(cores)

    # Se so tem um token alem de F/B, usar como template fixo (nao generative)
    n_tokens = len([t for t in paleta_final.keys() if t not in ('F','B')])
    
    # Tentar template entropico
    if len(todos_tokens) >= 3 and n_tokens >= 2:
        tmpl = extrair_template_entropico(todos_tokens, 0.5)
        fixas = sum(1 for t,v,h in tmpl if t == 'fixo')
        pct = 100*fixas/len(tmpl)
        print(f'  Template: {pct:.0f}% fixas ({fixas}/{len(tmpl)})')
        
        # Usar PRIMEIRO sprite como template se fixas < 50%
        if pct < 50:
            toks_base = todos_tokens[0]
            print(f'  Fixas baixas — usando sprite 0 como template')
        else:
            toks_base = gerar_do_template(tmpl, temperatura=0.85)
    else:
        toks_base = todos_tokens[0]
        print(f'  Usando sprite 0 como template (poucos tokens/templates)')
    
    # Gerar 3 variacoes
    for j in range(3):
        # Variar paleta
        paleta_variada = {}
        for tok, cores in paleta_final.items():
            if cores:
                if len(cores) == 1:
                    paleta_variada[tok] = cores
                else:
                    # Amostrar alguns da distribuicao
                    n_amostra = min(20, len(cores))
                    amostra = _rnd.sample(cores, n_amostra)
                    paleta_variada[tok] = amostra
        
        img_out = renderizar(toks_base, paleta_variada, 32)
        opacos_final = sum(1 for px in img_out.getdata() if px[3] > 128)
        caminho = os.path.join(OUT_DIR, f'g{gidx:03d}_v{j}.png')
        img_out.save(caminho)
        total_gerados += 1
    
    # Salvar referencia
    sprites[0].save(os.path.join(OUT_DIR, f'g{gidx:03d}_ref.png'))

print(f'\nTotal: {total_gerados} sprites gerados de {len(grupos_3)} grupos')
print('-'*60)
