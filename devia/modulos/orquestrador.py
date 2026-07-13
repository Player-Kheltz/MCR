"""modulos.orquestrador — Redireciona para mcr.adaptadores."""
try:
    from mcr.adaptadores import PipelineConectado as Orquestrador
except ImportError:
    class Orquestrador:
        def __init__(self, *a, **kw): pass
        def executar(self, *a, **kw): return {'status': 'modulo indisponivel'}

try:
    from mcr.adaptadores import _TEMPLATES
except ImportError:
    _TEMPLATES = {}
