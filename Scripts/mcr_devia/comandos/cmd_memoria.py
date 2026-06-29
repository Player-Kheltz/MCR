"""Comando: memoria - Consulta o historico de interacoes fragmentado."""
def register():
    return {
        "name": "memoria",
        "desc": "Consulta historico. Uso: memoria [--cmd X] [--limite N] [--stats] [--dias N] [--timeline]",
        "handler": execute,
        "args": [],
        "categoria": "kernel",
    }

def execute(kg, ia, args, ctx_crew=None):
    # Tenta acessar o modulo memoria via contexto
    memoria = None
    if ctx_crew:  # kernel passa ctx_crew, mas memoria fica em outro lugar
        pass
    
    # Como estamos no kernel, importamos direto
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    try:
        from modulos.memoria import Memoria
        mem = Memoria()
    except ImportError:
        print('[Memoria] Modulo de memoria nao disponivel')
        return True
    
    limite = 10
    dias = 7
    filtro_cmd = None
    mostrar_stats = '--stats' in args
    mostrar_timeline = '--timeline' in args or len([a for a in args if not a.startswith('--')]) == 0
    
    for i, a in enumerate(args):
        if a == '--cmd' and i+1 < len(args): filtro_cmd = args[i+1]
        if a == '--limite' and i+1 < len(args): limite = int(args[i+1])
        if a == '--dias' and i+1 < len(args): dias = int(args[i+1])
    
    if '--todos' in args: limite = 9999
    
    if mostrar_stats:
        est = mem.estatisticas(dias=dias)
        print(f'[Memoria] Estatisticas (ultimos {est["dias_consultados"]} dias):')
        print(f'  Total registros: {est["total"]}')
        print(f'  Comandos distintos: {est["comandos_distintos"]}')
        print(f'  Mais usado: {est["cmd_mais_usado"]}')
        print(f'  Sessoes: {est["sessoes"]}')
        print(f'  Arquivos em disco: {est["arquivos"]} ({est["tamanho_kb"]}KB)')
        print(f'  Ultimo registro: {est["ultimo_registro"]}')
        return True
    
    if mostrar_timeline:
        entradas = mem.consultar(cmd=filtro_cmd, limite=limite, dias=dias)
        if not entradas:
            print('[Memoria] Nenhum registro encontrado')
            return True
        print(f'[Memoria] Timeline ({len(entradas)} registros, {dias}dias):')
        for e in reversed(entradas):
            ts = e.get('ts', '?')[11:19]
            cmd = e.get('cmd', '?')
            a = e.get('args', [])
            r = e.get('resultado', '?')
            err = e.get('erro')
            a_str = ' '.join(str(x) for x in a)
            status = 'OK' if r else 'FALHA'
            linha = f'  [{ts}] {cmd:15s} {a_str:35s} {status}'
            if err: linha += f' ERRO: {err}'
            print(linha)
        return True
    
    return True
