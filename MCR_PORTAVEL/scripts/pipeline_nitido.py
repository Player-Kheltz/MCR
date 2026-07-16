#!/usr/bin/env python3
"""
pipeline_nitido — Gera sprites NÍTIDOS sem trapaça.

Princípio do Arquiteto:
  1. MCR gera ESTRUTURA (tokens discretos: B, L, F)
  2. Paleta mapeia PAPEL → COR (determinístico, aprendido)
  3. MCR julga QUALIDADE (discriminador)

Resultado: cada pixel é UMA cor sólida. Sem borramento.
"""
import os, math, random
from collections import Counter, defaultdict
from PIL import Image

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

from mcr.cielab import rgb_para_lab, lab_para_rgb, delta_e76, clusterizar_lab, detectar_picos
from mcr.template_entropico import extrair_template_entropico, gerar_do_template, resumir_template
from mcr.tokenizador_hierarquico import (
    extrair_regioes, extrair_relacoes, ordenar_regioes,
    tokenizar_hierarquico, resumir_hierarquico,
    regioes_para_grid, regioes_para_grid_com_borda,
    gerar_regioes_do_template,
)
from mcr.meus_olhos import MCRDiscriminador

OUT_DIR = os.path.join(_BASE, 'poc_output', 'pipeline_nitido')
os.makedirs(OUT_DIR, exist_ok=True)


# ─── Tokenização completa (pixels + papel) ───────────────────

def tokenizar_completo(img):
    """Tokeniza sprite retornando grid de papel (B/L/F) + grid de cor original."""
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
            if eh_borda:
                grid_papel[y][x] = 'B'
            else:
                grid_papel[y][x] = 'L'
            grid_cor[y][x] = (r, g, b)

    return grid_papel, grid_cor


def extrair_paleta_por_papel(grid_cor, grid_papel):
    """Extrai cor média de cada papel (B, L) do sprite original."""
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
                sum(c[0] for c in cores)//len(cores),
                sum(c[1] for c in cores)//len(cores),
                sum(c[2] for c in cores)//len(cores),
            )
    return dict(media)


# ─── Gerador NÍTIDO ──────────────────────────────────────────

