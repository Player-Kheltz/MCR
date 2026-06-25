"""Fix V18 qualidade scope"""
with open(r'E:\Projeto MCR\sandbox\mcr_crew_v18.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Line 185 has lore_npc = gerar_lore(...)
# Add qualidade = 0 after it
for i, line in enumerate(lines):
    if 'lore_npc = gerar_lore(ia' in line and i+1 < len(lines):
        if 'qualidade' not in lines[i+1]:
            lines.insert(i+1, '        qualidade = 0\n')
            break

with open(r'E:\Projeto MCR\sandbox\mcr_crew_v18.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

try:
    compile(''.join(lines), 'v18.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error: {e}')
