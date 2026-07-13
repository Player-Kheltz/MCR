#!/usr/bin/env python3
"""
pipeline_orc_mcr — MCR como gerador de ESTRUTURA + paleta deterministica.

Carrega 4 orcs (4 direcoes), treina MCR com transicoes de papel (B/L/F),
gera estruturas NOVAS via Markov, aplica paleta aprendida, valida com discriminador.
"""
import os, math, random
from collections import Counter, defaultdict
from PIL import Image

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

from mcr.cielab import rgb_para_lab, lab_para_rgb
from mcr.meus_olhos import MCRDiscriminador

OUT_DIR = os.path.join(_BASE, 'poc_output', 'orc_mcr_nitido')
os.makedirs(OUT_DIR, exist_ok=True)


# ─── Tokenizacao em papel ───────────────────────────────────

def tokenizar_papel(img):
    """Converte sprite para grid de papel (B/L/F) + grid de cor."""
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


# ─── MCR Gerador de Estrutura ────────────────────────────────

class MCRGerador:
    """Markov de 1a ordem que gera grids 2D de papeis (B/L/F)."""

    def __init__(self):
        self.transicoes = defaultdict(Counter)
        self.marginal_esq = Counter()
        self.marginal_cima = Counter()
        self.todos_papeis = set()

    def treinar(self, grids_papel):
        """Treina com multiplos grids 2D de papeis."""
        for grid in grids_papel:
            h, w = len(grid), len(grid[0])
            for y in range(h):
                for x in range(w):
                    tok = grid[y][x]
                    if tok == 'F':
                        continue
                    self.todos_papeis.add(tok)
                    # Contexto: esquerda + cima
                    ctx_esq = grid[y][x-1] if x > 0 else 'F'
                    ctx_cima = grid[y-1][x] if y > 0 else 'F'
                    self.transicoes[(ctx_esq, ctx_cima)][tok] += 1
                    self.marginal_esq[ctx_esq] += 1
                    self.marginal_cima[ctx_cima] += 1

    def _prob(self, ctx_esq, ctx_cima, papel):
        total_ctx = sum(self.transicoes[(ctx_esq, ctx_cima)].values())
        if total_ctx == 0:
            # Fallback: usar marginal
            total_marg = sum(self.marginal_cima.values())
            return self.marginal_cima.get(papel, 0) / max(total_marg, 1)
        return self.transicoes[(ctx_esq, ctx_cima)][papel] / total_ctx

    def gerar_grid(self, largura=32, altura=32, temperatura=0.8, semente=None):
        """Gera um grid 2D de papeis via Markov.

        Gera linha por linha, da esquerda para direita, de cima para baixo.
        Cada pixel: P(papel | esquerda, cima) com temperatura.
        """
        if semente is not None:
            random.seed(semente)

        grid = [['F']*largura for _ in range(altura)]
        papeis = list(self.todos_papeis)

        for y in range(altura):
            for x in range(largura):
                ctx_esq = grid[y][x-1] if x > 0 else 'F'
                ctx_cima = grid[y-1][x] if y > 0 else 'F'

                # Calcular probabilidades com temperatura
                probs = {}
                for p in papeis:
                    prob = self._prob(ctx_esq, ctx_cima, p)
                    probs[p] = prob ** (1.0 / max(temperatura, 0.01))

                total = sum(probs.values())
                if total == 0:
                    grid[y][x] = 'F'
                    continue

                # Amostrar
                r = random.random() * total
                acum = 0.0
                escolhido = 'F'
                for p, prob in probs.items():
                    acum += prob
                    if r <= acum:
                        escolhido = p
                        break

                grid[y][x] = escolhido

        return grid

    def gerar_grid_da_referencia(self, grid_ref, temperatura=0.5, variacao=0.3):
        """Gera variacao de um grid de referencia usando o MCR.

        Para cada pixel do reference, decide se mantem ou altera
        baseado na probabilidade do MCR.
        """
        h = len(grid_ref)
        w = len(grid_ref[0])
        grid_novo = [['F']*w for _ in range(h)]
        papeis = list(self.todos_papeis)

        for y in range(h):
            for x in range(w):
                ref = grid_ref[y][x]
                ctx_esq = grid_novo[y][x-1] if x > 0 else 'F'
                ctx_cima = grid_novo[y-1][x] if y > 0 else 'F'

                # Probabilidade do MCR para cada papel
                probs = {}
                for p in papeis:
                    probs[p] = self._prob(ctx_esq, ctx_cima, p)

                # Decidir: manter referencia ou gerar novo
                if random.random() < variacao:
                    # Gerar novo baseado no MCR
                    probs_temp = {p: pr ** (1.0/max(temperatura, 0.01)) for p, pr in probs.items()}
                    total = sum(probs_temp.values())
                    if total > 0:
                        r = random.random() * total
                        acum = 0.0
                        escolhido = 'F'
                        for p, prob in probs_temp.items():
                            acum += prob
                            if r <= acum:
                                escolhido = p
                                break
                        grid_novo[y][x] = escolhido
                    else:
                        grid_novo[y][x] = ref
                else:
                    # Manter referencia
                    grid_novo[y][x] = ref

        return grid_novo


# ─── Paleta aprendida dos dados ──────────────────────────────

def extrair_paleta(grids_cor, grids_papel):
    """Extrai cor media por papel de todos os sprites."""
    paleta = defaultdict(list)
    for grid_cor, grid_papel in zip(grids_cor, grids_papel):
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


