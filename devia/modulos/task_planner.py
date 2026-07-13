"""modulos.task_planner — Redireciona para mcr.planejador."""
try:
    from mcr.planejador import Planejador as TaskPlanner
except ImportError:
    class TaskPlanner:
        def __init__(self, *a, **kw): pass
        def planejar(self, *a, **kw): return []


class PlanValidator:
    @staticmethod
    def validar(plano):
        if not plano:
            return {'valido': False, 'erro': 'plano vazio'}
        return {'valido': True, 'etapas': len(plano) if isinstance(plano, list) else 1}
