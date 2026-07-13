"""modulos.npc_generator — Redireciona para mcr.golden_templates."""
try:
    from mcr.golden_templates import gerar_npc_canary as NPCGenerator
except ImportError:
    class NPCGenerator:
        def __init__(self, *a, **kw): pass
        def gerar(self, *a, **kw): return ''
