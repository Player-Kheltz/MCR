"""Fix resolver training - remove invalid python call"""
with open(r'E:\Projeto MCR\sandbox\resolver_training.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Remove the invalid line
c = c.replace("python criar_training.py  # recria os arquivos originais", "import subprocess; subprocess.run(['python', 'criar_training.py'], cwd=os.path.dirname(__file__))")

with open(r'E:\Projeto MCR\sandbox\resolver_training.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'resolver.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error: {e}')
