"""Comando: criar — Cria conteudo usando o pipeline ReAct."""
def register():
    return {"name": "criar", "desc": "Cria conteudo (codigo, NPC, item, etc.) usando pipeline ReAct.",
            "handler": execute, "args": [{"name": "descricao", "type": "str", "required": True}], "categoria": "criacao"}
def execute(kg, ia, args, ctx_crew=None):
    from comandos.cmd_perguntar import execute as _perguntar
    texto = ' '.join(args)
    return _perguntar(kg, ia, [f"crie {texto}"], ctx_crew)
