"""Comando: fazer — Cria/executa acoes usando o pipeline ReAct."""
def register():
    return {"name": "fazer", "desc": "Executa acoes (criar, modificar, configurar) usando pipeline ReAct.",
            "handler": execute, "args": [{"name": "descricao", "type": "str", "required": True}], "categoria": "criacao"}
def execute(kg, ia, args, ctx_crew=None):
    from comandos.cmd_perguntar import execute as _perguntar
    texto = ' '.join(args)
    return _perguntar(kg, ia, [f"faca {texto}"], ctx_crew)
