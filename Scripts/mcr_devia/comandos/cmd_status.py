"""Comando: status - Exibe metricas do Knowledge Graph."""
def register():
    return {
        "name": "status",
        "desc": "Exibe metricas do KG (versoes, licoes, geracoes)",
        "handler": execute,
        "args": [],
        "categoria": "consulta",
    }

def execute(kg, ia, args, ctx_crew=None):
    if not kg:
        print('[Status] KG nao disponivel')
        return True
    m = kg.data['metricas']
    print(f'\n[MCR-DevIA] V{kg.data["versoes"]}')
    print(f'  Licoes: {m["licoes"]}')
    print(f'  Geracoes: {m["geracoes"]}')
    print(f'  Compilacoes: {m["compilacoes"]}')
    print(f'  Usos: {m["usos"]}')
    # Mostra primeiras licoes
    for l in kg.data['licoes'][:5]:
        lid = l.get('id','?')
        err = l.get('erro','?')[:40]
        usos = l.get('usos',0)
        print(f'  {lid}: {err}... [{usos}x]')
    print(f'  Versoes: {kg.data.get("versoes",0)}')
    return True
