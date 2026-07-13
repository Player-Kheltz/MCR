"""modulos.sse_server — Redireciona para mcr.sse_server."""
try:
    from mcr.sse_server import sse_emit as emit
except ImportError:
    def emit(evento, dados=None, *a, **kw):
        pass
