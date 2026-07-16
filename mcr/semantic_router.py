"""SemanticRouter — Similaridade semântica local (zero dependências).

Usa apenas:
  - Trigrama de caracteres (Jaccard, 80% da eficácia)
  - Fingerprint 8D (categorias de byte, complementar)

Sem Ollama. Sem GPU. Sem rede. Sem cache em disco.
MCR puro: 1 equação, zero dependências.
"""
import math
from typing import Dict, List, Optional, Tuple


def _ngramas(s: str, n: int) -> set:
    s = s.lower().strip()
    return {s[i:i+n] for i in range(max(len(s)-n+1, 0))}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _dice_coef(a: set, b: set) -> float:
    """Dice coefficient: 2*|intersecao| / (|a| + |b|).
    Melhor que Jaccard para strings curtas."""
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return 2.0 * inter / (len(a) + len(b))


def _edit_sim(a: str, b: str) -> float:
    """Similaridade por Levenshtein normalizada (rápida: limitada a 20 chars)."""
    a, b = a[:20].lower(), b[:20].lower()
    if a == b:
        return 1.0
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 0.0
    # Matrix 2 linhas (otimizado)
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        curr = [i] + [0] * lb
        for j in range(1, lb + 1):
            cost = 0 if a[i-1] == b[j-1] else 1
            curr[j] = min(curr[j-1] + 1, prev[j] + 1, prev[j-1] + cost)
        prev = curr
    dist = prev[lb]
    return 1.0 - (dist / max(la, lb))


def _fingerprint_8d(s: str) -> list:
    """Fingerprint 8D: distribuição de categorias de byte."""
    cats = [0]*8
    for c in s.encode('utf-8', errors='replace'):
        if 97 <= c <= 122: cats[0] += 1
        elif 65 <= c <= 90: cats[1] += 1
        elif 48 <= c <= 57: cats[2] += 1
        elif c == 32: cats[3] += 1
        elif c in b'.,;:!?()[]{}<>+-*/=@#$%^&_~`\'\"|\\': cats[4] += 1
        elif c < 65: cats[5] += 1
        elif c > 122: cats[6] += 1
        else: cats[7] += 1
    total = sum(cats) or 1
    return [c/total for c in cats]


def _cosseno(a: list, b: list) -> float:
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(x*x for x in b))
    return dot / (na * nb + 1e-10)


def similaridade(a: str, b: str) -> float:
    """Similaridade semântica local entre duas strings (0-1).
    
    4 métricas combinadas:
      - Trigrama Dice (35%): captura morfologia de 3 chars
      - Bigrama Dice (30%): captura morfologia de 2 chars (ex: sufixos "-ar", "-er")
      - Levenshtein (20%): captura edição de caracteres
      - Fingerprint 8D (15%): captura categoria estrutural
    
    Só combina se há overlap mínimo de bigrama (evita falsos positivos).
    """
    big_a, big_b = _ngramas(a, 2), _ngramas(b, 2)
    tri_a, tri_b = _ngramas(a, 3), _ngramas(b, 3)
    
    bi_score = _dice_coef(big_a, big_b)
    tri_score = _dice_coef(tri_a, tri_b)
    edit_score = _edit_sim(a, b)
    fp_score = _cosseno(_fingerprint_8d(a), _fingerprint_8d(b))
    
    if bi_score > 0.05 or tri_score > 0.05:
        return round(max(0.0, min(1.0,
            tri_score * 0.35 + bi_score * 0.30 + edit_score * 0.20 + fp_score * 0.15
        )), 4)
    else:
        # Sem overlap: penaliza fortemente, apenas edit + fp residual
        return round(max(0.0, min(1.0, edit_score * 0.10 + fp_score * 0.05)), 4)


def termo_mais_similar(termo: str, candidatos: List[str],
                       threshold: float = 0.3) -> Tuple[Optional[str], float]:
    """Encontra o termo mais similar em candidatos (puramente local).
    
    Args:
        termo: termo de busca
        candidatos: lista de termos conhecidos
        threshold: similaridade mínima (0-1)
    
    Returns:
        (melhor_candidato, score) ou (None, 0.0)
    """
    if not termo or not candidatos:
        return None, 0.0
    
    melhor = None
    melhor_score = 0.0
    
    # Match exato (case insensitive)
    termo_lower = termo.lower().strip()
    for c in candidatos:
        if c.lower().strip() == termo_lower:
            return c, 1.0
    
    # Substring match
    for c in candidatos:
        cl = c.lower()
        if termo_lower in cl or cl in termo_lower:
            ratio = max(len(termo_lower), len(cl)) / (min(len(termo_lower), len(cl)) + 1)
            score = min(1.0, 1.0 / ratio)
            if score > melhor_score:
                melhor_score = score
                melhor = c
    
    if melhor_score >= 0.8:
        return melhor, melhor_score
    
    # Similaridade estrutural (trigrama + fingerprint)
    for c in candidatos:
        score = similaridade(termo, c)
        if score > melhor_score:
            melhor_score = score
            melhor = c
    
    if melhor_score >= threshold:
        return melhor, melhor_score
    
    return None, 0.0


def palavras_similares(termo: str, candidatos: Dict[str, any],
                       threshold: float = 0.25, max_resultados: int = 5
                       ) -> List[Tuple[str, float]]:
    """Retorna palavras similares ordenadas por score.
    
    Args:
        termo: termo de busca
        candidatos: dict {palavra: qualquer_coisa}
        threshold: similaridade mínima
    
    Returns:
        [(palavra, score), ...] ordenado por score decrescente
    """
    if not termo or not candidatos:
        return []
    
    scores = []
    for palavra in candidatos:
        score = similaridade(termo, palavra)
        if score >= threshold:
            scores.append((palavra, score))
    
    scores.sort(key=lambda x: -x[1])
    return scores[:max_resultados]
