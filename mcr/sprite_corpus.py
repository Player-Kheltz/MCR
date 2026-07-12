"""
mcr.sprite_corpus — Carregador do corpus categorizado de sprites Tibia.

Schema do corpus:
  poc_output/sprites_categorizados/{categoria}/*.png
  Cada PNG = 32x32 RGBA, extraido via SpriteExtractor + items.xml/monsters.xml

Uso:
    from mcr.sprite_corpus import carregar_categoria, listar_categorias
    sprites = carregar_categoria('sword_weapons')  # List[np.array] 32x32x4
    cats = listar_categorias()  # {'sword_weapons': 80, 'shields': 80, ...}
"""
import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from mcr.paths import POC_OUTPUT_DIR

CORPUS_DIR = POC_OUTPUT_DIR / 'sprites_categorizados'


def _listar_pngs(diretorio: Path) -> List[Path]:
    """Lista todos os PNGs em um diretorio, ordenados por nome."""
    if not diretorio.exists():
        return []
    return sorted(diretorio.glob('*.png'))


def listar_categorias(minimo: int = 0) -> Dict[str, int]:
    """Lista categorias disponiveis com contagem de sprites.
    
    Args:
        minimo: numero minimo de sprites para incluir (0 = todas)
    
    Returns:
        dict {nome_categoria: n_sprites}
    """
    resultado = {}
    if not CORPUS_DIR.exists():
        return resultado
    
    for item in sorted(CORPUS_DIR.iterdir()):
        if item.is_dir() and item.name != 'resumo.json':
            pngs = _listar_pngs(item)
            if len(pngs) >= minimo:
                resultado[item.name] = len(pngs)
    
    return resultado


def carregar_categoria(
    nome: str,
    max_sprites: int = 0,
    tamanho: Tuple[int, int] = (32, 32),
) -> List[np.ndarray]:
    """Carrega todos os sprites de uma categoria como arrays numpy.
    
    Args:
        nome: nome do diretorio da categoria (ex: 'sword_weapons')
        max_sprites: limite de sprites a carregar (0 = todos)
        tamanho: (largura, altura) para resize se necessario
    
    Returns:
        lista de arrays numpy shape (altura, largura, 4) dtype uint8 (RGBA)
    """
    categoria_dir = CORPUS_DIR / nome
    if not categoria_dir.exists():
        raise FileNotFoundError(f"Categoria nao encontrada: {nome} ({categoria_dir})")
    
    pngs = _listar_pngs(categoria_dir)
    if not pngs:
        raise ValueError(f"Nenhum PNG encontrado em {categoria_dir}")
    
    if max_sprites > 0:
        pngs = pngs[:max_sprites]
    
    sprites = []
    for png_path in pngs:
        try:
            from PIL import Image
            img = Image.open(png_path).convert('RGBA')
            if img.size != tamanho:
                img = img.resize(tamanho, Image.NEAREST)
            arr = np.array(img, dtype=np.uint8)
            sprites.append(arr)
        except Exception as e:
            print(f'[sprite_corpus] Aviso: falha ao carregar {png_path.name}: {e}')
            continue
    
    return sprites


def carregar_todas(
    minimo: int = 50,
    max_sprites: int = 0,
    tamanho: Tuple[int, int] = (32, 32),
) -> Dict[str, List[np.ndarray]]:
    """Carrega todas as categorias que tenham >= minimo sprites.
    
    Args:
        minimo: numero minimo de sprites para incluir a categoria
        max_sprites: limite por categoria (0 = todos)
        tamanho: (largura, altura)
    
    Returns:
        dict {categoria: [arrays numpy]}
    """
    cats = listar_categorias(minimo=minimo)
    resultado = {}
    for nome, count in cats.items():
        sprites = carregar_categoria(nome, max_sprites=max_sprites, tamanho=tamanho)
        if sprites:
            resultado[nome] = sprites
    return resultado


