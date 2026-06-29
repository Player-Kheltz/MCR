"""Comando: ensinar - Registra conhecimento no KG."""
def register():
    return {
        "name": "ensinar",
        "desc": "Regstra licao no KG: ensinar <erro> <causa> <solucao> [ctx]",
        "handler": execute,
        "args": [
            {"name": "erro", "type": "str", "required": True},
            {"name": "causa", "type": "str", "required": True},
            {"name": "solucao", "type": "str", "required": True},
            {"name": "ctx", "type": "str", "required": False},
        ],
        "categoria": "kg",
    }

def execute(kg, ia, args, ctx_crew=None):
    if not kg or len(args) < 3:
        print('[Ensinar] Uso: ensinar <erro> <causa> <solucao> [ctx]')
        return True
    erro = args[0]
    causa = args[1]
    solucao = args[2]
    ctx = args[3] if len(args) > 3 else 'licao'
    kg.aprender(erro, causa, solucao, ctx)
    print(f'  [APRENDIDO] "{erro[:60]}..."')
    return True
