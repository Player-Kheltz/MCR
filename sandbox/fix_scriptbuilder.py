"""Fix prompt string issue"""
with open(r'E:\Projeto MCR\sandbox\mcr_scriptbuilder.py','r',encoding='utf-8') as f:
    c = f.read()

# The issue is the """ at the end of the prompt closing the string
# Fix: replace with a different approach
old = """Exemplo de funcao:
def executar(args):
    import os
    results = []
    for root, dirs, files in os.walk(args.diretorio):
        for f in files:
            if f.endswith('.lua'):
                results.append(f)
    return f'Encontrados {len(results)} arquivos'\"\"\""""  

new = """Exemplo de funcao:
def executar(args):
    import os
    files = [f for root, dirs, files in os.walk(args.diretorio) for f in files if f.endswith('.lua')]
    return f'Encontrados {len(files)} arquivos'"""

c = c.replace(old, new)

# Also need to fix the closing of the prompt string properly
# The old code had """ at the end which was meant to be part of the f-string
# But it was actually closing the Python string

with open(r'E:\Projeto MCR\sandbox\mcr_scriptbuilder.py','w',encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'scriptbuilder.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
