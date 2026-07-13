#!/usr/bin/env python3
"""mcr.equacao_mcr — Fonte da verdade absoluta do sistema.
Contem a _EQUACAO_ATUAL original recuperada do git (commit de7bcb1d).
Esta equacao dita como o MCR avalia conexoes, pontes e similaridades."""
import copy

# ─── EQUACAO ATUAL — parametros calibrados por evolucao ──────
_EQUACAO_ATUAL = {
    'formula': '2*by + 1*pa',
    'peso_byte': 1,
    'peso_palavra': 13,
    'peso_token': 1,
    'penalidade_compartilhado': 0.0,
    'penalidade_parcial': 0.3,
    'penalidade_byte': 0.7,
    'penalidade_none': 0.9,
    'ponte_divergencia': 2,
    'ponte_especificidade': 3,
    'ponte_profundidade': 2,
    'threshold_conteudo': 0.6,
    'threshold_parcial': 0.3,
    'conf_min_base': 0.1,
    'passos_base': 6,
}

_FORMULAS_DISPONIVEIS = [
    'by + pa + tk',
    'by + pa + tk + h',
    '(by + pa + tk) / 3',
    'by * pa + tk',
    'pa + tk',
    'pa',
    'max(by, pa, tk)',
    'by + pa + tk + by*pa',
]

_PENALIDADES = {
    'conteudo_compartilhado': _EQUACAO_ATUAL['penalidade_compartilhado'],
    'conteudo_mas_parcial': _EQUACAO_ATUAL['penalidade_parcial'],
    'byte_only': _EQUACAO_ATUAL['penalidade_byte'],
    'none': _EQUACAO_ATUAL['penalidade_none'],
}


def get_eq() -> dict:
    """Retorna copia da equacao atual."""
    return copy.deepcopy(_EQUACAO_ATUAL)


def get_penalidade(tipo_ponte: str) -> float:
    """Retorna a penalidade para um tipo de ponte."""
    return _PENALIDADES.get(tipo_ponte, _EQUACAO_ATUAL['penalidade_none'])


def calcular_ponte(divergencia: float, especificidade: float, profundidade: float) -> float:
    """Calcula PONTE_OTIMA usando a equacao original.
    
    PONTE_OTIMA = (divergencia * w_div + especificidade * w_esp + profundidade * w_prof) / 10
    """
    w_div = _EQUACAO_ATUAL['ponte_divergencia']
    w_esp = _EQUACAO_ATUAL['ponte_especificidade']
    w_prof = _EQUACAO_ATUAL['ponte_profundidade']
    score = (divergencia * w_div + especificidade * w_esp + profundidade * w_prof) / 10.0
    return min(1.0, max(0.0, score))


def classificar_tipo_ponte(score: float, jaccard_bytes: float = 0.0) -> str:
    """Classifica o tipo de ponte baseado no score e similaridade."""
    if jaccard_bytes > 0.8:
        return 'conteudo_compartilhado'
    th_cont = _EQUACAO_ATUAL['threshold_conteudo']
    th_parc = _EQUACAO_ATUAL['threshold_parcial']
    if score >= th_cont:
        return 'conteudo_compartilhado'
    if score >= th_parc:
        return 'conteudo_mas_parcial'
    return 'byte_only'


def get_formula(formula_key: str = None) -> str:
    """Retorna a formula atual ou uma especifica."""
    if formula_key:
        return formula_key
    return _EQUACAO_ATUAL['formula']


def aplicar_formula(by: float, pa: float, tk: float, h: float = 0.0) -> float:
    """Aplica a formula atual para calcular a nota final."""
    formula = _EQUACAO_ATUAL['formula']
    try:
        return eval(formula, {'by': by, 'pa': pa, 'tk': tk, 'h': h})
    except Exception:
        return (by + pa + tk) / 3.0