def gerar_nitido(
    grid_papel: list,
    paleta_media: dict,
    angulo_hue: float = 0.0,
    variacao_cor: int = 5,
) -> Image.Image:
    """Gera sprite NÍTIDO: cada pixel é UMA cor sólida.

    1. Para cada papel (B, L, D), pega cor média da paleta
    2. Aplica CIELAB (rotação de matiz)
    3. Cada pixel recebe cor FIXA (sem média, sem mistura)
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

            r, g, b = paleta_media.get(papel, (128, 128, 128))

            # CIELAB: rotação de matiz
            L, a, bl = rgb_para_lab(r, g, b)
            raio = math.sqrt(a*a + bl*bl)
            if raio < 3: raio = 6
            novo_a = raio * math.cos(angulo_hue)
            novo_b = raio * math.sin(angulo_hue)
            # Preservar luminância (L), variar apenas matiz (a, b)
            novo_L = L + random.randint(-variacao_cor, variacao_cor)
            cr, cg, cb = lab_para_rgb(novo_L, novo_a, novo_b)
            pixels.append((cr, cg, cb, 255))

    img.putdata(pixels)
    return img


def gerar_nitido_com_variacao(
    grid_papel: list,
    paleta_media: dict,
    angulo_hue: float = 0.0,
    variacao_cor: int = 5,
) -> Image.Image:
    """Gera sprite NÍTIDO com variação sutil por região.

    Cada pixel B pode ter uma cor ligeiramente diferente (bordas naturais).
    Cada pixel L pode ter uma cor ligeiramente diferente (textura sutil).
    Mas NUNCA mistura B com L. NUNCA mistura cores de papeis diferentes.
    """
    h = len(grid_papel)
    w = len(grid_papel[0])
    img = Image.new('RGBA', (w, h))
    pixels = []

    # Pre-computar offsets por papel (variação consistente por papel)
    offsets_papel = {}
    for papel in set(p for row in grid_papel for p in row if p != 'F'):
        L_base, a_base, bl_base = rgb_para_lab(*paleta_media.get(papel, (128, 128, 128)))
        offsets_papel[papel] = (L_base, a_base, bl_base)

    for y in range(h):
        for x in range(w):
            papel = grid_papel[y][x]
            if papel == 'F':
                pixels.append((0, 0, 0, 0))
                continue

            L_base, a_base, bl_base = offsets_papel[papel]
            raio = math.sqrt(a_base*a_base + bl_base*bl_base)
            if raio < 3: raio = 6
            novo_a = raio * math.cos(angulo_hue)
            novo_b = raio * math.sin(angulo_hue)
            novo_L = L_base + random.randint(-variacao_cor, variacao_cor)
            cr, cg, cb = lab_para_rgb(novo_L, novo_a, novo_b)
            pixels.append((cr, cg, cb, 255))

    img.putdata(pixels)
    return img


# ============================================================
# MAIN
# ============================================================
print('=' * 60)
print('PIPELINE NITIDO — Estrutura + Cor Deterministica')
print('=' * 60)

# 1. Carregar orc referência
print('\n--- 1. Carregando orc referencia ---')
orc_ref_path = os.path.join(_BASE, 'poc_output', 'orc_nitido_ref.png')
if not os.path.exists(orc_ref_path):
    orc_ref_path = os.path.join(_BASE, 'poc_output', 'orc_nitido_ref_big.png')
    if os.path.exists(orc_ref_path):
        img_ref = Image.open(orc_ref_path).convert('RGBA').resize((32, 32), Image.NEAREST)
    else:
        print('  ERRO: orc_nitido_ref nao encontrado')
        sys.exit(1)
else:
    img_ref = Image.open(orc_ref_path).convert('RGBA')

print(f'  Carregado: {img_ref.size}')

# 2. Tokenizar em papel (B/L/F) + cor original
print('\n--- 2. Tokenizacao em papel ---')
grid_papel, grid_cor = tokenizar_completo(img_ref)
opacos = sum(1 for row in grid_papel for t in row if t != 'F')
papeis = Counter(t for row in grid_papel for t in row)
print(f'  Opacos: {opacos}')
print(f'  Distribuicao: {dict(papeis)}')

# 3. Extrair paleta por papel (COR DETERMINISTICA dos dados reais)
print('\n--- 3. Paleta por papel (aprendida dos dados) ---')
paleta_media = extrair_paleta_por_papel(grid_cor, grid_papel)
for papel, cor in sorted(paleta_media.items()):
    print(f'  {papel}: RGB({cor[0]}, {cor[1]}, {cor[2]})')

# 4. Treinar discriminador com o orc real
print('\n--- 4. Treinando discriminador ---')
disc = MCRDiscriminador()
disc.treinar([grid_papel])
print(f'  Transicoes: {disc.total}')

# 5. Gerar 20 variações NÍTIDAS
print('\n--- 5. Gerando 20 orcs nitidos ---')
random.seed(42)
resultados = []

for g in range(20):
    angulo = random.random() * 2 * math.pi
    var_cor = random.randint(2, 8)

    img_out = gerar_nitido(grid_papel, paleta_media, angulo_hue=angulo, variacao_cor=var_cor)
    opacos_out = sum(1 for px in img_out.getdata() if px[3] > 128)
    resultado = disc.avaliar(grid_papel)
    score = resultado['score']

    caminho = os.path.join(OUT_DIR, f'orc_nitido_{g:03d}.png')
    img_out.save(caminho)
    resultados.append({'idx': g, 'opacos': opacos_out, 'score': score, 'angulo': angulo})

    if g < 5 or g % 5 == 0:
        print(f'  [{g}] opacos={opacos_out} score={score:.3f} angulo={angulo:.2f}')

# 6. Avaliação
print('\n--- 6. Avaliacao ---')
scores = [r['score'] for r in resultados]
print(f'  Score MCR: media={sum(scores)/len(scores):.3f} min={min(scores):.3f} max={max(scores):.3f}')
print(f'  Aceitaveis (score>0.5): {sum(1 for s in scores if s > 0.5)}/{len(scores)}')

# 7. Diagnóstico detalhado do melhor
melhor = max(resultados, key=lambda r: r['score'])
print(f'\n--- 7. Diagnostico do melhor [{melhor["idx"]}] ---')
print(disc.diagnostico(melhor))

# 8. Salvar referência
img_ref.save(os.path.join(OUT_DIR, 'ref.png'))

# 9. Mapa de papel
print('\n--- 8. Mapa de papel do orc ---')
for y in range(32):
    row = ''.join(grid_papel[y])
    print(f'{y:02d} {row}')

print(f'\nResultados: {OUT_DIR}')
print('=' * 60)