def extrair_grid_papel(
    sprite_rgba: np.ndarray,
    bg_estimator: str = 'borda',
) -> Tuple[List[List[str]], List[List[tuple]]]:
    """Converte sprite RGBA para grid de papel (B/L/F) + grid de cor RGB.
    
    Identico a tokenizar_completo() do pipeline_nitido, mas opera em numpy.
    
    Args:
        sprite_rgba: array (H, W, 4) uint8 RGBA
        bg_estimator: 'borda' = cor mais comum na borda = background
    
    Returns:
        (grid_papel, grid_cor) onde:
        - grid_papel: lista de listas de strings ('F', 'B', 'L')
        - grid_cor: lista de listas de tuplas (r, g, b)
    """
    h, w = sprite_rgba.shape[:2]
    MAGENTA = (255, 0, 255)
    
    # Estimar background da borda
    borda_cores = []
    for x in range(w):
        r, g, b, a = sprite_rgba[0, x]
        if a > 128:
            borda_cores.append((int(r), int(g), int(b)))
        r, g, b, a = sprite_rgba[h-1, x]
        if a > 128:
            borda_cores.append((int(r), int(g), int(b)))
    for y in range(h):
        r, g, b, a = sprite_rgba[y, 0]
        if a > 128:
            borda_cores.append((int(r), int(g), int(b)))
        r, g, b, a = sprite_rgba[y, w-1]
        if a > 128:
            borda_cores.append((int(r), int(g), int(b)))
    
    if borda_cores:
        from collections import Counter
        bg = Counter(borda_cores).most_common(1)[0][0]
    else:
        bg = MAGENTA
    
    grid_papel = [['F'] * w for _ in range(h)]
    grid_cor = [[(0, 0, 0)] * w for _ in range(h)]
    
    for y in range(h):
        for x in range(w):
            r, g, b, a = int(sprite_rgba[y, x, 0]), int(sprite_rgba[y, x, 1]), int(sprite_rgba[y, x, 2]), int(sprite_rgba[y, x, 3])
            if a < 128 or (r, g, b) == MAGENTA or (r, g, b) == bg:
                grid_papel[y][x] = 'F'
                continue
            
            eh_borda = False
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    nr, ng, nb, na = int(sprite_rgba[ny, nx, 0]), int(sprite_rgba[ny, nx, 1]), int(sprite_rgba[ny, nx, 2]), int(sprite_rgba[ny, nx, 3])
                    if na < 128 or (nr, ng, nb) == MAGENTA or (nr, ng, nb) == bg:
                        eh_borda = True
                        break
            
            grid_papel[y][x] = 'B' if eh_borda else 'L'
            grid_cor[y][x] = (r, g, b)
    
    return grid_papel, grid_cor


