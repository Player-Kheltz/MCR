#!/usr/bin/env python3
"""Teste de Geração Hierárquica (Nível 2 → Nível 1 → Nível 0 + CIELAB)."""
import os, random, math
from collections import Counter, defaultdict

from mcr.cielab import rgb_para_lab, lab_para_rgb, delta_e76, clusterizar_lab, detectar_picos
from mcr.template_entropico import entropia_shannon, extrair_template_entropico
from mcr.tokenizador_hierarquico import (
    extrair_regioes, extrair_relacoes, ordenar_regioes,
    tokenizar_hierarquico, resumir_hierarquico,
    gerar_regioes_do_template, regioes_para_grid, regioes_para_grid_com_borda,
)
from PIL import Image

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

OUT_DIR = os.path.join(_BASE, 'poc_output', 'resultado')
os.makedirs(OUT_DIR, exist_ok=True)

# ─── Funções auxiliares (do gerar_spell_icons.py) ─────────────

def tokenizar_para_grid(img):
    """Tokeniza sprite e retorna grid 2D + paleta."""
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


# ─── Geração Hierárquica Principal ────────────────────────────

def gerar_sprite_hierarquico(
    regioes_template: list,
    paleta_media: dict,
    temperatura: float = 0.6,
    angulo_hue: float = 0.0,
    variacao_posicao: float = 1.0,
    variacao_area: float = 0.15,
) -> Image.Image:
    """Gera um sprite completo via pipeline hierárquico.
    
    1. Nível 1: gera novas regiões a partir do template
    2. Nível 0: converte para grid de tokens
    3. CIELAB: colore com ângulo global
    
    Returns:
        PIL Image RGBA 32×32
    """
    # 1. Gerar novas regiões
    novas_regioes = gerar_regioes_do_template(
        regioes_template,
        temperatura=temperatura,
        variacao_posicao=variacao_posicao,
        variacao_area=variacao_area,
    )
    
    # 2. Converter para grid (com bordas D entre L e B)
    grid = regioes_para_grid_com_borda(novas_regioes, 32, 32)
    
    # 3. CIELAB: colorir cada pixel
    img = Image.new('RGBA', (32, 32))
    pixels = []
    
    # Paleta base: média das cores da paleta original para cada token
    cor_borda = (80, 80, 80, 255)
    if 'B' in paleta_media and paleta_media['B']:
        cores_b = paleta_media['B']
        if isinstance(cores_b[0], tuple):
            cb = cores_b[0]
        else:
            cb = cores_b
        cor_borda = (cb[0], cb[1], cb[2], 255)
    cor_interior = (150, 150, 150, 255)
    cor_detalhe = (200, 200, 100, 255)
    
    for y in range(32):
        for x in range(32):
            tok = grid[y][x]
            if tok == 'F':
                pixels.append((0, 0, 0, 0))
            elif tok == 'B':
                r, g, b = cor_borda[:3]
                L, a, bl = rgb_para_lab(r, g, b)
                raio = math.sqrt(a*a + bl*bl)
                if raio < 3: raio = 6
                novo_a = raio * math.cos(angulo_hue)
                novo_b = raio * math.sin(angulo_hue)
                cr, cg, cb = lab_para_rgb(L, novo_a, novo_b)
                pixels.append((cr, cg, cb, 255))
            elif tok == 'D':
                r, g, b = cor_detalhe[:3]
                L, a, bl = rgb_para_lab(r, g, b)
                raio = math.sqrt(a*a + bl*bl)
                if raio < 3: raio = 6
                novo_a = raio * math.cos(angulo_hue + 0.3)
                novo_b = raio * math.sin(angulo_hue + 0.3)
                cr, cg, cb = lab_para_rgb(L, novo_a, novo_b)
                pixels.append((cr, cg, cb, 255))
            else:  # L
                r, g, b = cor_interior[:3]
                L, a, bl = rgb_para_lab(r, g, b)
                raio = math.sqrt(a*a + bl*bl)
                if raio < 3: raio = 6
                novo_a = raio * math.cos(angulo_hue)
                novo_b = raio * math.sin(angulo_hue)
                cr, cg, cb = lab_para_rgb(L, novo_a, novo_b)
                pixels.append((cr, cg, cb, 255))
    
    img.putdata(pixels)
    return img


