#!/usr/bin/env python
"""Fix --json handler to skip sys.argv parsing when using JSON."""
import sys

path = r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and modify the --json handler to add _from_json flag
for i, line in enumerate(lines):
    if '    # Modo --json: comando via arquivo' in line:
        # Add _from_json = False before the handler
        lines.insert(i, '    _from_json = False\n')
        i += 1
        break

# Now find the handler itself and update it to set _from_json = True
for i, line in enumerate(lines):
    if "import json as _json; cmd_data = _json.load(f)" in line:
        # After the except block, add _from_json = True and a comment
        # Find the line with 'return' in the except block
        for j in range(i, i+10):
            if 'return' in lines[j] and j < len(lines):
                # Insert _from_json = True before the return
                lines.insert(j, '                _from_json = True\n')
                break
        break

# Find the normal arg parsing: 'if len(sys.argv) < 2:' and wrap with if not _from_json
for i, line in enumerate(lines):
    if 'if len(sys.argv) < 2:' in line and '_from_json' not in lines[i-1] if i > 0 else True:
        # Check if this is the SECOND occurrence (first is wrapped)
        # Actually just check surrounding code
        lines.insert(i, '    if not _from_json:\n')
        # Now indent all lines until the next non-indented (relative to function)
        # Find the closing of this block
        indent_level = 4  # 4 spaces
        for j in range(i+1, len(lines)):
            if lines[j].startswith('    ') and not lines[j].startswith('        '):
                # This is at function indent level, add indentation
                if not _from_json check already processed:
                    pass
        break

print('Nao implementado - abordagem muito complexa para script simples')
print('Usando abordagem alternativa: mover cmd/args parsing para dentro do if not _from_json')
