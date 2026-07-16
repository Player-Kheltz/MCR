"""Stub — TaskPlanner, PlanValidator."""
class TaskPlanner:
    def __init__(self, tools_orchestrator=None, ia=None, **kw): pass
    def planejar(self, *a, **kw): return []

class PlanValidator:
    @staticmethod
    def validar(*a, **kw): return {"valido": True, "erros": []}
