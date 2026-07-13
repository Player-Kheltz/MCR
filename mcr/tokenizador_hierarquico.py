"""
mcr.tokenizador_hierarquico — Tokenizador Hierárquico por Entropia Diferencial.

3 níveis:
  Nível 0 (Pixel):   tokens F B S M H + L{n}C{m}
  Nível 1 (Região):  flood fill → regiões conexas com propriedades
  Nível 2 (Relação): adjacência entre regiões com vetores delta

Cada nível pode ser alimentado no mesmo extrair_template_entropico()
e no mesmo MCR. A entropia decide estrutura vs gap em cada nível.
"""
import math
import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional


def _svd_orientacao(pontos: np.ndarray) -> float:
    """Orientação principal via SVD dos pontos 2D.
    
    Retorna ângulo em graus do autovetor principal (0-180).
    Para regiões circulares (baixa excentricidade), retorna -1.
    """
    if len(pontos) < 3:
        return -1.0
    centro = pontos.mean(axis=0)
    centralized = pontos - centro
    _, s, vh = np.linalg.svd(centralized, full_matrices=False)
    excentricidade = s[0] / (s[1] + 1e-10)
    if excentricidade < 1.5:
        return -1.0
    angulo = math.degrees(math.atan2(vh[0, 1], vh[0, 0]))
    return angulo % 180


def _papel(token: str) -> str:
    """Extrai papel base do token: 'F' fundo, 'B' borda, 'L' interior lum."""
    if token == 'F':
        return 'F'
    if token == 'B':
        return 'B'
    if token.startswith('L'):
        return 'L'
    return token


def extrair_regioes(
    grid_tokens: List[List[str]],
    modo: str = 'papel',
) -> List[Dict]:
    """Flood fill em pixels adjacentes com o MESMO token (ou mesmo papel).
    
    Args:
        grid_tokens: grid 2D [y][x] de tokens (F, B, L0C0, etc.)
        modo: 'papel' → agrupa por papel (B, L) — para anatomia
              'token' → agrupa por token exato — para textura
    
    Returns:
        lista de regiões, cada uma com:
          id, papel, area, centroide, bbox, orientacao, pixels
    """
    h = len(grid_tokens)
    w = len(grid_tokens[0]) if h else 0
    visited = [[False] * w for _ in range(h)]
    regioes = []
    
    def _mesmo(a: str, b: str) -> bool:
        if modo == 'papel':
            return _papel(a) == _papel(b)
        return a == b
    
    for sy in range(h):
        for sx in range(w):
            if visited[sy][sx]:
                continue
            token = grid_tokens[sy][sx]
            if token == 'F':
                visited[sy][sx] = True
                continue
            
            # BFS flood fill
            stack = [(sx, sy)]
            visited[sy][sx] = True
            pixels = []
            
            while stack:
                x, y = stack.pop()
                pixels.append((x, y))
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx]:
                        if _mesmo(grid_tokens[ny][nx], token):
                            visited[ny][nx] = True
                            stack.append((nx, ny))
            
            if len(pixels) < 2:
                continue
            
            # Propriedades da região
            xs = [p[0] for p in pixels]
            ys = [p[1] for p in pixels]
            papel = _papel(token)
            
            pontos = np.array(pixels)
            area = len(pixels)
            centroide = (sum(xs) / area, sum(ys) / area)
            bbox = (min(xs), min(ys), max(xs), max(ys))
            orientacao = _svd_orientacao(pontos)
            
            regioes.append({
                'id': len(regioes),
                'papel': papel,
                'token': token,
                'area': area,
                'centroide': centroide,
                'bbox': bbox,
                'orientacao': orientacao,
                'pixels': pixels,
                'excentricidade': max(1.0, (bbox[3]-bbox[1]+1) / max(1, bbox[2]-bbox[0]+1)),
                'cor_media_lab': (50, 0, 0),
            })
    
    return regioes


def _bbox_dilatada(bbox, dilation=1):
    """Expande bounding box em N pixels."""
    xmin, ymin, xmax, ymax = bbox
    return (xmin - dilation, ymin - dilation, xmax + dilation, ymax + dilation)


