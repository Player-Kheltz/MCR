"""
    local_utils.py — Utilitarios locais para substituir Read/Write/Edit/Glob/Todo
    Uso: python local_utils.py <comando> [args...]
    
    Comandos:
      read <path>              — Le arquivo
      write <path> <content>   — Escreve arquivo (content via stdin ou argumento)
      edit <path> <old> <new>  — Substitui texto no arquivo
      glob <pattern> [path]    — Busca arquivos por padrao
      todowrite <json>         — Salva todo list (json via stdin)
      todoread                 — Le todo list atual
"""
import sys, os, json, glob as glob_mod, re

BASE = os.environ.get('MCR_ROOT', r'E:\Projeto MCR')

def cmd_read(args):
    path = os.path.join(BASE, args[0]) if not os.path.isabs(args[0]) else args[0]
    if not os.path.exists(path):
        print(f"Arquivo nao encontrado: {path}", file=sys.stderr)
        return 1
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        sys.stdout.buffer.write(f.read().encode('utf-8'))
    return 0

def cmd_write(args):
    path = os.path.join(BASE, args[0]) if not os.path.isabs(args[0]) else args[0]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if len(args) > 1:
        content = args[1]
    else:
        content = sys.stdin.read()
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Escrito: {path}", file=sys.stderr)
    return 0

def cmd_edit(args):
    if len(args) < 3:
        print("Uso: edit <path> <old> <new>", file=sys.stderr)
        return 1
    path = os.path.join(BASE, args[0]) if not os.path.isabs(args[0]) else args[0]
    old, new = args[1], args[2]
    if not os.path.exists(path):
        print(f"Arquivo nao encontrado: {path}", file=sys.stderr)
        return 1
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if old not in content:
        print(f"ERRO: texto nao encontrado em {path}", file=sys.stderr)
        return 1
    count = content.count(old)
    if count > 1:
        print(f"AVISO: {count} ocorrencias, substituindo todas", file=sys.stderr)
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Editado: {path} ({count} ocorrencias)", file=sys.stderr)
    return 0

def cmd_glob(args):
    pattern = args[0]
    path = args[1] if len(args) > 1 else BASE
    full_pattern = os.path.join(path, pattern)
    results = glob_mod.glob(full_pattern, recursive=True)
    for r in results:
        rel = os.path.relpath(r, BASE)
        print(rel)
    return 0

def cmd_todowrite(args):
    if sys.stdin.isatty():
        print("Forneca o JSON via stdin", file=sys.stderr)
        return 1
    data = json.load(sys.stdin)
    todo_path = os.path.join(BASE, '.local_todo.json')
    with open(todo_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"TODO salvo: {len(data.get('todos', []))} itens", file=sys.stderr)
    return 0

def cmd_todoread(args):
    todo_path = os.path.join(BASE, '.local_todo.json')
    if not os.path.exists(todo_path):
        print("Nenhum TODO ativo", file=sys.stderr)
        return 0
    with open(todo_path, 'r', encoding='utf-8') as f:
        print(f.read())
    return 0

COMMANDS = {
    'read': cmd_read, 'write': cmd_write, 'edit': cmd_edit,
    'glob': cmd_glob, 'todowrite': cmd_todowrite, 'todoread': cmd_todoread,
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__, file=sys.stderr)
        return 1
    return COMMANDS[sys.argv[1]](sys.argv[2:])

if __name__ == '__main__':
    sys.exit(main())
