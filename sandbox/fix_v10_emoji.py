"""Fix ALL emojis in v10 - replace with ASCII"""
import re
with open(r'E:\Projeto MCR\sandbox\mcr_crew_v10.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace ALL emoji unicode escapes with ASCII text
emoji_map = {
    '\\u2705': '[OK]',
    '\\u274c': '[ERRO]',
    '\\U0001f4cc': '[TESTE]',
}

for old, new in emoji_map.items():
    c = c.replace(old, new)

with open(r'E:\Projeto MCR\sandbox\mcr_crew_v10.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'v10.py', 'exec')
    print('OK! Emojis removed, ASCII replacements added')
except SyntaxError as e:
    print(f'Error: {e}')
