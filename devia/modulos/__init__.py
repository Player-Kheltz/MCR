"""devia.modulos — Wrapper de retrocompatibilidade.

Redireciona imports antigos ('from modulos.X import Y') para
as implementacoes atuais em mcr/ e devia/kernel/.
"""
import sys as _sys
from pathlib import Path as _Path

_ROOT = str(_Path(__file__).resolve().parent.parent.parent)
_MCR = str(_Path(__file__).resolve().parent.parent / '..' / 'mcr')
_KERNEL = str(_Path(__file__).resolve().parent.parent / 'kernel')
_DEVIA = str(_Path(__file__).resolve().parent.parent)  # devia/

for p in (_ROOT, _MCR, _KERNEL, _DEVIA):
    if p not in _sys.path:
        _sys.path.insert(0, p)
