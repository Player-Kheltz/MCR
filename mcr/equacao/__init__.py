"""equacao — Equação MCR. Fonte da verdade do sistema.

Define como o MCR avalia conexões, pontes e similaridades.
Parâmetros calibrados por evolução.
"""
from .equacao_mcr import (
    get_eq, calcular_ponte, classificar_tipo_ponte,
    get_penalidade, get_formula, aplicar_formula,
)
