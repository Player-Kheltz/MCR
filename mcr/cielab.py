"""
mcr.cielab — Módulo compartilhado de colorimetria CIELAB.

Consolida as 5 funções duplicadas em 9 scripts raiz:
  - rgb_para_lab: conversão sRGB → CIELAB (D65)
  - lab_para_rgb: conversão CIELAB → sRGB (D65)
  - delta_e76: distância Euclidiana em CIELAB (CIE76)
  - clusterizar_lab: agrupamento greedy single-pass por limiar delta-E
  - detectar_picos: detecção de picos em histograma suavizado
  - limiar_automatico: calibração do limiar via histograma de distâncias
  - clusterizar_por_picos: clusterização por picos de densidade

Zero dependências externas — apenas math + numpy.
"""
import math
import random as _rnd
import numpy as np


# ─── Conversão sRGB ↔ CIELAB (D65) ─────────────────────────

def rgb_para_lab(r, g, b):
    """Converte sRGB (0-255) para CIELAB (L:0-100, a:-128~127, b:-128~127).
    
    Referência: D65 illuminant, gamut sRGB padrão.
    """
    def f(t): return t**(1/3) if t > 0.008856 else (7.787*t + 16/116)
    r_ = f((r/255+0.055)/1.055*100/95.047)
    g_ = f((g/255+0.055)/1.055*100/100.0)
    b_ = f((b/255+0.055)/1.055*100/108.883)
    return (116*g_-16, 500*(r_-g_), 200*(g_-b_))


def lab_para_rgb(L, a, b):
    """Converte CIELAB para sRGB (0-255). Valores são clampados ao gamut."""
    def f_inv(t): return t**3 if t > 0.008856 else (t-16/116)/7.787
    g_ = (L+16)/116; r_ = a/500 + g_; b_ = g_ - b/200
    return (max(0,min(255,int(round((1.055*(f_inv(r_)*95.047/100)-0.055)*255)))),
            max(0,min(255,int(round((1.055*(f_inv(g_)*100/100)-0.055)*255)))),
            max(0,min(255,int(round((1.055*(f_inv(b_)*108.883/100)-0.055)*255)))))


# ─── Métrica de distância ───────────────────────────────────

def delta_e76(c1, c2):
    """Distância Euclidiana em CIELAB (CIE76 delta-E).
    
    c1, c2: tuplas (L, a, b).
    Retorna: float ≥ 0 (0 = idênticas, >100 = muito diferentes).
    """
    return math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2)


# ─── Clustering ─────────────────────────────────────────────

def clusterizar_lab(cores_lab, limiar=20.0):
    """Agrupa cores CIELAB por proximidade (greedy single-pass).
    
    Para cada cor, calcula delta-E ao centroide de cada cluster existente.
    Se menor que limiar, adiciona ao cluster. Caso contrário, cria novo cluster.
    
    Args:
        cores_lab: lista de tuplas (L, a, b)
        limiar: distância máxima delta-E para agrupar (default 20.0)
    
    Returns:
        dict {cluster_id: [(L, a, b), ...]}
    """
    clusters = {}; cid = 0
    for cor in cores_lab:
        enc = False
        for cid_ex, memb in clusters.items():
            centro = (sum(m[0] for m in memb)/len(memb), sum(m[1] for m in memb)/len(memb), sum(m[2] for m in memb)/len(memb))
            if delta_e76(cor, centro) < limiar: memb.append(cor); enc = True; break
        if not enc: clusters[cid] = [cor]; cid += 1
    return clusters


# ─── Detecção de picos ──────────────────────────────────────

def detectar_picos(hist, bins):
    """Detecta picos em histograma suavizado (média móvel 3 pontos).
    
    Um pico é um ponto onde o valor suavizado é maior que os vizinhos
    e acima de 3% do máximo global.
    
    Args:
        hist: lista de contagens por bin
        bins: número de bins (deve ser == len(hist))
    
    Returns:
        lista de índices dos picos (ordenaados). Fallback: bin mais alto.
    """
    suave = []
    for i in range(bins):
        l = hist[i-1] if i > 0 else 0
        c = hist[i]; r = hist[i+1] if i < bins-1 else 0
        suave.append((l+c+r)/3.0)
    max_v = max(suave) if suave else 1
    lim = max_v * 0.03
    picos = []
    for i in range(1, bins-1):
        if suave[i] > suave[i-1] and suave[i] > suave[i+1] and suave[i] >= lim:
            picos.append(i)
    return sorted(picos) if picos else [sorted(range(bins), key=lambda i: hist[i], reverse=True)[0]]


