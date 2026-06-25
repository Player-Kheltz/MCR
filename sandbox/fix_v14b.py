"""Fix V14 double quote"""
with open(r'E:\Projeto MCR\sandbox\mcr_crew_v14.py', 'r', encoding='utf-8') as f:
    c = f.read()
# Fix: ''.cpp' -> '.cpp'
c = c.replace("''.cpp'", "'.cpp'")
with open(r'E:\Projeto MCR\sandbox\mcr_crew_v14.py', 'w', encoding='utf-8') as f:
    f.write(c)
try:
    compile(c, 'v14.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
