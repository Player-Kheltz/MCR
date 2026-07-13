"""modulos.emergir — Redireciona para mcr.emergir."""
try:
    from mcr.emergir import Emergir as EmergirEngine
except ImportError:
    class EmergirEngine:
        def __init__(self, *a, **kw): pass
        def ideias(self, *a, **kw): return []
