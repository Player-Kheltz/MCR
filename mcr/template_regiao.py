"""
mcr.template_regiao — Ponte entre template_entropico e tokenizador_hierarquico.

Conecta os 2 sistemas:
  - template_entropico: decide fixed vs gap por posicao (entropia de Shannon)
  - tokenizador_hierarquico: extrai N1 (regioes) e N2 (relacoes espaciais)

Fluxo de treino:
  1. Para N sprites da mesma categoria, extrair N1+N2
  2. Ordenar regioes consistentemente (por papel, y, x)
  3. Construir template entropico nas propriedades de N1 e N2
  4. Calcular limiar automatico (detectar_picos) ou fallback 0.5

Fluxo de geracao:
  1. Usar sprite de referencia para obter convex hulls base
  2. Para cada regiao: template decide fixed ou gap
  3. Fixed = mantem hull exato; Gap = transforma hull (translacao, escala, rotacao)
  4. Renderizar via regioes_para_grid_com_borda
"""
import math
import random
import numpy as np
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional

from mcr.template_entropico import (
    entropia_shannon,
    extrair_template_entropico,
    gerar_do_template,
    resumir_template,
)
from mcr.tokenizador_hierarquico import (
    extrair_regioes,
    extrair_relacoes,
    ordenar_regioes,
    propriedades_para_vetor,
    _convex_hull,
    _rasterizar_hull,
    _svd_orientacao,
    _bbox_dilatada,
    _bboxes_tocam,
)
from mcr.cielab import detectar_picos


# ─── Temperatura por posicao (Decision #7) ────────────────────


def temperatura_por_posicao(entropias_posicao: List[float]) -> List[float]:
    """Deriva temperatura por posicao do template a partir da entropia real.

    Regra (aprovada por 2 arquitetos):
    - H < 0.2:  temperatura 0.1 (posicao estrutural — quase fixed)
    - 0.2 <= H < 0.5: temperatura 0.5 (variacao moderada)
    - H >= 0.5:  temperatura 0.8 (variacao criativa)

    Args:
        entropias_posicao: lista de entropia de Shannon por posicao do template

    Returns:
        Lista de temperaturas, uma por posicao
    """
    temperaturas = []
    for h in entropias_posicao:
        if h < 0.2:
            temperaturas.append(0.1)
        elif h < 0.5:
            temperaturas.append(0.6)
        else:
            temperaturas.append(1.0)
    return temperaturas


def classificar_posicoes(
    template_n1: Dict,
    limiar_fixed: float = 0.2,
    limiar_criativo: float = 0.5,
) -> Dict[int, str]:
    """Classifica cada posicao do template em: fixed, moderado, criativo.

    Usa MEDIA da entropia das propriedades (nao max) para classificar.
    Se maioria das propriedades sao fixed, a posicao e fixed.

    Returns:
        dict {posicao: 'fixed'|'moderado'|'criativo'}
    """
    classificacao = {}
    for pos, props in template_n1.items():
        entropias = []
        for prop_info in props.values():
            if isinstance(prop_info, dict) and 'h' in prop_info:
                entropias.append(prop_info['h'])
        
        if not entropias:
            classificacao[pos] = 'fixed'
            continue
        
        # Usar media, nao max — posicao com maioria de props fixed = fixed
        h_media = sum(entropias) / len(entropias)
        
        if h_media < limiar_fixed:
            classificacao[pos] = 'fixed'
        elif h_media < limiar_criativo:
            classificacao[pos] = 'moderado'
        else:
            classificacao[pos] = 'criativo'
    return classificacao


# ─── Clusterizacao por arquetipo (Caminho D) ─────────────────


