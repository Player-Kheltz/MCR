"""modulos.lua_validator — Redireciona para mcr.lua_validator."""
try:
    from mcr.lua_validator import LuaValidator
except ImportError:
    class LuaValidator:
        def __init__(self, *a, **kw): pass
        def validar(self, *a, **kw): return {'valido': False, 'erros': ['modulo indisponivel']}