def _bboxes_tocam(b1, b2):
    """True se duas bounding boxes (mesmo que dilatadas) se tocam."""
    return not (b1[2] < b2[0] or b2[2] < b1[0] or b1[3] < b2[1] or b2[3] < b1[1])


def extrair_relacoes(regioes: List[Dict]) -> List[Dict]:
    """Extrai relações entre pares de regiões adjacentes.
    
    Args:
        regioes: lista de regiões (saída de extrair_regioes)
    
    Returns:
        lista de relações, cada uma com:
          id_a, id_b, tipo_adj, delta_centroide, delta_area, delta_orientacao
    """
    relacoes = []
    n = len(regioes)
    
    for i in range(n):
        bbox_i = _bbox_dilatada(regioes[i]['bbox'], dilation=1)
        for j in range(i + 1, n):
            bbox_j = _bbox_dilatada(regioes[j]['bbox'], dilation=1)
            
            if not _bboxes_tocam(bbox_i, bbox_j):
                continue
            
            # Verificar adjacência real: pixels de uma região tocam pixels da outra?
            # Checar bordas da bbox original (menos custoso que todos os pixels)
            bi = regioes[i]['bbox']
            bj = regioes[j]['bbox']
            tocam = not (bi[2] < bj[0] - 1 or bj[2] < bi[0] - 1 or
                         bi[3] < bj[1] - 1 or bj[3] < bi[1] - 1)
            
            ci = regioes[i]['centroide']
            cj = regioes[j]['centroide']
            delta_cx = cj[0] - ci[0]
            delta_cy = cj[1] - ci[1]
            
            delta_area = regioes[j]['area'] / (regioes[i]['area'] + 1e-10)
            
            oi = regioes[i]['orientacao']
            oj = regioes[j]['orientacao']
            if oi >= 0 and oj >= 0:
                delta_orientacao = abs(oj - oi) % 180
            else:
                delta_orientacao = -1.0
            
            if tocam:
                tipo_adj = 'toca'
            else:
                tipo_adj = 'proxima'
            
            relacoes.append({
                'id_a': i,
                'id_b': j,
                'tipo_adj': tipo_adj,
                'delta_centroide': (delta_cx, delta_cy),
                'delta_area': delta_area,
                'delta_orientacao': delta_orientacao,
            })
    
    return relacoes


def propriedades_para_vetor(regioes: List[Dict]) -> Dict[str, List]:
    """Converte lista de regiões em vetores de propriedades para template entrópico.
    
    Retorna dict onde cada chave é uma propriedade (area, orientacao, etc.)
    e o valor é uma lista de valores (um por região).
    """
    props = defaultdict(list)
    for r in regioes:
        props['papel'].append(r['papel'])
        props['area'].append(r['area'])
        props['centroide_x'].append(r['centroide'][0])
        props['centroide_y'].append(r['centroide'][1])
        props['orientacao'].append(r['orientacao'])
        props['bbox_w'].append(r['bbox'][2] - r['bbox'][0] + 1)
        props['bbox_h'].append(r['bbox'][3] - r['bbox'][1] + 1)
    return dict(props)


def token_grid_para_linear(grid: List[List[str]]) -> List[str]:
    """Converte grid 2D [y][x] para sequência linear com marcadores R{y}."""
    toks = []
    for y, row in enumerate(grid):
        toks.append(f'R{y}')
        toks.extend(row)
    return toks


def token_linear_para_grid(tokens: List[str], largura: int = 32) -> List[List[str]]:
    """Converte sequência linear com R{y} de volta para grid 2D."""
    grid = [['F'] * largura for _ in range(largura)]
    y = x = 0
    for t in tokens:
        if t.startswith('R'):
            y = int(t[1:])
            x = 0
        elif y < len(grid) and x < len(grid[0]):
            grid[y][x] = t
            x += 1
    return grid


# ─── Função única de pipeline ─────────────────────────────────


