"""Comando: processar - ALIAS para perguntar (processa entrada)."""
def register():
    return {"name": "processar", "desc": "ALIAS: processa entrada (usa perguntar internamente).",
            "handler": execute, "args": [{"name": "texto", "type": "str", "required": True}], "categoria": "comando"}
def execute(kg, ia, args, ctx_crew=None):
    from comandos.cmd_perguntar import execute as _perguntar
    return _perguntar(kg, ia, args, ctx_crew)
