"""modulos.enricher — Redireciona para mcr.internal_monologue."""
try:
    from mcr.internal_monologue import InternalMonologue as Enricher
except ImportError:
    class Enricher:
        def __init__(self, *a, **kw): pass
        def enriquecer(self, *a, **kw): return ''
