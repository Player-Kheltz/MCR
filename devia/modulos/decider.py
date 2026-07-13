"""modulos.decider — Redireciona para mcr.metacognicao."""
try:
    from mcr.metacognicao import Metacognicao as Decider
except ImportError:
    class Decider:
        def __init__(self, *a, **kw): pass
        def decidir(self, *a, **kw): return {'decisao': 'mcr', 'confianca': 0.5}