# ============================================================
# TESTE
# ============================================================
print('=' * 60)
print('TESTE: Geração Hierárquica de Sprites')
print('=' * 60)

# 1. Carregar shields
print('\n--- 1. Carregando shields ---')
shields = []
for i in range(9):
    path = os.path.join(_BASE, 'poc_output', f'shield_ref_{i}.png')
    if os.path.exists(path):
        shields.append(Image.open(path).convert('RGBA'))

print(f'  Total: {len(shields)} shields')

# 2. Tokenizar e extrair regiões de cada shield
print(f'\n--- 2. Extraindo regiões (Nível 1) ---')
todas_regioes_ordenadas = []
for i, img in enumerate(shields):
    grid, pal = tokenizar_para_grid(img)
    regioes = extrair_regioes(grid, modo='papel')
    reg_ord = ordenar_regioes(regioes)
    todas_regioes_ordenadas.append(reg_ord)
    print(f'  Shield {i}: {len(reg_ord)} regiões')

# 3. Criar paleta média
paleta_media = defaultdict(list)
for img in shields:
    grid, pal = tokenizar_para_grid(img)
    for tok, cores in pal.items():
        paleta_media[tok].extend(cores)

print(f'\n  Paleta média: {len(paleta_media)} tokens')

# 4. Usar shield 0 como template de regiões
regioes_template = todas_regioes_ordenadas[0]
print(f'\n  Template: {len(regioes_template)} regiões')

# 5. Gerar variações hierárquicas
print(f'\n--- 3. Gerando variações hierárquicas ---')
random.seed(42)

for g in range(20):
    # Diferentes temperaturas e ângulos
    temp = 0.3 + random.random() * 0.7
    hue = random.random() * 2 * math.pi
    vp = 0.5 + random.random() * 2.0
    va = 0.05 + random.random() * 0.25
    
    img_out = gerar_sprite_hierarquico(
        regioes_template, paleta_media,
        temperatura=temp,
        angulo_hue=hue,
        variacao_posicao=vp,
        variacao_area=va,
    )
    
    opacos = sum(1 for px in img_out.getdata() if px[3] > 128)
    caminho = os.path.join(OUT_DIR, f'hg_{g:03d}.png')
    img_out.save(caminho)
    
    if g < 5 or g % 5 == 0:
        print(f'  [{g}] temp={temp:.2f} hue={hue:.2f} opacos={opacos} -> {caminho}')

# 6. Salvar referência
shields[0].save(os.path.join(OUT_DIR, 'hg_ref.png'))
print(f'\n  Referência salva: hg_ref.png')

# 7. Estatísticas
print(f'\n--- 4. Estatísticas ---')
print(f'  Sprites gerados: {len(range(20))}')
print(f'  Diretório: {OUT_DIR}')

# 8. Validar: quantos sprites têm pelo menos 50% dos opacos do template?
template_opacos = sum(1 for r in regioes_template for _ in r['pixels'])
print(f'  Opacos no template: {template_opacos}')

opacos_list = []
for g in range(20):
    path = os.path.join(OUT_DIR, f'hg_{g:03d}.png')
    img = Image.open(path)
    op = sum(1 for px in img.getdata() if px[3] > 128)
    opacos_list.append(op)

media_op = sum(opacos_list) / len(opacos_list)
min_op = min(opacos_list)
max_op = max(opacos_list)
print(f'  Opacos gerados: media={media_op:.0f} min={min_op} max={max_op}')
print(f'  Taxa de preservação: {100*media_op/template_opacos:.0f}%')

print(f'\n--- FIM ---')
