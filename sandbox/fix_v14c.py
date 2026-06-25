"""Fix V14 - handle None template"""
with open(r'E:\Projeto MCR\sandbox\mcr_crew_v14.py', 'r', encoding='utf-8') as f:
    c = f.read()
# Fix: check if template is not None
c = c.replace("if mod['template'] and mod['blanks']:", "if mod.get('template') and mod.get('blanks'):")
with open(r'E:\Projeto MCR\sandbox\mcr_crew_v14.py', 'w', encoding='utf-8') as f:
    f.write(c)
try:
    compile(c, 'v14.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error: {e}')
