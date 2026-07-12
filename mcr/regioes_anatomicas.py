"""
mcr.regioes_anatomicas — Extrator de regiões anatômicas.

Duas abordagens:
  1. cortar_em_regioes: projeção de densidade 1D (bom para itens com partes separadas)
  2. extrair_regioes_cromaticas: clustering CIELAB + flood fill (bom para criaturas compactas)

Zero dependências externas — apenas numpy + mcr.cielab.
"""
import math
import random as _rnd
import numpy as np
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional

from mcr.cielab import (
    rgb_para_lab, lab_para_rgb, delta_e76,
    clusterizar_lab, detectar_picos,
    limiar_automatico, clusterizar_por_picos,
)


def _papel(tok: str) -> str:
    if tok == 'F': return 'F'
    if tok == 'B': return 'B'
    if tok.startswith('L'): return 'L'
    if tok == 'D': return 'D'
    return tok


def projetar_densidade(grid_papel: List[List[str]]) -> Tuple[List[int], List[int]]:
    """Projeta pixels opacos nos eixos X e Y.
    
    Retorna:
        dens_x[y] = número de pixels opacos na linha y
        dens_y[x] = número de pixels opacos na coluna x
    """
    h = len(grid_papel)
    w = len(grid_papel[0])
    dens_x = [0] * h  # densidade por linha
    dens_y = [0] * w  # densidade por coluna
    
    for y in range(h):
        for x in range(w):
            if grid_papel[y][x] != 'F':
                dens_x[y] += 1
                dens_y[x] += 1
    
    return dens_x, dens_y


def projetar_diversidade(grid_papel: List[List[str]]) -> Tuple[List[int], List[int]]:
    """Projeta diversidade de tokens nos eixos X e Y.
    
    Conta quantos tipos diferentes de tokens aparecem em cada linha/coluna.
    Transições entre partes anatômicas frequentemente têm alta diversidade.
    
    Retorna:
        div_x[y] = número de tipos de tokens na linha y
        div_y[x] = número de tipos de tokens na coluna x
    """
    h = len(grid_papel)
    w = len(grid_papel[0])
    div_x = [0] * h
    div_y = [0] * w
    
    for y in range(h):
        tipos = set()
        for x in range(w):
            if grid_papel[y][x] != 'F':
                tipos.add(grid_papel[y][x])
        div_x[y] = len(tipos)
    
    for x in range(w):
        tipos = set()
        for y in range(h):
            if grid_papel[y][x] != 'F':
                tipos.add(grid_papel[y][x])
        div_y[x] = len(tipos)
    
    return div_x, div_y


def projetar_instante(grid_papel: List[List[str]]) -> Tuple[List[float], List[float]]:
    """Projeta "inércia" (momento de inércia lateral) nos eixos X e Y.
    
    Para cada linha, calcula a dispersão horizontal dos pixels opacos.
    Um pico de inércia indica uma linha onde os pixels estão muito dispersos
    (ex: ombros largos), enquanto um vale indica uma linha concentrada (pescoço).
    
    Retorna:
        iner_x[y] = momento de inércia horizontal da linha y (normalizado)
        iner_y[x] = momento de inércia vertical da coluna x (normalizado)
    """
    h = len(grid_papel)
    w = len(grid_papel[0])
    iner_x = [0.0] * h
    iner_y = [0.0] * w
    
    # Eixo X: momento por linha
    for y in range(h):
        xs = [x for x in range(w) if grid_papel[y][x] != 'F']
        if len(xs) < 2:
            continue
        media = sum(xs) / len(xs)
        var = sum((x - media)**2 for x in xs) / len(xs)
        iner_x[y] = math.sqrt(var)  # desvio padrão
    
    # Eixo Y: momento por coluna
    for x in range(w):
        ys = [y for y in range(h) if grid_papel[y][x] != 'F']
        if len(ys) < 2:
            continue
        media = sum(ys) / len(ys)
        var = sum((y - media)**2 for y in ys) / len(ys)
        iner_y[x] = math.sqrt(var)
    
    return iner_x, iner_y