def extrair_paleta_mediana(
    grid_cor: List[List[tuple]],
    grid_papel: List[List[str]],
) -> Dict[str, Tuple[int, int, int]]:
    """Extrai mediana de cor por papel (B, L) — robusta a outliers.
    
    Decisao de Design #3: usar MEDIANA, nao media.
    Se sub-clusters existem dentro do papel, faz sub-clustering.
    
    Args:
        grid_cor: grid 2D de cores RGB
        grid_papel: grid 2D de papeis (B, L, F)
    
    Returns:
        dict {papel: (r_median, g_median, b_median)}
    """
    from collections import defaultdict
    
    por_papel = defaultdict(list)
    for y in range(len(grid_cor)):
        for x in range(len(grid_cor[0])):
            papel = grid_papel[y][x]
            if papel != 'F':
                por_papel[papel].append(grid_cor[y][x])
    
    mediana = {}
    for papel, cores in por_papel.items():
        if not cores:
            continue
        rs = sorted(c[0] for c in cores)
        gs = sorted(c[1] for c in cores)
        bs = sorted(c[2] for c in cores)
        n = len(rs)
        mediana[papel] = (rs[n//2], gs[n//2], bs[n//2])
    
    return mediana


def salvar_grid_como_png(
    grid_papel: List[List[str]],
    paleta: Dict[str, Tuple[int, int, int]],
    caminho: str,
    angulo_hue: float = 0.0,
    variacao: int = 0,
):
    """Salva grid B/L/F + paleta como PNG 32x32."""
    from PIL import Image
    import math
    from mcr.cielab import rgb_para_lab, lab_para_rgb
    
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
            
            r, g, b = paleta.get(papel, (128, 128, 128))
            
            if angulo_hue != 0.0 or variacao > 0:
                L, a, bl = rgb_para_lab(r, g, b)
                raio = math.sqrt(a*a + bl*bl)
                if raio < 3:
                    raio = 6
                novo_a = raio * math.cos(angulo_hue)
                novo_b = raio * math.sin(angulo_hue)
                import random
                novo_L = L + random.randint(-variacao, variacao) if variacao > 0 else L
                r, g, b = lab_para_rgb(novo_L, novo_a, novo_b)
            
            pixels.append((r, g, b, 255))
    
    img.putdata(pixels)
    img.save(caminho)


def salvar_referencias(
    categoria: str,
    sprites_rgba: List[np.ndarray],
    max_salvar: int = 5,
    out_dir: str = None,
) -> List[str]:
    """Salva primeiros N sprites de uma categoria como PNGs de referencia.
    
    Returns:
        lista de paths salvos
    """
    if out_dir is None:
        out_dir = str(POC_OUTPUT_DIR / 'sprite_corpus_refs' / categoria)
    os.makedirs(out_dir, exist_ok=True)
    
    paths = []
    from PIL import Image
    
    for i, arr in enumerate(sprites_rgba[:max_salvar]):
        img = Image.fromarray(arr, 'RGBA')
        path = os.path.join(out_dir, f'ref_{i:03d}.png')
        img.save(path)
        paths.append(path)
    
    return paths


def sprite_para_ascii(grid_papel: List[List[str]], largura: int = 32) -> str:
    """Converte grid B/L/F para ASCII para inspecao visual no terminal.
    
    Uso: debug, worklog, validacao pelos 3 arquitetos (chat-only).
    
    Mapeamento:
      ' ' (espaco) = F (fundo)
      # = B (borda)
      + = L (interior)
      . = D (detalhe)
      : = S (sombra)
    
    Returns:
        string multi-linha com representacao ASCII
    """
    MAPA = {'F': ' ', 'B': '#', 'L': '+', 'D': '.', 'S': ':', 'H': "'"}
    linhas = []
    for row in grid_papel:
        linha = ''.join(MAPA.get(t, '?') for t in row)
        linhas.append(linha)
    return '\n'.join(linhas)


def jaccard_silhueta(sprites: list) -> float:
    """Jaccard medio entre todos os pares de sprites.

    Mede diversidade morfologica: 0.0 = totalmente diferentes, 1.0 = identicos.

    Para cada par (i, j), calcula:
        |intersecao opacos| / |uniao opacos|
    onde opaco = pixel != 'F' (ou alpha > 0 para arrays numpy).

    Args:
        sprites: lista de grids B/L/F (List[List[str]]) OU arrays numpy (H,W,4)

    Returns:
        Jaccard medio sobre todos os pares C(n, 2).
    """
    from itertools import combinations

    def _para_mascara(item):
        if isinstance(item, np.ndarray):
            h, w = item.shape[:2]
            if item.ndim == 3 and item.shape[2] >= 4:
                return item[:, :, 3] > 128
            return item[:, :, 0] != 0
        h = len(item)
        w = len(item[0]) if h else 0
        mask = np.zeros((h, w), dtype=bool)
        for y in range(h):
            for x in range(w):
                mask[y, x] = item[y][x] != 'F'
        return mask

    mascaras = [_para_mascara(s) for s in sprites]
    n = len(mascaras)
    if n < 2:
        return 0.0

    total = 0.0
    count = 0
    for i, j in combinations(range(n), 2):
        inter = np.sum(mascaras[i] & mascaras[j])
        uni = np.sum(mascaras[i] | mascaras[j])
        if uni > 0:
            total += inter / uni
        count += 1

    return total / count if count > 0 else 0.0


def jaccard_gerados_vs_reais(gerados: list, reais: list) -> float:
    """Jaccard medio entre sprites gerados e reais.

    Mede realismo de silhueta: valores proximos ao Jaccard reais-vs-reais
    indicam que gerados tem forma similar aos reais.

    Args:
        gerados: lista de grids ou arrays numpy
        reais: lista de grids ou arrays numpy

    Returns:
        Jaccard medio entre todos os pares (gerado, real).
    """
    def _para_mascara(item):
        if isinstance(item, np.ndarray):
            h, w = item.shape[:2]
            if item.ndim == 3 and item.shape[2] >= 4:
                return item[:, :, 3] > 128
            return item[:, :, 0] != 0
        h = len(item)
        w = len(item[0]) if h else 0
        mask = np.zeros((h, w), dtype=bool)
        for y in range(h):
            for x in range(w):
                mask[y][x] = item[y][x] != 'F'
        return mask

    mascaras_g = [_para_mascara(s) for s in gerados]
    mascaras_r = [_para_mascara(s) for s in reais]

    total = 0.0
    count = 0
    for mg in mascaras_g:
        for mr in mascaras_r:
            inter = np.sum(mg & mr)
            uni = np.sum(mg | mr)
            if uni > 0:
                total += inter / uni
            count += 1

    return total / count if count > 0 else 0.0


def sprite_rgba_para_ascii(sprite_rgba: np.ndarray) -> str:
    """Converte sprite RGBA direto para ASCII (estimativa por luminancia).
    
    Uso rapido sem passar por grid_papel.
    """
    h, w = sprite_rgba.shape[:2]
    linhas = []
    for y in range(h):
        linha = ''
        for x in range(w):
            r, g, b, a = int(sprite_rgba[y, x, 0]), int(sprite_rgba[y, x, 1]), int(sprite_rgba[y, x, 2]), int(sprite_rgba[y, x, 3])
            if a < 128:
                linha += ' '
            else:
                lum = (r + g + b) / 3
                if lum < 40:
                    linha += '#'
                elif lum < 100:
                    linha += '+'
                elif lum < 160:
                    linha += '.'
                else:
                    linha += "'"
        linhas.append(linha)
    return '\n'.join(linhas)
