"""Comando: todo - Gerenciador de tarefas simples."""
def register():
    return {
        "name": "todo",
        "desc": "Lista tarefas pendentes. Uso: todo [add|done|list] [texto]",
        "handler": execute,
        "args": [],
        "categoria": "util",
    }

_tarefas = []

def execute(kg, ia, args, ctx_crew=None):
    if not args or args[0] == 'list':
        if not _tarefas:
            print('[Todo] Nenhuma tarefa pendente')
        else:
            print(f'[Todo] {len(_tarefas)} tarefa(s):')
            for i, t in enumerate(_tarefas, 1):
                status = 'x' if t.get('done') else ' '
                print(f'  [{status}] {i}. {t.get("texto","")}')
        return True
    
    if args[0] == 'add' and len(args) > 1:
        texto = ' '.join(args[1:])
        _tarefas.append({'texto': texto, 'done': False})
        print(f'[Todo] Adicionado: {texto}')
        return True
    
    if args[0] == 'done' and len(args) > 1:
        try:
            idx = int(args[1]) - 1
            if 0 <= idx < len(_tarefas):
                _tarefas[idx]['done'] = True
                print(f'[Todo] Concluido: {_tarefas[idx]["texto"]}')
            else:
                print(f'[Todo] Tarefa #{args[1]} nao encontrada')
        except Exception: pass
        return True
    
    print('[Todo] Uso: todo [add <texto>|done <n>|list]')
    return True