def encontrar_vales(densidade: List[int], suavizacao: int = 1, min_pico: int = 1, 
                    profundidade: float = 0.5) -> List[int]:
    """Encontra índices de vales (mínimos locais) na curva de densidade.
    
    Um vale é um ponto onde a densidade cai abaixo dos vizinhos
    e depois sobe novamente. Isso indica um corte anatômico.
    
    Args:
        densidade: array de densidade
        suavizacao: raio de suavização (mediana móvel)
        min_pico: densidade mínima para considerar um pico válido
        profundidade: fração mínima do pico para considerar um vale profundo (0-1)
    
    Returns:
        lista de índices onde há vales (cortes anatômicos)
    """
    n = len(densidade)
    if n < 5:
        return []
    
    # 1. Suavizar com mediana móvel (leve)
    suave = []
    for i in range(n):
        ini = max(0, i - suavizacao)
        fim = min(n, i + suavizacao + 1)
        vizinhos = densidade[ini:fim]
        suave.append(sorted(vizinhos)[len(vizinhos)//2])
    
    # 2. Encontrar TODOS os mínimos locais
    minimos = []
    for i in range(1, n - 1):
        if suave[i] <= suave[i-1] and suave[i] <= suave[i+1]:
            minimos.append((i, suave[i]))
    
    if not minimos:
        return []
    
    # 3. Filtrar: só manter vales que são "profundos" em relação aos vizinhos
    vales = []
    for idx, val in minimos:
        # Encontrar o pico mais próximo à esquerda
        pico_esq = 0
        for j in range(idx - 1, -1, -1):
            if suave[j] > val:
                pico_esq = max(pico_esq, suave[j])
                break
        
        # Encontrar o pico mais próximo à direita
        pico_dir = 0
        for j in range(idx + 1, n):
            if suave[j] > val:
                pico_dir = max(pico_dir, suave[j])
                break
        
        pico_min = min(pico_esq, pico_dir)
        # O vale deve ser significativamente menor que os picos
        if pico_min > 0 and val <= pico_min * profundidade:
            vales.append(idx)
    
    # 4. Se não encontrou vales profundos, usar abordagem mais suave:
    #    split pela média global
    if not vales and len(densidade) > 8:
        media = sum(densidade) / len(densidade)
        # Encontrar o ponto mais abaixo da média
        menor_diff = 0
        menor_idx = n // 2
        for i in range(2, n - 2):
            diff = suave[i] - media
            if diff < menor_diff:
                menor_diff = diff
                menor_idx = i
        if menor_diff < -1:
            vales.append(menor_idx)
    
    return sorted(set(vales))


def cortar_em_regioes(
    grid_papel: List[List[str]],
    grid_cor: Optional[List[List[tuple]]] = None,
    min_regiao: int = 4,
    metodo: str = 'combinado',
) -> List[Dict]:
    """Corta o sprite em regiões anatômicas.
    
    Algoritmo:
    1. Projetar features (densidade, diversidade, inércia) nos eixos X e Y
    2. Encontrar vales em todas as features
    3. Combinar vales: se ≥2 features concordam no mesmo local → corte anatômico
    4. Usar cortes para criar retângulos
    5. Cada retângulo com pixels opacos = uma região
    
    Args:
        grid_papel: grid 2D de tokens (B, L, F, etc.)
        grid_cor: grid 2D de cores RGB (opcional)
        min_regiao: número mínimo de pixels para considerar uma região
        metodo: 'densidade', 'diversidade', 'combinado'
    
    Returns:
        lista de regiões
    """
    h = len(grid_papel)
    w = len(grid_papel[0])
    
    # 1. Projetar features
    dens_x, dens_y = projetar_densidade(grid_papel)
    div_x, div_y = projetar_diversidade(grid_papel)
    iner_x, iner_y = projetar_instante(grid_papel)
    
    # 2. Encontrar vales em cada feature
    vales_dens_y = encontrar_vales(dens_x, suavizacao=1, min_pico=1, profundidade=0.6)
    vales_dens_x = encontrar_vales(dens_y, suavizacao=1, min_pico=1, profundidade=0.6)
    vales_div_y = encontrar_vales(div_x, suavizacao=1, min_pico=0, profundidade=0.7)
    vales_div_x = encontrar_vales(div_y, suavizacao=1, min_pico=0, profundidade=0.7)
    vales_iner_y = encontrar_vales(iner_x, suavizacao=1, min_pico=0, profundidade=0.5)
    vales_iner_x = encontrar_vales(iner_y, suavizacao=1, min_pico=0, profundidade=0.5)
    
    # 3. Combinar: aceitar corte se ≥2 features concordam (dentro de tolerância)
    tol = 2  # pixels de tolerância
    
    def combinar_vales(*listas_vales):
        contagem = {}
        for lista in listas_vales:
            for v in lista:
                # Contar vizinhos próximos
                encontrado = False
                for k in contagem:
                    if abs(v - k) <= tol:
                        contagem[k] += 1
                        encontrado = True
                        break
                if not encontrado:
                    contagem[v] = 1
        # Aceitar vales com concordância ≥ 2
        return sorted([v for v, c in contagem.items() if c >= 2])
    
    vales_y = combinar_vales(vales_dens_y, vales_div_y, vales_iner_y)
    vales_x = combinar_vales(vales_dens_x, vales_div_x, vales_iner_x)
    
    # Se poucos vales combinados, adicionar os mais fortes de cada feature
    if len(vales_y) < 2:
        extras = set(vales_dens_y + vales_div_y + vales_iner_y)
        for e in sorted(extras):
            if len(vales_y) >= 3:
                break
            if e not in vales_y:
                vales_y.append(e)
        vales_y = sorted(vales_y)
    
    if len(vales_x) < 2:
        extras = set(vales_dens_x + vales_div_x + vales_iner_x)
        for e in sorted(extras):
            if len(vales_x) >= 3:
                break
            if e not in vales_x:
                vales_x.append(e)
        vales_x = sorted(vales_x)
    
    # 4. Criar limites de corte
    limites_y = [0] + vales_y + [h]
    limites_x = [0] + vales_x + [w]
    
    # 5. Extrair retângulos
    regioes = []
    reg_id = 0
    
    for i in range(len(limites_y) - 1):
        for j in range(len(limites_x) - 1):
            y1, y2 = limites_y[i], limites_y[i+1]
            x1, x2 = limites_x[j], limites_x[j+1]
            
            pixels = []
            tokens = []
            for y in range(y1, y2):
                for x in range(x1, x2):
                    if grid_papel[y][x] != 'F':
                        pixels.append((x, y))
                        tokens.append(grid_papel[y][x])
            
            if len(pixels) < min_regiao:
                continue
            
            xs = [p[0] for p in pixels]
            ys = [p[1] for p in pixels]
            area = len(pixels)
            centroide = (sum(xs) / area, sum(ys) / area)
            bbox = (min(xs), min(ys), max(xs), max(ys))
            
            contagem = Counter(tokens)
            total = sum(contagem.values())
            proporcoes = {t: c/total for t, c in contagem.items()}
            
            prop_b = contagem.get('B', 0) / total
            prop_l = contagem.get('L', 0) / total
            
            regioes.append({
                'id': reg_id,
                'bbox': bbox,
                'centroide': centroide,
                'area': area,
                'pixels': pixels,
                'tokens': tokens,
                'proporcoes': proporcoes,
                'prop_b': prop_b,
                'prop_l': prop_l,
                'largura': bbox[2] - bbox[0] + 1,
                'altura': bbox[3] - bbox[1] + 1,
            })
            reg_id += 1
    
    return regioes


def fingerprint_regiao(reg: Dict) -> str:
    """Gera fingerprint compacto de uma região para clusterização.
    
    Formato: "B{prop_b:.1f}_L{prop_l:.1f}_W{largura}_H{altura}_A{area}"
    """
    return (
        f"B{reg['prop_b']:.2f}"
        f"_L{reg['prop_l']:.2f}"
        f"_W{reg['largura']}"
        f"_H{reg['altura']}"
        f"_A{reg['area']}"
    )


def comparar_regioes(r1: Dict, r2: Dict) -> float:
    """Compara duas regiões. Retorna score de similaridade (0-1)."""
    # Comparar proporções de token
    d_prop = abs(r1['prop_b'] - r2['prop_b'])
    
    # Comparar proporção de dimsão
    d_larg = abs(r1['largura'] - r2['largura']) / max(r1['largura'], r2['largura'], 1)
    d_alt = abs(r1['altura'] - r2['altura']) / max(r1['altura'], r2['altura'], 1)
    
    # Comparar proporção de área
    d_area = abs(r1['area'] - r2['area']) / max(r1['area'], r2['area'], 1)
    
    # Score: 1 = idêntica, 0 = totalmente diferente
    score = 1.0 - (d_prop * 0.4 + d_larg * 0.2 + d_alt * 0.2 + d_area * 0.2)
    return max(0.0, min(1.0, score))


def alinhar_regioes(listas_regioes: List[List[Dict]]) -> List[List[Dict]]:
    """Alinha regiões de múltiplos sprites por similaridade.
    
    Para cada sprite, ordena regiões por posição (y, x) e proporção B.
    Isso garante que regiões correspondentes ficam na mesma posição da lista.
    """
    resultado = []
    for regioes in listas_regioes:
        # Ordenar por: proporção B (desc), depois centroide y (asc), depois x (asc)
        ordenadas = sorted(regioes, key=lambda r: (
            -r['prop_b'],
            r['centroide'][1],
            r['centroide'][0],
        ))
        resultado.append(ordenadas)
    return resultado


def resumir_regioes(regioes: List[Dict]) -> str:
    """Resumo textual das regiões."""
    if not regioes:
        return "0 regioes"
    total_area = sum(r['area'] for r in regioes)
    papeis = Counter()
    for r in regioes:
        for t, c in r['proporcoes'].items():
            papeis[t] += c * r['area']
    partes = [f"{t}:{p:.0%}" for t, p in sorted(papeis.items())]
    return f"{len(regioes)}reg({total_area}px, {', '.join(partes)})"


# ─── Segmentação Cromática (nova abordagem) ──────────────────

def _flood_fill_cluster(mask: np.ndarray, sx: int, sy: int, 
                         largura: int, altura: int, label: int) -> List[Tuple[int, int]]:
    """BFS flood fill em máscara binária. Retorna pixels do componente conexo."""
    stack = [(sx, sy)]
    pixels = []
    while stack:
        x, y = stack.pop()
        if x < 0 or x >= largura or y < 0 or y >= altura:
            continue
        if mask[y, x] != label:
            continue
        mask[y, x] = -1  # marcar como visitado
        pixels.append((x, y))
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            stack.append((x + dx, y + dy))
    return pixels


def _cor_media(pixels_rgb: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
    """Cor média RGB de uma lista de pixels."""
    if not pixels_rgb:
        return (0, 0, 0)
    r = sum(int(p[0]) for p in pixels_rgb) // len(pixels_rgb)
    g = sum(int(p[1]) for p in pixels_rgb) // len(pixels_rgb)
    b = sum(int(p[2]) for p in pixels_rgb) // len(pixels_rgb)
    return (r, g, b)


def extrair_regioes_cromaticas(
    grid_cor: List[List[tuple]],
    grid_papel: List[List[str]] = None,
    limiar_cluster: float = None,
    area_minima: int = 10,
) -> List[Dict]:
    """Extrai regiões anatômicas por clustering CIELAB + flood fill.
    
    Algoritmo:
    1. Coletar pixels opacos (não-magenta)
    2. Calcular limiar de clusterização (auto ou manual)
    3. Clusterizar por picos de densidade no espaço Lab*
    4. Para cada cluster: flood fill → componentes conexos
    5. Filtrar por área mínima
    6. Extrair propriedades geométricas e cromáticas
    
    Args:
        grid_cor: grid 2D de cores RGB (altura × largura)
        grid_papel: grid 2D de papéis F/B/L (opcional)
        limiar_cluster: limiar ΔE (None = auto-calibrar)
        area_minima: pixels mínimos por região (filtro anti-ruído)
    
    Returns:
        lista de regiões, cada uma com:
          id, cluster_id, bbox, centroide, area,
          cor_media_rgb, cor_media_lab, excentricidade,
          prop_b, prop_l (se grid_papel fornecido)
    """
    altura = len(grid_cor)
    largura = len(grid_cor[0]) if altura else 0
    if altura == 0 or largura == 0:
        return []
    
    MAGENTA = (255, 0, 255)
    
    # 1. Coletar pixels opacos
    pixels_rgb = []
    posicoes = []
    for y in range(altura):
        for x in range(largura):
            r, g, b = grid_cor[y][x]
            if (r, g, b) != MAGENTA:
                pixels_rgb.append((r, g, b))
                posicoes.append((x, y))
    
    if not pixels_rgb:
        return []
    
    # 2-3. Clusterizar
    resultado = clusterizar_por_picos(pixels_rgb, limiar=limiar_cluster)
    labels = resultado['labels']
    centroides = resultado['centroides']
    limiar_usado = resultado['limiar']
    
    # 4. Para cada cluster, encontrar componentes conexos
    regioes = []
    
    # Criar máscara de cluster (altura × largura, -1 = fundo)
    mask_cluster = np.full((altura, largura), -1, dtype=np.int32)
    for idx, (x, y) in enumerate(posicoes):
        mask_cluster[y, x] = labels[idx]
    
    # Para cada cluster, extrair componentes conexos
    for cid in sorted(set(labels)):
        # Máscara binária deste cluster
        mask_bin = (mask_cluster == cid).astype(np.int32)
        
        # Encontrar componentes conexos via flood fill
        for sy in range(altura):
            for sx in range(largura):
                if mask_bin[sy, sx] != 1:
                    continue
                
                # Flood fill neste componente
                pixels_comp = _flood_fill_cluster(mask_bin, sx, sx, largura, altura, 1)
                
                if len(pixels_comp) < area_minima:
                    continue
                
                # 5. Extrair propriedades
                xs = [p[0] for p in pixels_comp]
                ys = [p[1] for p in pixels_comp]
                area = len(pixels_comp)
                centroide = (sum(xs) / area, sum(ys) / area)
                bbox = (min(xs), min(ys), max(xs), max(ys))
                
                # Cor média
                cores_comp = [grid_cor[y][x] for x, y in pixels_comp]
                cor_media = _cor_media(cores_comp)
                cor_media_lab = rgb_para_lab(*cor_media)
                
                # Excentricidade
                w = bbox[2] - bbox[0] + 1
                h = bbox[3] - bbox[1] + 1
                excentricidade = max(w, h) / max(min(w, h), 1)
                
                # Proporções de papel (se fornecido)
                prop_b = 0.0
                prop_l = 0.0
                if grid_papel:
                    papeis = [grid_papel[y][x] for x, y in pixels_comp]
                    n = len(papeis)
                    if n > 0:
                        prop_b = sum(1 for p in papeis if p == 'B') / n
                        prop_l = sum(1 for p in papeis if p == 'L') / n
                
                regioes.append({
                    'id': len(regioes),
                    'cluster_id': cid,
                    'bbox': bbox,
                    'centroide': centroide,
                    'area': area,
                    'cor_media_rgb': cor_media,
                    'cor_media_lab': cor_media_lab,
                    'excentricidade': excentricidade,
                    'prop_b': prop_b,
                    'prop_l': prop_l,
                    'largura': w,
                    'altura': h,
                    'pixels': pixels_comp,
                })
    
    return regioes


def fingerprint_cromatico(reg: Dict) -> str:
    """Fingerprint de região cromática para comparação.
    
    Formato: "C{cluster}_L{lab[0]:.0f}_a{lab[1]:.0f}_b{lab[2]:.0f}_W{w}_H{h}_A{area}"
    """
    lab = reg['cor_media_lab']
    return (
        f"C{reg['cluster_id']}"
        f"_L{lab[0]:.0f}"
        f"_a{lab[1]:.0f}"
        f"_b{lab[2]:.0f}"
        f"_W{reg['largura']}"
        f"_H{reg['altura']}"
        f"_A{reg['area']}"
    )


def comparar_regioes_cromaticas(r1: Dict, r2: Dict) -> float:
    """Compara duas regiões cromáticas. Score 0-1 (1 = idêntica)."""
    # Distância de cor (normalizada)
    d_cor = delta_e76(r1['cor_media_lab'], r2['cor_media_lab']) / 100.0
    
    # Diferença de área (normalizada)
    d_area = abs(r1['area'] - r2['area']) / max(r1['area'], r2['area'], 1)
    
    # Diferença de excentricidade (normalizada)
    d_excc = abs(r1['excentricidade'] - r2['excentricidade']) / max(r1['excentricidade'], r2['excentricidade'], 1)
    
    # Score: 1 = idêntica, 0 = totalmente diferente
    score = 1.0 - (d_cor * 0.5 + d_area * 0.3 + d_excc * 0.2)
    return max(0.0, min(1.0, score))
