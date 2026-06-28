import re
with open(r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find build command section
for i, line in enumerate(lines):
    if "cmd == 'build'" in line:
        for j in range(i, min(i+30, len(lines))):
            txt = lines[j].rstrip()[:120]
            if 'ia(' in txt or 'fast(' in txt or 'subprocess' in txt or 'builder' in txt:
                print(f'L{j+1}: {txt}')
        break