def clusterizar_por_arquetipo(
    sprites_grids: List[List[List[str]]],
    threshold_jaccard: float = None,
    min_cluster_size: int = 3,
) -> List[List[int]]:
    """Clusteriza sprites por similaridade de silhueta.

    Algoritmo: clustering aglomerativo via componentes conexos.
    1. Calcular matriz Jaccard entre todos os pares de sprites
    2. Dois sprites sao "vizinhos" se Jaccard >= threshold
    3. Componentes conexos = clusters
    4. Clusters com < min_cluster_size sprites sao descartados

    Se threshold_jaccard e None, calcula automaticamente:
    - Usa mediana dos Jaccard pares como threshold base
    - Se mediana > 0.6, usa mediana (corpus similar)
    - Se mediana <= 0.6, usa 0.75 (corpus variado, threshold mais alto)

    Args:
        sprites_grids: lista de grids B/L/F
        threshold_jaccard: threshold ou None para auto
        min_cluster_size: tamanho minimo do cluster (default 3)

    Returns:
        Lista de clusters, cada cluster e lista de indices dos sprites
    """
    from itertools import combinations

    n = len(sprites_grids)
    if n < 2:
        return [[i] for i in range(n)]

    # Converter para mascaras binarias
    def _para_mascara(grid):
        h = len(grid)
        w = len(grid[0]) if h else 0
        mask = np.zeros((h, w), dtype=bool)
        for y in range(h):
            for x in range(w):
                mask[y, x] = grid[y][x] != 'F'
        return mask

    mascaras = [_para_mascara(g) for g in sprites_grids]

    # Calcular matriz de Jaccard completa
    jaccard_pairs = []
    for i, j in combinations(range(n), 2):
        inter = np.sum(mascaras[i] & mascaras[j])
        uni = np.sum(mascaras[i] | mascaras[j])
        jaccard_val = inter / uni if uni > 0 else 0.0
        jaccard_pairs.append((i, j, jaccard_val))

    # Auto-threshold se nao especificado
    if threshold_jaccard is None:
        vals = [v for _, _, v in jaccard_pairs]
        mediana = sorted(vals)[len(vals) // 2] if vals else 0.5
        if mediana > 0.6:
            threshold_jaccard = mediana
        else:
            threshold_jaccard = 0.75

    # Construir adjacencia
    adj = defaultdict(set)
    for i, j, jaccard_val in jaccard_pairs:
        if jaccard_val >= threshold_jaccard:
            adj[i].add(j)
            adj[j].add(i)

    # BFS para encontrar componentes conexos
    visitado = set()
    clusters = []
    for i in range(n):
        if i in visitado:
            continue
        cluster = []
        fila = [i]
        while fila:
            no = fila.pop(0)
            if no in visitado:
                continue
            visitado.add(no)
            cluster.append(no)
            for vizinho in adj[no]:
                if vizinho not in visitado:
                    fila.append(vizinho)
        clusters.append(sorted(cluster))

    # Filtrar clusters pequenos
    clusters = [c for c in clusters if len(c) >= min_cluster_size]

    return clusters


def treinar_templates_por_arquetipo(
    sprites_grids: List[List[List[str]]],
    clusters: List[List[int]],
) -> List[Dict]:
    """Treina um template por arquétipo.

    Args:
        sprites_grids: lista completa de grids
        clusters: output de clusterizar_por_arquetipo()

    Returns:
        Lista de templates, um por cluster.
    """
    templates = []
    for cluster in clusters:
        grids_cluster = [sprites_grids[i] for i in cluster]
        template = treinar_templates(grids_cluster)
        templates.append(template)
    return templates


def gerar_sprite_por_arquetipo(
    templates: List[Dict],
    clusters: List[List[int]],
    total_gerados: int = 20,
    **kwargs,
) -> List[Tuple[List[List[str]], Dict]]:
    """Gera sprites distribuidos proporcionalmente entre arquetipos.

    Cada arquétipo gera sprites proporcionalmente ao tamanho do cluster.

    Args:
        templates: lista de templates (um por cluster)
        clusters: lista de clusters (output de clusterizar_por_arquetipo())
        total_gerados: total de sprites a gerar
        **kwargs: argumentos para gerar_sprite() (temperatura, angulo_hue, etc.)

    Returns:
        Lista de (grid_papel, info)
    """
    if not templates or not clusters:
        return []

    # Calcular pesos proporcionais ao tamanho do cluster
    tamanhos = [len(c) for c in clusters]
    total_treino = sum(tamanhos)
    pesos = [t / total_treino for t in tamanhos]

    # Distribuir sprites por arquétipo
    sprites_por_cluster = []
    for i, (peso, template) in enumerate(zip(pesos, templates)):
        n = max(1, round(peso * total_gerados))
        sprites_por_cluster.append((template, n))

    # Ajustar para bater total_gerados
    soma = sum(n for _, n in sprites_por_cluster)
    while soma > total_gerados and sprites_por_cluster:
        # Remover do cluster com menor prioridade
        idx_min = min(range(len(sprites_por_cluster)), key=lambda i: pesos[i])
        if sprites_por_cluster[idx_min][1] > 1:
            sprites_por_cluster[idx_min] = (sprites_por_cluster[idx_min][0], sprites_por_cluster[idx_min][1] - 1)
            soma -= 1
        else:
            break

    # Gerar
    resultado = []
    for template, n in sprites_por_cluster:
        for _ in range(n):
            grid, info = gerar_sprite(template, **kwargs)
            resultado.append((grid, info))

    return resultado


# ─── Limiar automatico com fallback ────────────────────────────


def _calcular_limiar_automatico(
    sprites_grids: List[List[List[str]]],
    n_amostra: int = 500,
) -> float:
    """Calcula limiar de entropia via detectar_picos no histograma de entropias.
    
    Decisao de Design #1: auto via detectar_picos, fallback 0.5 se:
    - <30 amostras na categoria
    - detectar_picos retorna 0 picos (histograma plano) ou >4 picos (ruido)
    
    Returns:
        limiar de entropia (float)
    """
    if len(sprites_grids) < 30:
        return 0.5
    
    # Coletar entropias por posicao (N1: propriedades das regioes)
    todas_entropias = []
    for grid in sprites_grids:
        regioes = extrair_regioes(grid)
        if not regioes:
            continue
        props = propriedades_para_vetor(regioes)
        for prop_name, valores in props.items():
            if prop_name == 'papel':
                continue
            # Converter para tokens string para calcular entropia
            tokens = [str(round(v, 1)) for v in valores]
            if len(tokens) >= 2:
                h = entropia_shannon(tokens)
                todas_entropias.append(h)
    
    if not todas_entropias:
        return 0.5
    
    # Construir histograma e detectar picos
    import numpy as np
    arr = np.array(todas_entropias)
    hist, bordas = np.histogram(arr, bins=20, range=(0, 1.0))
    picos = detectar_picos(list(hist), len(hist))
    
    if len(picos) == 0 or len(picos) > 4:
        return 0.5
    
    # Usar o pico mais baixo como limiar (separar fixed de gap)
    limiar_idx = picos[0]
    limiar = float(bordas[limiar_idx])
    return max(0.2, min(0.8, limiar))


# ─── Treino: extrair templates de N sprites ────────────────────


def treinar_templates(
    sprites_grids: List[List[List[str]]],
    limiar: float = None,
) -> Dict:
    """Constrói templates entropicos para N1 e N2 a partir de N sprites.
    
    Args:
        sprites_grids: lista de grids B/L/F (2D) de sprites da mesma categoria
        limiar: limiar de entropia (None = auto-calibrar)
    
    Returns:
        dict com:
          - 'limiar': float
          - 'n_sprites': int
          - 'template_n1': template entropico das propriedades N1
          - 'template_n2': template entropico das propriedades N2
          - 'regioes_referencia': regioes do sprite de referencia (mediana de opacos)
          - 'n_regioes_media': float
          - 'n_regioes_dp': float
    """
    if not sprites_grids:
        return {}
    
    # Calcular limiar
    if limiar is None:
        limiar = _calcular_limiar_automatico(sprites_grids)
    
    # Extrair N1+N2 de cada sprite
    todos_n1 = []
    todos_n2 = []
    opacos_por_sprite = []
    
    for grid in sprites_grids:
        opacos = sum(1 for row in grid for t in row if t != 'F')
        opacos_por_sprite.append(opacos)
        regioes = extrair_regioes(grid)
        regioes_ordenadas = ordenar_regioes(regioes)
        relacoes = extrair_relacoes(regioes_ordenadas)
        todos_n1.append(regioes_ordenadas)
        todos_n2.append(relacoes)
    
    # Escolher sprite de referencia = mediana de opacos
    idx_sorted = sorted(range(len(opacos_por_sprite)), key=lambda i: opacos_por_sprite[i])
    idx_ref = idx_sorted[len(idx_sorted) // 2]
    regioes_ref = todos_n1[idx_ref]
    
    # Alinhar numero de regioes: todos devem ter o mesmo count
    # Usar o numero mediano de regioes
    contagens = [len(n1) for n1 in todos_n1]
    contagens_sorted = sorted(contagens)
    n_regioes_alvo = contagens_sorted[len(contagens_sorted) // 2]
    
    # Filtrar sprites com numero de regioes proximo ao alvo (±2)
    indices_validos = [i for i, c in enumerate(contagens) 
                       if abs(c - n_regioes_alvo) <= 2]
    
    if len(indices_validos) < 10:
        # Se poucos validos, usar todos e truncar/padronizar
        indices_validos = list(range(len(todos_n1)))
    
    # Construir vetores de propriedades para template
    # N1: propriedades por regiao (area, centroide_x, centroide_y, orientacao, bbox_w, bbox_h)
    props_n1_por_posicao = defaultdict(lambda: defaultdict(list))
    
    for i in indices_validos:
        regioes = todos_n1[i][:n_regioes_alvo]  # truncar
        for pos, reg in enumerate(regioes):
            props_n1_por_posicao[pos]['area'].append(reg['area'])
            props_n1_por_posicao[pos]['centroide_x'].append(reg['centroide'][0])
            props_n1_por_posicao[pos]['centroide_y'].append(reg['centroide'][1])
            props_n1_por_posicao[pos]['orientacao'].append(reg['orientacao'])
            props_n1_por_posicao[pos]['bbox_w'].append(reg['bbox'][2] - reg['bbox'][0] + 1)
            props_n1_por_posicao[pos]['bbox_h'].append(reg['bbox'][3] - reg['bbox'][1] + 1)
    
    # Construir template N1: propriedades por posicao
    # Decisao #7: classificar por entropia por posicao (nao global limiar)
    template_n1 = {}
    entropias_por_posicao = {}
    for pos in range(n_regioes_alvo):
        template_n1[pos] = {}
        entropias_pos = []
        for prop_name in ['area', 'centroide_x', 'centroide_y', 'orientacao', 'bbox_w', 'bbox_h']:
            valores = props_n1_por_posicao[pos].get(prop_name, [])
            if not valores:
                template_n1[pos][prop_name] = {'tipo': 'fixo', 'valor': 0, 'h': 0}
                continue
            
            tokens = [str(round(v, 1)) for v in valores]
            h = entropia_shannon(tokens)
            entropias_pos.append(h)
            
            # Decisao #7: H < 0.2 = fixed, senao gap (mais flexivel que antes)
            if h < 0.2:
                valores_sorted = sorted(valores)
                mediana = valores_sorted[len(valores_sorted) // 2]
                template_n1[pos][prop_name] = {'tipo': 'fixo', 'valor': mediana, 'h': h}
            else:
                template_n1[pos][prop_name] = {'tipo': 'gap', 'distribuicao': Counter(tokens), 'h': h}
        
        entropias_por_posicao[pos] = max(entropias_pos) if entropias_pos else 0.0
    
    # Calcular temperaturas por posicao
    temperaturas_pos = temperatura_por_posicao([entropias_por_posicao[pos] for pos in range(n_regioes_alvo)])
    
    # Classificar posicoes
    classificacao = classificar_posicoes(template_n1, limiar_fixed=0.2, limiar_criativo=0.5)
    
    # Construir template N2: relacoes entre pares de regioes
    props_n2_por_par = defaultdict(lambda: defaultdict(list))
    
    for i in indices_validos:
        regioes = todos_n1[i][:n_regioes_alvo]
        # Gerar relacoes manualmente (pares adjacentes)
        for a in range(len(regioes)):
            for b in range(a + 1, min(a + 3, len(regioes))):  # max 2 vizinhos por regiao
                par_key = (a, b)
                ra, rb = regioes[a], regioes[b]
                delta_cx = rb['centroide'][0] - ra['centroide'][0]
                delta_cy = rb['centroide'][1] - ra['centroide'][1]
                delta_area = rb['area'] / max(ra['area'], 1)
                
                props_n2_por_par[par_key]['delta_cx'].append(delta_cx)
                props_n2_por_par[par_key]['delta_cy'].append(delta_cy)
                props_n2_por_par[par_key]['delta_area'].append(delta_area)
    
    template_n2 = {}
    for par, props in props_n2_por_par.items():
        template_n2[par] = {}
        for prop_name, valores in props.items():
            tokens = [str(round(v, 1)) for v in valores]
            h = entropia_shannon(tokens)
            
            # N2 sempre usa gap se H >= 0.2 (relacoes sao mais criativas)
            if h < 0.2:
                valores_sorted = sorted(valores)
                mediana = valores_sorted[len(valores_sorted) // 2]
                template_n2[par][prop_name] = {'tipo': 'fixo', 'valor': mediana, 'h': h}
            else:
                template_n2[par][prop_name] = {'tipo': 'gap', 'distribuicao': Counter(tokens), 'h': h}
    
    # Estatisticas
    n_regioes_vals = [len(n1) for n1 in todos_n1]
    media_regioes = sum(n_regioes_vals) / len(n_regioes_vals)
    dp_regioes = (sum((x - media_regioes)**2 for x in n_regioes_vals) / len(n_regioes_vals)) ** 0.5
    
    # Contar fixed vs gap
    n1_fixed = sum(1 for pos in template_n1 for prop in template_n1[pos].values() if prop['tipo'] == 'fixo')
    n1_gap = sum(1 for pos in template_n1 for prop in template_n1[pos].values() if prop['tipo'] == 'gap')
    n2_fixed = sum(1 for par in template_n2 for prop in template_n2[par].values() if prop['tipo'] == 'fixo')
    n2_gap = sum(1 for par in template_n2 for prop in template_n2[par].values() if prop['tipo'] == 'gap')
    
    return {
        'limiar': limiar,
        'n_sprites': len(sprites_grids),
        'n_sprites_validos': len(indices_validos),
        'n_regioes_alvo': n_regioes_alvo,
        'n_regioes_media': round(media_regioes, 2),
        'n_regioes_dp': round(dp_regioes, 2),
        'template_n1': template_n1,
        'template_n2': template_n2,
        'regioes_referencia': regioes_ref,
        'n1_fixed': n1_fixed,
        'n1_gap': n1_gap,
        'n2_fixed': n2_fixed,
        'n2_gap': n2_gap,
        'temperaturas_pos': temperaturas_pos,
        'classificacao': classificacao,
        'entropias_por_posicao': entropias_por_posicao,
    }


# ─── Geracao: criar novos sprites a partir do template ────────


def _amostar_valor(prop_info: Dict, temperatura: float = 0.5) -> float:
    """Amostra um valor do template (fixed ou gap)."""
    if prop_info['tipo'] == 'fixo':
        return prop_info['valor']
    
    dist = prop_info['distribuicao']
    tokens = list(dist.keys())
    if not tokens:
        return 0
    
    total = sum(dist.values())
    pesos = [(dist[t] / total) ** (1.0 / max(temperatura, 0.01)) for t in tokens]
    total_peso = sum(pesos)
    if total_peso <= 0:
        return float(tokens[0])
    
    r = random.random() * total_peso
    acum = 0.0
    for token, peso in zip(tokens, pesos):
        acum += peso
        if r <= acum:
            return float(token)
    return float(tokens[-1])


def gerar_sprite(
    treino: Dict,
    temperatura_n1: float = 0.25,
    temperatura_n2: float = 0.6,
    angulo_hue: float = None,
    variacao_cor: int = 5,
    largura: int = 32,
    altura: int = 32,
) -> Tuple[List[List[str]], Dict]:
    """Gera um novo sprite a partir do template treinado.

    Decisao #7: usa temperatura POR POSICAO (nao global).
    Posicoes fixed (H < 0.2) usam temp 0.1, moderadas usam 0.5, criativas usam 0.8.

    Args:
        treino: dict retornado por treinar_templates()
        temperatura_n1: fallback se treino nao tem temperaturas_pos
        temperatura_n2: fallback para N2
        angulo_hue: angulo de rotacao CIELAB (None = aleatorio)
        variacao_cor: variacao de luminancia
        largura, altura: dimensoes do grid

    Returns:
        (grid_papel, info) onde grid_papel e list de listas B/L/F
    """
    if not treino or 'template_n1' not in treino:
        return [['F'] * largura for _ in range(altura)], {}

    template_n1 = treino['template_n1']
    template_n2 = treino['template_n2']
    regioes_ref = treino['regioes_referencia']
    temperaturas_pos = treino.get('temperaturas_pos', None)

    # Usar TODAS as regioes da referencia
    n_regioes = min(len(regioes_ref), len(template_n1))

    # Gerar novas propriedades para cada regiao com temperatura POR POSICAO
    novas_propriedades = []
    for pos in range(n_regioes):
        if pos not in template_n1:
            continue

        props = template_n1[pos]

        # Temperatura especifica desta posicao
        if temperaturas_pos and pos < len(temperaturas_pos):
            temp_pos = temperaturas_pos[pos]
        else:
            temp_pos = temperatura_n1

        nova_area = max(5, int(_amostar_valor(props.get('area', {'tipo': 'fixo', 'valor': 50, 'h': 0}), temp_pos)))
        novo_cx = _amostar_valor(props.get('centroide_x', {'tipo': 'fixo', 'valor': 16, 'h': 0}), temp_pos)
        novo_cy = _amostar_valor(props.get('centroide_y', {'tipo': 'fixo', 'valor': 16, 'h': 0}), temp_pos)
        nova_orientacao = _amostar_valor(props.get('orientacao', {'tipo': 'fixo', 'valor': -1, 'h': 0}), temp_pos)
        novo_bbox_w = max(3, int(_amostar_valor(props.get('bbox_w', {'tipo': 'fixo', 'valor': 10, 'h': 0}), temp_pos)))
        novo_bbox_h = max(3, int(_amostar_valor(props.get('bbox_h', {'tipo': 'fixo', 'valor': 10, 'h': 0}), temp_pos)))

        novas_propriedades.append({
            'area': nova_area,
            'centroide': (novo_cx, novo_cy),
            'orientacao': nova_orientacao,
            'bbox_w': novo_bbox_w,
            'bbox_h': novo_bbox_h,
        })
    
    # Gerar novas relacoes com temperatura N2
    novas_relacoes = {}
    for par, props in template_n2.items():
        a, b = par
        if a >= len(novas_propriedades) or b >= len(novas_propriedades):
            continue
        
        delta_cx = _amostar_valor(props.get('delta_cx', {'tipo': 'fixo', 'valor': 0, 'h': 0}), temperatura_n2)
        delta_cy = _amostar_valor(props.get('delta_cy', {'tipo': 'fixo', 'valor': 0, 'h': 0}), temperatura_n2)
        delta_area = _amostar_valor(props.get('delta_area', {'tipo': 'fixo', 'valor': 1.0, 'h': 0}), temperatura_n2)
        
        novas_relacoes[par] = {
            'delta_cx': delta_cx,
            'delta_cy': delta_cy,
            'delta_area': delta_area,
        }
    
    # Construir grid copiando pixels REAIS das regioes de referencia
    # com deslocamento amostrado do template (fixed = sem deslocamento, gap = deslocamento)
    grid = [['F'] * largura for _ in range(altura)]
    
    # Usar TODAS as regioes da referencia (nao so as que cabem no template)
    for pos in range(len(regioes_ref)):
        reg_ref = regioes_ref[pos]
        
        # Se tem template para esta posicao, usar propriedades amostradas
        if pos in template_n1:
            props_novas = novas_propriedades[pos] if pos < len(novas_propriedades) else None
        else:
            props_novas = None
        
        # Pixels REAIS da regiao
        pixels_ref = reg_ref['pixels']
        
        # Deslocamento: se tem propriedades novas, usar delta; senao, copiar direto
        if props_novas is not None:
            centro_ref = reg_ref['centroide']
            centro_novo = props_novas['centroide']
            dx = (centro_novo[0] - centro_ref[0]) * 0.8
            dy = (centro_novo[1] - centro_ref[1]) * 0.8
        else:
            dx = 0.0
            dy = 0.0
        
        # Copiar pixels com deslocamento
        for (px, py) in pixels_ref:
            nx = int(round(px + dx))
            ny = int(round(py + dy))
            if 0 <= nx < largura and 0 <= ny < altura:
                grid[ny][nx] = reg_ref['papel']
    
    # Aplicar borda (D) entre L e B adjacentes
    for y in range(altura):
        for x in range(largura):
            if grid[y][x] == 'L':
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < largura and 0 <= ny < altura:
                        if grid[ny][nx] == 'B':
                            grid[y][x] = 'D'
                            break
    
    info = {
        'n_regioes_geradas': len(novas_propriedades),
        'n1_fixed': treino.get('n1_fixed', 0),
        'n1_gap': treino.get('n1_gap', 0),
        'temperaturas_pos': temperaturas_pos if temperaturas_pos else [],
        'classificacao': treino.get('classificacao', {}),
    }
    
    return grid, info


# ─── Resumo ───────────────────────────────────────────────────


def resumir_treino(treino: Dict) -> str:
    """Resumo textual do treino."""
    if not treino:
        return "vazio"
    
    classificacao = treino.get('classificacao', {})
    n_fixed = sum(1 for v in classificacao.values() if v == 'fixed')
    n_moderado = sum(1 for v in classificacao.values() if v == 'moderado')
    n_criativo = sum(1 for v in classificacao.values() if v == 'criativo')
    
    partes = [
        f"limiar={treino.get('limiar', 0):.3f}",
        f"sprites={treino.get('n_sprites', 0)}",
        f"validos={treino.get('n_sprites_validos', 0)}",
        f"regAlvo={treino.get('n_regioes_alvo', 0)}",
        f"N1: {treino.get('n1_fixed', 0)}fixed + {treino.get('n1_gap', 0)}gap",
        f"N2: {treino.get('n2_fixed', 0)}fixed + {treino.get('n2_gap', 0)}gap",
        f"posicoes: {n_fixed}fixed/{n_moderado}mod/{n_criativo}cri",
    ]
    return ', '.join(partes)
