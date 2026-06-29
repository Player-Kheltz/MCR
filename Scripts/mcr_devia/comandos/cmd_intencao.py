"""Comando: intencao - ALIAS para perguntar (interpreta intencao)."""
def register():
    return {"name": "intencao", "desc": "ALIAS: interpreta intencao (usa perguntar internamente).",
            "handler": execute, "args": [{"name": "texto", "type": "str", "required": True}], "categoria": "comando"}
def execute(kg, ia, args, ctx_crew=None):
    from comandos.cmd_perguntar import execute as _perguntar
    return _perguntar(kg, ia, args, ctx_crew)
