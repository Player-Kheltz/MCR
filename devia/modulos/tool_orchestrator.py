"""modulos.tool_orchestrator — Redireciona para mcr.executor_map."""
try:
    from mcr.executor_map import get_registry
    class ToolOrchestrator:
        def __init__(self):
            self._reg = get_registry()
        def executar(self, token, **kwargs):
            return self._reg.executar(token, **kwargs) if hasattr(self._reg, 'executar') else None
except ImportError:
    class ToolOrchestrator:
        def __init__(self): pass
        def executar(self, *a, **kw): return None
