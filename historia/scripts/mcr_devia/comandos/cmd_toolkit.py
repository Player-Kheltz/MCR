"""Comando: toolkit - Mostra inventario completo de capacidades do MCR-DevIA."""
def register():
    return {
        "name": "toolkit",
        "desc": "Mostra inventario completo de capacidades, comandos, modulos, e conceitos do MCR-DevIA.",
        "handler": execute,
        "args": [],
        "categoria": "consulta",
    }

def execute(kg, ia, args, ctx_crew=None):
    # Tenta usar o toolkit.py resgatado
    try:
        from tools.toolkit import gerar_contexto, resumo_rapido, TOOLKIT
        print(f'\n=== MCR-DevIA Toolkit ===')
        print(f'  {resumo_rapido()}')
        print()
        print(gerar_contexto())
    except ImportError:
        # Fallback: lista estatisticas basicas
        import os
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        modulos_dir = os.path.join(base, 'Scripts', 'mcr_devia', 'modulos')
        comandos_dir = os.path.join(base, 'Scripts', 'mcr_devia', 'comandos')
        
        n_modulos = len([f for f in os.listdir(modulos_dir) if f.endswith('.py')])
        n_comandos = len([f for f in os.listdir(comandos_dir) if f.startswith('cmd_') and f.endswith('.py')])
        
        print(f'\n=== MCR-DevIA ===')
        print(f'  Modulos: {n_modulos}')
        print(f'  Comandos: {n_comandos}')
        if kg:
            licoes = kg._get_licoes()
            ativas = sum(1 for l in licoes if not l.get('inactive'))
            print(f'  Lessons KG: {len(licoes)} total, {ativas} ativas')
    return True
