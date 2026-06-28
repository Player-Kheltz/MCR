"""Comando: status - Exibe metricas do KG."""
def register():
    return {
        "name": "status",
        "desc": "Exibe metricas do Knowledge Graph",
        "handler": execute,
        "args": [],
        "categoria": "consulta",
    }

def execute(kg, ia, args, ctx_crew=None):
    m = kg.data['metricas']
    print(f'[Comando] V{kg.data["versoes"]} | Licoes: {m["licoes"]} | Geracoes: {m["geracoes"]}')
    return True
