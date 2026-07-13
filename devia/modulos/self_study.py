"""modulos.self_study — Redireciona para mcr.auto_curiosidade."""
try:
    from mcr.auto_curiosidade import AutoCuriosidade as SelfStudyEngine
except ImportError:
    class SelfStudyEngine:
        def __init__(self, *a, **kw): pass
        def escanear(self, *a, **kw): return {}
