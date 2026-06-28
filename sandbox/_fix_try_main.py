#!/usr/bin/env python
"""Add try/except around main() call."""
path = r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find "if __name__ == '__main__':" and the next line "    main()"
for i, line in enumerate(lines):
    if "if __name__ == '__main__':" in line:
        # Replace the next line with try/except
        if i + 1 < len(lines) and 'main()' in lines[i + 1]:
            lines[i + 1] = '    try: main()\n'
            lines.insert(i + 2, '    except Exception as e:\n')
            lines.insert(i + 3, '        print(f"[MCR-DevIA] ERRO FATAL: {e}")\n')
            lines.insert(i + 4, '        import traceback; traceback.print_exc()\n')
            break

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

try:
    compile(''.join(lines), path, 'exec')
    print('OK - try/except adicionado ao main()')
except SyntaxError as e:
    print(f'ERRO: {e}')