def tokenizar_hierarquico(grid_tokens: List[List[str]]) -> Dict:
    """Pipeline completo: grid → regiões → relações.
    
    Args:
        grid_tokens: grid 2D [y][x] de tokens
    
    Returns:
        dict com 'nivel0' (grid original), 'nivel1' (regiões), 'nivel2' (relações)
    """
    regioes = extrair_regioes(grid_tokens)
    relacoes = extrair_relacoes(regioes)
    props = propriedades_para_vetor(regioes)
    
    return {
        'nivel0': grid_tokens,
        'nivel1': {
            'regioes': regioes,
            'propriedades': props,
            'total': len(regioes),
        },
        'nivel2': {
            'relacoes': relacoes,
            'total': len(relacoes),
        },
    }


def resumir_hierarquico(h: Dict) -> str:
    """Resumo textual do resultado hierárquico."""
    n0 = len(h['nivel0']) * len(h['nivel0'][0])
    n1 = h['nivel1']['total']
    n2 = h['nivel2']['total']
    
    # Estatísticas das regiões
    areas = [r['area'] for r in h['nivel1']['regioes']]
    papeis = Counter(r['papel'] for r in h['nivel1']['regioes'])
    
    partes = []
    for papel, count in sorted(papeis.items()):
        partes.append(f'{count}x{papel}')
    
    return (
        f'N0:{n0}px N1:{n1}reg({", ".join(partes)}) '
        f'N2:{n2}rel '
        f'areas:{min(areas):.0f}-{max(areas):.0f}'
    )


# ─── Ordenação consistente de regiões ─────────────────────────


def ordenar_regioes(regioes: List[Dict]) -> List[Dict]:
    """Ordena regiões por papel (B antes de L), depois por posição (y, x).
    
    Garante que regiões correspondentes entre sprites fiquem na mesma posição
    na lista, permitindo template entrópico nas propriedades.
    """
    return sorted(regioes, key=lambda r: (
        0 if r['papel'] == 'B' else 1 if r['papel'] == 'L' else 2,
        r['centroide'][1],  # y
        r['centroide'][0],  # x
    ))


# ─── Geração Hierárquica ──────────────────────────────────────


