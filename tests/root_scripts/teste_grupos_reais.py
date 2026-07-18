#!/usr/bin/env python3
"""Pipeline Hierárquico em grupos REAIS de itens do catalog-content.json.

Extrai sprites do client, agrupa por máscara (silhueta idêntica),
aplica tokenizador hierárquico em cada grupo com 3+ amostras,
e gera novas variações via CIELAB.
"""
import os, random, json
from collections import Counter, defaultdict

from mcr.cielab import rgb_para_lab, lab_para_rgb, delta_e76, clusterizar_lab, detectar_picos
from mcr.sprite_extractor import SpriteExtractor
from mcr.template_entropico import extrair_template_entropico, gerar_do_template, resumir_template
from mcr.tokenizador_hierarquico import (
    extrair_regioes, extrair_relacoes, ordenar_regioes,
    tokenizar_hierarquico, resumir_hierarquico,
    regioes_para_grid, regioes_para_grid_com_borda,
    gerar_regioes_do_template,
)
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

OUT_DIR = os.path.join(_BASE, 'poc_output', 'grupos_hierarquicos')
os.makedirs(OUT_DIR, exist_ok=True)

# ─── Tokenização ─────────────────────────────────────────────

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

def obter_mascara(img):
    px = img.load()
    bits = []
    for y in range(32):
        for x in range(32):
            r, g, b, a = px[x, y]
            bits.append('1' if a > 128 and (r, g, b) != (255, 0, 255) else '0')
    return ''.join(bits)


# ─── CIELAB coloring ─────────────────────────────────────────

def colorir_grid(grid_estrutural, paleta_media, angulo_hue=0.0):
    """Colore grid estrutural (B, D, L, F) com CIELAB."""
    # Determinar cor base para cada papel
    cor_borda = (80, 80, 80)
    cor_interior = (150, 150, 150)
    cor_detalhe = (200, 200, 100)
    
    img = Image.new('RGBA', (32, 32))
    pixels = []
    
    for y in range(32):
        for x in range(32):
            tok = grid_estrutural[y][x]
            if tok == 'F':
                pixels.append((0, 0, 0, 0))
                continue
            
            if tok == 'B':
                r, g, b = cor_borda
            elif tok == 'D':
                r, g, b = cor_detalhe
            else:  # L
                r, g, b = cor_interior
            
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
# MAIN
# ============================================================
print('=' * 60)
print('PIPELINE HIERÁRQUICO EM GRUPOS REAIS')
print('=' * 60)

