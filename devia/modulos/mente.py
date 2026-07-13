"""modulos.mente — Redireciona para mcr.mcr_mente_pura."""
try:
    from mcr.mcr_mente_pura import MentePura as mente_pura
except ImportError:
    class mente_pura:
        def __init__(self, *a, **kw): pass
        def pensar(self, *a, **kw): return {'resposta': ''}
