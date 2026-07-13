"""modulos.ia — Redireciona para mcr.ensemble_7b."""
try:
    from mcr.ensemble_7b import Ensemble7B as IA
except ImportError:
    class IA:
        def __init__(self, *a, **kw): pass
        def gerar(self, *a, **kw): return ''