# 1. Extrair sprites do client usando SpriteExtractor
print('\n--- 1. Extraindo sprites do client ---')
ext = SpriteExtractor()
all_sprite_ids = []
for entry in ext.catalog:
    if entry.get('type') == 'sprite':
        first = entry.get('firstspriteid', 0)
        last = entry.get('lastspriteid', 0)
        # Amostrar 50 sprites por entry (max 10 entries = ~500 sprites)
        step = max(1, (last - first) // 50)
        for sid in range(first, last + 1, step):
            all_sprite_ids.append(sid)
        if len(all_sprite_ids) >= 300:
            break

print(f'  IDs de sprite para extrair: {len(all_sprite_ids)}')

# 2. Extrair sprites e agrupar por máscara
print(f'\n--- 2. Extraindo e agrupando por máscara ---')
grupos = defaultdict(list)
extraidos = 0
falhas = 0

for sid in all_sprite_ids:
    try:
        sprite = ext.get_sprite(sid, 32, 32)
        if sprite and len(sprite.pixels) >= 32*32*4:
            img = Image.frombytes('RGBA', (32, 32), sprite.pixels)
            mask = obter_mascara(img)
            opacos = mask.count('1')
            if opacos > 10:
                grupos[mask].append({'id': sid, 'img': img})
                extraidos += 1
        else:
            falhas += 1
    except Exception:
        falhas += 1

print(f'  Extraídos: {extraidos}, Falhas: {falhas}')
print(f'  Máscaras únicas: {len(grupos)}')

# 3. Filtrar grupos com 3+
grupos_3 = {k: v for k, v in grupos.items() if len(v) >= 3}
print(f'\n  Grupos com 3+ amostras: {len(grupos_3)}')

if grupos_3:
    maiores = sorted(grupos_3.items(), key=lambda x: -len(x[1]))[:10]
    for mask, members in maiores:
        op = mask.count('1')
        print(f'    {len(members)} sprites, {op} opacos, IDs: {[m["id"] for m in members[:5]]}...')

# 4. Para cada grupo com 3+, aplicar pipeline hierárquico
print(f'\n--- 3. Pipeline hierárquico ---')

grupos_processados = 0
for gidx, (mask, members) in enumerate(sorted(grupos_3.items(), key=lambda x: -len(x[1]))[:10]):
    if len(members) < 3:
        continue
    
    opacos_mask = mask.count('1')
    print(f'\n  Grupo {gidx}: {len(members)} sprites, {opacos_mask} opacos')
    
    # Tokenizar cada sprite
    todos_grids = []
    todas_paletas = []
    for m in members:
        grid, pal = tokenizar_para_grid(m['img'])
        todos_grids.append(grid)
        todas_paletas.append(pal)
    
    # Extrair regiões de cada
    todas_regioes = []
    for grid in todos_grids:
        reg = extrair_regioes(grid, modo='papel')
        reg_ord = ordenar_regioes(reg)
        todas_regioes.append(reg_ord)
    
    # Verificar consistência das regiões
    n_regs = [len(r) for r in todas_regioes]
    papeis_set = set()
    for regs in todas_regioes:
        papeis_set.add(tuple(sorted(Counter(r['papel'] for r in regs).items())))
    
    print(f'    Regiões: {min(n_regs)}-{max(n_regs)} por sprite')
    print(f'    Estrutura de papéis consistente: {len(papeis_set) == 1}')
    if papeis_set:
        print(f'    Papeis: {papeis_set.pop()}')
    
    # Template entrópico nas propriedades das regiões
    # Alinhar regiões por papel e posição
    props_names = ['area', 'centroide_x', 'centroide_y', 'bbox_w', 'bbox_h']
    for prop in props_names:
        seqs = []
        for regs in todas_regioes:
            vals = []
            for r in regs:
                if prop == 'area':
                    vals.append(f'{r["papel"]}_{r["area"]}')
                elif prop == 'centroide_x':
                    vals.append(f'{r["papel"]}_{r["centroide"][0]:.0f}')
                elif prop == 'centroide_y':
                    vals.append(f'{r["papel"]}_{r["centroide"][1]:.0f}')
                elif prop == 'bbox_w':
                    vals.append(f'{r["papel"]}_{r["bbox"][2]-r["bbox"][0]+1}')
                elif prop == 'bbox_h':
                    vals.append(f'{r["papel"]}_{r["bbox"][3]-r["bbox"][1]+1}')
            seqs.append(vals)
        tmpl = extrair_template_entropico(seqs, 0.5) if len(seqs) >= 3 else None
        if tmpl:
            fixas = sum(1 for t, v, h in tmpl if t == 'fixo')
            pct = 100 * fixas / len(tmpl)
            print(f'    {prop}: {fixas}/{len(tmpl)} fixas ({pct:.0f}%)')
        else:
            print(f'    {prop}: N/A (<3 amostras)')
    
    # Gerar variações
    template_regioes = todas_regioes[0]
    gdir = os.path.join(OUT_DIR, f'grupo_{gidx:04d}')
    os.makedirs(gdir, exist_ok=True)
    
    # Salvar referências
    for mi, m in enumerate(members[:5]):
        m['img'].save(os.path.join(gdir, f'ref_{mi}_{m["id"]}.png'))
    
    # Gerar 5 variações
    for vi in range(5):
        hue = random.random() * 2 * math.pi
        novas_regioes = gerar_regioes_do_template(
            template_regioes,
            temperatura=0.5,
            variacao_posicao=1.5,
            variacao_area=0.15,
        )
        grid = regioes_para_grid_com_borda(novas_regioes, 32, 32)
        img_out = colorir_grid(grid, todas_paletas[0], angulo_hue=hue)
        caminho = os.path.join(gdir, f'gerado_{vi}.png')
        img_out.save(caminho)
    
    grupos_processados += 1
    print(f'    -> 5 variações geradas em {gdir}')

print(f'\n--- RESUMO ---')
print(f'  Grupos processados: {grupos_processados}')
print(f'  Saída: {OUT_DIR}')
print(f'  Grupos com 3+: {len(grupos_3)}')
if not grupos_3:
    print(f'  AVISO: Nenhum grupo com 3+ encontrado. Tentando fallback...')
    # Fallback: usar shields
    print(f'  Usando shields do poc_output como fallback')
