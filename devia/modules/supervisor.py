"""Stub de compatibilidade — Supervisor."""
class Supervisor:
    def __init__(self, **kw): pass
    def avaliar(self, *a, **kw): return {"status": "ok"}
    def revisar(self, *a, **kw): return {"valido": True}
