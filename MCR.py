"""MCR.py — Shim no root do projeto.

Redireciona imports antigos que faziam 'from MCR import *'
ou 'exec(MCR.py)' para o kernel real em devia/kernel/.
"""
import sys as _sys
from pathlib import Path as _Path

_ROOT = str(_Path(__file__).resolve().parent)
_KERNEL = str(_Path(__file__).resolve().parent / 'devia' / 'kernel')

if _ROOT not in _sys.path:
    _sys.path.insert(0, _ROOT)
if _KERNEL not in _sys.path:
    _sys.path.insert(0, _KERNEL)

try:
    from MCR_legacy import (
        MCR, MCRBridge, MCRByteUtils, MCRSignatureExpansiva,
        MCRJanelamentoFingerprint, MCRHDCOperation, MCRSuperposicao,
        MCREntropicSearch, MCRAutoEvolution, MCRThreshold, MCREntropia,
        MCRDecisorUniversal, MCRSerializador, MCRAcao, MCRNLP,
        MCRAttention, MCRWorld, MCRCoupling, MCREsfera,
        MCRHiperesferaAutoExpansiva, MCRAutoTopologia,
        MCRConfig,
    )
except ImportError:
    from mcr.engine import MCR, MCRBridge

try:
    from CerebroAGI import CerebroAGI
except ImportError:
    pass

def main():
    pass
