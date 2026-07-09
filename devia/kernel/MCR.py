#!/usr/bin/env python3
"""MCR — Thin wrapper para compatibilidade retroativa.

Todas as classes agora vivem no pacote mcr_kernel/.
Este arquivo apenas re-exporta tudo para manter compatibilidade
com imports existentes: from MCR import MCR, MCRSystem, ...
"""
import os, sys

# Garante que o diretorio pai esta no path para imports relativos
_base = os.path.abspath(os.path.dirname(__file__))
if _base not in sys.path:
    sys.path.insert(0, _base)

from mcr_kernel import *

# Re-exporta simbolos adicionais para compatibilidade
from mcr_kernel import (
    _MCR_DATA, _MCR_STATE, _get_kg, _autotestar,
    MCR_COMPLETO, MarkovUniversal,
    _MCR_THRESHOLD_FILTRO, _MCR_THRESHOLD_CONF,
    _MCR_THRESHOLD_TAMANHO, _MCR_THRESHOLD_REPETICAO,
    _MCR_THRESHOLD_PALAVRA, _MCR_THRESHOLD_CONEXAO,
    _MCR_THRESHOLD_NOTA, _MCR_SELF_CHECK,
)


if __name__ == '__main__':
    _base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if _base not in sys.path:
        sys.path.insert(0, _base)
    try:
        _autotestar()
    except Exception as _ate:
        print(f'[MCR AutoTest] Aviso: {_ate}')
