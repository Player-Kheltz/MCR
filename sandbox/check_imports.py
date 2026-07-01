import ast, sys, os

base = 'E:/Projeto MCR/Scripts/mcr_devia'
files = ['kernel.py', 'comandos/cmd_memoria.py', 'master_agent.py']
all_ok = True

for f in files:
    path = os.path.join(base, f.replace('/', os.sep))
    if not os.path.exists(path):
        print(f'{f}: FILE NOT FOUND')
        all_ok = False
        continue
    with open(path, 'r', encoding='utf-8') as fh:
        try:
            tree = ast.parse(fh.read())
            print(f'=== {f} ({len(fh.read())} chars, {len(tree.body)} stmts) ===')
            fh.seek(0)
            content = fh.read()
            for line_no, line in enumerate(content.split('\n'), 1):
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    print(f'  Line {line_no}: {stripped}')
        except SyntaxError as e:
            print(f'{f}: SYNTAX ERROR - {e}')
            all_ok = False

print(f'\nAll OK: {all_ok}')