def _convex_hull(pontos: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Convex hull de um conjunto de pontos 2D (algoritmo monótono)."""
    pontos = sorted(set(pontos))
    if len(pontos) <= 3:
        return pontos
    
    def _sentido(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    
    lower = []
    for p in pontos:
        while len(lower) >= 2 and _sentido(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    
    upper = []
    for p in reversed(pontos):
        while len(upper) >= 2 and _sentido(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    
    return lower[:-1] + upper[:-1]


def _rasterizar_hull(hull: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Rasteriza um polígono convexo (pontos do hull) para pixels internos."""
    if not hull:
        return []
    ys = [p[1] for p in hull]
    min_y, max_y = min(ys), max(ys)
    pixels = []
    
    for y in range(min_y, max_y + 1):
        # Encontrar interseções da scanline com o polígono
        inter_xs = []
        n = len(hull)
        for i in range(n):
            x1, y1 = hull[i]
            x2, y2 = hull[(i + 1) % n]
            if (y1 <= y < y2) or (y2 <= y < y1):
                x_inter = x1 + (y - y1) * (x2 - x1) / (y2 - y1 + 1e-10)
                inter_xs.append(x_inter)
        
        if len(inter_xs) >= 2:
            x_min = int(round(min(inter_xs)))
            x_max = int(round(max(inter_xs)))
            for x in range(x_min, x_max + 1):
                pixels.append((x, y))
    
    return pixels


def gerar_regioes_do_template(
    template_regioes: List[Dict],
    temperatura: float = 0.5,
    variacao_posicao: float = 2.0,
    variacao_area: float = 0.2,
) -> List[Dict]:
    """Gera novas regiões a partir de um template de regiões de referência.
    
    Cada região é tratada como uma FORMA (convex hull do seus pixels).
    A forma é transformada como um todo (translação, escala, rotação),
    depois re-rasterizada. Isso preserva a integridade estrutural.
    
    Args:
        template_regioes: regiões de referência (ordenadas)
        temperatura: 0 = cópia exata, 1 = variação máxima
        variacao_posicao: desvio padrão do deslocamento em pixels
        variacao_area: fração de variação da área (0.2 = ±20%)
    
    Returns:
        novas regiões com pixels reposicionados
    """
    import random
    
    novas = []
    for reg in template_regioes:
        papel = reg['papel']
        pixels = reg['pixels']
        centro = reg['centroide']
        
        # Convex hull da região
        hull = _convex_hull(pixels)
        if len(hull) < 3:
            continue
        
        # Transformar hull como um todo
        dx = random.gauss(0, variacao_posicao * temperatura)
        dy = random.gauss(0, variacao_posicao * temperatura)
        escala = 1.0 + random.gauss(0, variacao_area * temperatura)
        escala = max(0.5, min(1.5, escala))
        angulo_rot = random.gauss(0, 10.0 * temperatura)  # graus
        rad = math.radians(angulo_rot)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        
        hull_transformado = []
        for (px, py) in hull:
            # Centralizar no centroide
            rx = px - centro[0]
            ry = py - centro[1]
            # Rotacionar
            rrx = rx * cos_r - ry * sin_r
            rry = rx * sin_r + ry * cos_r
            # Escalar
            rrx *= escala
            rry *= escala
            # Transladar de volta + deslocamento
            nx = int(round(rrx + centro[0] + dx))
            ny = int(round(rry + centro[1] + dy))
            hull_transformado.append((nx, ny))
        
        # Rasterizar hull transformado
        novos_pixels = _rasterizar_hull(hull_transformado)
        
        # Recalcular propriedades
        novos_pixels = [(x, y) for (x, y) in novos_pixels if 0 <= x < 32 and 0 <= y < 32]
        if len(novos_pixels) < 2:
            continue
        
        xs = [p[0] for p in novos_pixels]
        ys = [p[1] for p in novos_pixels]
        area = len(novos_pixels)
        centroide = (sum(xs) / area, sum(ys) / area)
        bbox = (min(xs), min(ys), max(xs), max(ys))
        orientacao = -1.0
        if len(novos_pixels) >= 3:
            orientacao = _svd_orientacao(np.array(novos_pixels))
        
        novas.append({
            'id': len(novas),
            'papel': papel,
            'token': reg['token'],
            'area': area,
            'centroide': centroide,
            'bbox': bbox,
            'orientacao': orientacao,
            'pixels': novos_pixels,
        })
    
    return novas


def regioes_para_grid(
    regioes: List[Dict],
    largura: int = 32,
    altura: int = 32,
) -> List[List[str]]:
    """Converte lista de regiões de volta para grid de tokens.
    
    Pixels de cada região recebem o token da região ('B' ou 'L' base).
    Regiões sobrepostas: a última na lista vence.
    """
    grid = [['F'] * largura for _ in range(altura)]
    
    for reg in regioes:
        papel = reg['papel']
        token = papel  # usar papel como token (B ou L)
        for (x, y) in reg['pixels']:
            if 0 <= x < largura and 0 <= y < altura:
                grid[y][x] = token
    
    return grid


def regioes_para_grid_com_borda(
    regioes: List[Dict],
    largura: int = 32,
    altura: int = 32,
) -> List[List[str]]:
    """Converte regiões para grid, marcando bordas internas entre B e L.
    
    Pixels L adjacentes a pixels B viram 'D' (detalhe).
    Pixels B adjacentes a F permanecem 'B'.
    """
    grid = [['F'] * largura for _ in range(altura)]
    papel_grid = [['F'] * largura for _ in range(altura)]
    
    for reg in regioes:
        papel = reg['papel']
        for (x, y) in reg['pixels']:
            if 0 <= x < largura and 0 <= y < altura:
                papel_grid[y][x] = papel
                grid[y][x] = papel
    
    # Detectar borda entre L e B
    for y in range(altura):
        for x in range(largura):
            if papel_grid[y][x] == 'L':
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < largura and 0 <= ny < altura:
                        if papel_grid[ny][nx] == 'B':
                            grid[y][x] = 'D'
                            break
    
    return grid