# ─── Calibração automática ──────────────────────────────────

def limiar_automatico(pixels_rgb, n_amostra=500, bins=50):
    """Calcula limiar de clusterização a partir do histograma de distâncias ΔE.
    
    Amostra pares de pixels, calcula distâncias ΔE, e encontra o primeiro
    vale após o pico principal — fronteira natural intra-cluster vs inter-cluster.
    
    Args:
        pixels_rgb: lista de tuplas (r, g, b)
        n_amostra: máximo de pixels para amostrar (O(n²) pares)
        bins: número de bins no histograma
    
    Returns:
        limiar ΔE (float), com clamp de segurança [5, 30]
    """
    n = min(len(pixels_rgb), n_amostra)
    if n < 10:
        return 20.0
    
    amostra = _rnd.sample(pixels_rgb, n)
    labs = [rgb_para_lab(r, g, b) for r, g, b in amostra]
    
    distancias = []
    for i in range(n):
        for j in range(i + 1, min(i + 50, n)):  # limitar pares por pixel
            distancias.append(delta_e76(labs[i], labs[j]))
    
    if not distancias:
        return 20.0
    
    arr = np.array(distancias)
    hist, bordas = np.histogram(arr, bins=bins)
    
    # Encontrar picos
    picos_idx = detectar_picos(list(hist), bins)
    
    if len(picos_idx) < 1:
        return 20.0
    
    # Primeiro pico = cluster principal
    primeiro_pico = picos_idx[0]
    
    # Encontrar o primeiro vale após o primeiro pico
    vales = []
    for i in range(primeiro_pico + 1, len(hist) - 1):
        if hist[i] < hist[i - 1] and hist[i] < hist[i + 1]:
            vales.append(i)
    
    if vales:
        limiar = float(bordas[vales[0]])
        return max(5.0, min(30.0, limiar))
    
    return 20.0


def clusterizar_por_picos(pixels_rgb, limiar=None):
    """Clusterização por picos de densidade no espaço CIELAB.
    
    1. Se limiar não fornecido, calibrar automaticamente
    2. Usar clusterizar_lab (greedy single-pass) com limiar calibrado
    3. Retornar clusters com centróides e labels
    
    Args:
        pixels_rgb: lista de tuplas (r, g, b)
        limiar: limiar ΔE (None = auto-calibrar)
    
    Returns:
        dict {
            'clusters': {cluster_id: [(r,g,b), ...]},
            'centroides': {cluster_id: (L, a, b)},
            'labels': [cluster_id, ...]  (mesma ordem que pixels_rgb)
        }
    """
    if limiar is None:
        limiar = limiar_automatico(pixels_rgb)
    
    # Converter tudo para Lab
    labs = [rgb_para_lab(r, g, b) for r, g, b in pixels_rgb]
    
    # Clusterizar
    clusters_lab = clusterizar_lab(labs, limiar=limiar)
    
    # Mapear de volta para RGB e calcular centróides
    clusters_rgb = {}
    centroides = {}
    labels = []
    
    for cid, membros_lab in clusters_lab.items():
        # Encontrar os RGB correspondentes
        membros_rgb = []
        for i, lab in enumerate(labs):
            for m in membros_lab:
                if lab == m:  # tuplas são comparáveis
                    membros_rgb.append(pixels_rgb[i])
                    break
        clusters_rgb[cid] = membros_rgb
        
        # Centróide Lab
        n = len(membros_lab)
        centro = (
            sum(m[0] for m in membros_lab) / n,
            sum(m[1] for m in membros_lab) / n,
            sum(m[2] for m in membros_lab) / n,
        )
        centroides[cid] = centro
    
    # Gerar labels (mapear cada pixel ao cluster)
    for i, lab in enumerate(labs):
        label = -1
        for cid, membros_lab in clusters_lab.items():
            if lab in membros_lab:
                label = cid
                break
        labels.append(label if label >= 0 else 0)
    
    return {
        'clusters': clusters_rgb,
        'centroides': centroides,
        'labels': labels,
        'limiar': limiar,
    }