def colorir_grid(grid_papel, paleta, angulo_hue=0.0, variacao=3):
    """Colore grid de papeis com CIELAB. Cada pixel = UMA cor solida."""
    h = len(grid_papel)
    w = len(grid_papel[0])
    img = Image.new('RGBA', (w, h))
    pixels = []

    # Pre-computar L/a/b base por papel
    lab_base = {}
    for papel, cor in paleta.items():
        L, a, b = rgb_para_lab(*cor)
        lab_base[papel] = (L, a, b)

    for y in range(h):
        for x in range(w):
            papel = grid_papel[y][x]
            if papel == 'F':
                pixels.append((0, 0, 0, 0))
                continue
            L, a, bl = lab_base.get(papel, (50, 0, 0))
            raio = math.sqrt(a*a + bl*bl)
            if raio < 3: raio = 6
            novo_a = raio * math.cos(angulo_hue)
            novo_b = raio * math.sin(angulo_hue)
            novo_L = L + random.randint(-variacao, variacao)
            cr, cg, cb = lab_para_rgb(novo_L, novo_a, novo_b)
            pixels.append((cr, cg, cb, 255))

    img.putdata(pixels)
    return img


# ============================================================
# MAIN
# ============================================================
print('=' * 60)
print('MCR GERADOR DE ESTRUTURA — Orc sem trapaca')
print('=' * 60)

# 1. Carregar 4 orcs
print('\n--- 1. Carregando 4 orcs ---')
orc_paths = [
    os.path.join(_BASE, 'poc_output', 'orc_hue_ref_0.png'),
    os.path.join(_BASE, 'poc_output', 'orc_hue_ref_1.png'),
    os.path.join(_BASE, 'poc_output', 'orc_nitido_ref.png'),
    os.path.join(_BASE, 'poc_output', 'orc_nitido_ref_big.png'),
]

grids_papel = []
grids_cor = []
for path in orc_paths:
    if os.path.exists(path):
        img = Image.open(path).convert('RGBA')
        if img.size != (32, 32):
            img = img.resize((32, 32), Image.NEAREST)
        gp, gc = tokenizar_papel(img)
        grids_papel.append(gp)
        grids_cor.append(gc)
        opacos = sum(1 for row in gp for t in row if t != 'F')
        print(f'  {os.path.basename(path)}: {opacos} opacos')

print(f'  Total: {len(grids_papel)} sprites carregados')

if len(grids_papel) < 2:
    print('  ERRO: Preciso de pelo menos 2 orcs')
    sys.exit(1)

# 2. Treinar MCR gerador com as estruturas de papel
print('\n--- 2. Treinando MCR gerador ---')
mcr = MCRGerador()
mcr.treinar(grids_papel)
print(f'  Transicoes: {sum(len(v) for v in mcr.transicoes.values())}')
print(f'  Papeis: {mcr.todos_papeis}')

# 3. Treinar discriminador com as estruturas reais
print('\n--- 3. Treinando discriminador ---')
disc = MCRDiscriminador()
disc.treinar(grids_papel)
print(f'  Transicoes disc: {disc.total}')

# 4. Extrair paleta dos dados reais
print('\n--- 4. Paleta aprendida ---')
paleta = extrair_paleta(grids_cor, grids_papel)
for papel, cor in sorted(paleta.items()):
    print(f'  {papel}: RGB({cor[0]}, {cor[1]}, {cor[2]})')

# 5. Gerar estruturas NOVAS via MCR
print('\n--- 5. Gerando 20 estruturas novas ---')
random.seed(42)
resultados = []

for g in range(20):
    temp = 0.5 + random.random() * 0.5
    variacao = 0.1 + random.random() * 0.4
    angulo = random.random() * 2 * math.pi

    # Gerar estrutura nova via MCR
    grid_ref = grids_papel[g % len(grids_papel)]
    grid_novo = mcr.gerar_grid_da_referencia(grid_ref, temperatura=temp, variacao=variacao)

    # Colorir com paleta deterministica
    img_out = colorir_grid(grid_novo, paleta, angulo_hue=angulo)

    # Avaliar com discriminador
    resultado = disc.avaliar(grid_novo)
    score = resultado['score']
    opacos = sum(1 for row in grid_novo for t in row if t != 'F')

    caminho = os.path.join(OUT_DIR, f'orc_mcr_{g:03d}.png')
    img_out.save(caminho)
    resultados.append({'idx': g, 'opacos': opacos, 'score': score, 'temp': temp, 'resultado': resultado})

    if g < 5 or g % 5 == 0:
        print(f'  [{g}] opacos={opacos} score={score:.3f} temp={temp:.2f} var={variacao:.2f}')

# 6. Avaliacao
print('\n--- 6. Avaliacao ---')
scores = [r['score'] for r in resultados]
opacos_list = [r['opacos'] for r in resultados]
print(f'  Score MCR: media={sum(scores)/len(scores):.3f} min={min(scores):.3f} max={max(scores):.3f}')
print(f'  Opacos: media={sum(opacos_list)/len(opacos_list):.0f} min={min(opacos_list)} max={max(opacos_list)}')
print(f'  Aceitaveis (score>0.5): {sum(1 for s in scores if s > 0.5)}/{len(scores)}')

# 7. Melhor e pior
melhor = max(resultados, key=lambda r: r['score'])
pior = min(resultados, key=lambda r: r['score'])
print(f'\n  Melhor [{melhor["idx"]}]: score={melhor["score"]:.3f}')
print(disc.diagnostico(melhor['resultado']))
print(f'  Pior [{pior["idx"]}]: score={pior["score"]:.3f}')
print(disc.diagnostico(pior['resultado']))

# 8. Salvar referencias
for i, path in enumerate(orc_paths):
    if os.path.exists(path):
        img = Image.open(path).convert('RGBA')
        if img.size != (32, 32):
            img = img.resize((32, 32), Image.NEAREST)
        img.save(os.path.join(OUT_DIR, f'ref_{i}.png'))

print(f'\nResultados: {OUT_DIR}')
print('=' * 60)
