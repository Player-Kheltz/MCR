"""modulos.kg — Redireciona para mcr.pattern_miner."""
try:
    from mcr.pattern_miner import KnowledgeGraph
except ImportError:
    class KnowledgeGraph:
        def __init__(self, *a, **kw): pass
        def consultar(self, *a, **kw): return []
