#!/usr/bin/env python3
"""mcr.equacao_mcr — FONTE DA VERDADE do sistema MCR.

Sigmoide 5D: avalia toda execução do MCR.
Parâmetros mutáveis pela AutoEvolution.

5 dimensões ortogonais:
  - CERTEZA:     confiança da predição Markov (0-1)
  - COMPLETUDE:  checks estruturais passados / total (0-1)
  - INFORMACAO:  entropia Shannon normalizada da saída (0-1)
  - ESTABILIDADE: gaussiana da entropia do Markov (pune loops e caos)
  - EFICIENCIA:  1/log2(n_tools+1) (recompensa simplicidade)
"""
import math

# ─── EQUAÇÃO 5D — parâmetros mutáveis pela AutoEvolution ──────
EQUACAO_5D = {
    'pesos': {'certeza': 2, 'completude': 2, 'informacao': 2,
              'estabilidade': 2, 'eficiencia': 2},
    'theta': 2.0,
    'tau': 0.35,
    # Penalidades (classificação de falha)
    'penalidade_compartilhado': 0.0,
    'penalidade_parcial': 0.3,
    'penalidade_byte': 0.7,
    'penalidade_none': 0.9,
    # Thresholds de classificação de ponte
    'threshold_conteudo': 0.6,
    'threshold_parcial': 0.3,
    # Pesos da ponte (cálculo de similaridade)
    'ponte_divergencia': 2,
    'ponte_especificidade': 3,
    'ponte_profundidade': 2,
}

_PENALIDADES = {
    'conteudo_compartilhado': EQUACAO_5D['penalidade_compartilhado'],
    'conteudo_mas_parcial': EQUACAO_5D['penalidade_parcial'],
    'byte_only': EQUACAO_5D['penalidade_byte'],
    'none': EQUACAO_5D['penalidade_none'],
}


# ═══════════════════════════════════════════════════════════════
# AVALIAÇÃO PRINCIPAL — Sigmoide 5D
# ═══════════════════════════════════════════════════════════════

def avaliar_5d(certeza: float, completude: float, informacao: float,
               estabilidade: float, eficiencia: float,
               pesos: dict = None) -> float:
    """Avaliação principal do MCR — Sigmoide 5D.

    Calcula nota (0-1) a partir de 5 dimensões orgânicas.
    Abaixo de tau, nota ≈ 0 (ruído).
    pesos: opcional, para grid search testar candidatos.
    """
    w = pesos or EQUACAO_5D['pesos']
    theta = EQUACAO_5D['theta']
    tau = EQUACAO_5D['tau']

    dimensoes = {'certeza': certeza, 'completude': completude,
                 'informacao': informacao, 'estabilidade': estabilidade,
                 'eficiencia': eficiencia}

    soma = sum(w[k] * dimensoes[k] for k in dimensoes) / sum(w.values())

    nota = 1.0 / (1.0 + math.exp(-theta * (soma - tau)))
    return max(0.0, min(1.0, nota))


# ═══════════════════════════════════════════════════════════════
# CLASSIFICAÇÃO DE FALHA — Penalidades
# ═══════════════════════════════════════════════════════════════

def get_penalidade(tipo_ponte: str) -> float:
    """Retorna a penalidade para um tipo de ponte."""
    return _PENALIDADES.get(tipo_ponte, EQUACAO_5D['penalidade_none'])


def classificar_tipo_ponte(score: float, jaccard_bytes: float = 0.0) -> str:
    """Classifica o tipo de ponte baseado no score e similaridade."""
    if jaccard_bytes > 0.8:
        return 'conteudo_compartilhado'
    th_cont = EQUACAO_5D['threshold_conteudo']
    th_parc = EQUACAO_5D['threshold_parcial']
    if score >= th_cont:
        return 'conteudo_compartilhado'
    if score >= th_parc:
        return 'conteudo_mas_parcial'
    return 'byte_only'


# ═══════════════════════════════════════════════════════════════
# PONTE — Cálculo de similaridade
# ═══════════════════════════════════════════════════════════════

def calcular_ponte(divergencia: float, especificidade: float,
                   profundidade: float) -> float:
    """Calcula PONTE_OTIMA.
    
    PONTE_OTIMA = (div * w_div + esp * w_esp + prof * w_prof) / soma_pesos
    Normalizacao pela soma dos pesos (nao fixa /10) — adaptativo.
    """
    w_div = EQUACAO_5D['ponte_divergencia']
    w_esp = EQUACAO_5D['ponte_especificidade']
    w_prof = EQUACAO_5D['ponte_profundidade']
    soma_pesos = w_div + w_esp + w_prof
    score = (divergencia * w_div + especificidade * w_esp +
             profundidade * w_prof) / max(soma_pesos, 0.01)
    return min(1.0, max(0.0, score))


# ═══════════════════════════════════════════════════════════════
# HELPERS (compatibilidade)
# ═══════════════════════════════════════════════════════════════

def get_eq() -> dict:
    """Retorna cópia da equação atual (para serialização/auto-evolution)."""
    import copy
    return copy.deepcopy(EQUACAO_5D)
