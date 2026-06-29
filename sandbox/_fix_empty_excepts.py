"""Adiciona pass a todos os except sem corpo em context_crew.py."""
lines = open(r'E:\Projeto MCR\scripts\mcr_devia\context_crew.py', 'r', encoding='utf-8').readlines()

new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    stripped = line.strip()
    if stripped.startswith('except') and stripped.endswith(':'):
        # Check if next line (after skip blank) has any code
        next_line = ''
        for j in range(i + 1, min(i + 5, len(lines))):
            if lines[j].strip():
                next_line = lines[j].strip()
                break
        if not next_line or next_line.startswith(('class ', 'def ', '#', '"""')):
            # Add pass with proper indentation
            indent = len(line) - len(line.lstrip())
            add_pass = ' ' * (indent + 4) + 'pass\n'
            # Check if we already added pass
            already_has = False
            for j in range(i + 1, min(i + 3, len(lines))):
                if 'pass' in lines[j]:
                    already_has = True
                    break
            if not already_has:
                new_lines.append(add_pass)
                print(f'  Added pass after L{i+1}: {stripped}')

with open(r'E:\Projeto MCR\scripts\mcr_devia\context_crew.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Done')
