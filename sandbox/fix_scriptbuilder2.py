"""Fix script builder prompt"""
with open(r'E:\Projeto MCR\sandbox\mcr_scriptbuilder.py','r',encoding='utf-8') as f:
    c = f.read()

# The issue is f-string with triple quotes containing code with triple quotes
# Replace the entire prompt definition with one that doesn't have this issue
old_start = """prompt = f\"\"\"Crie uma funcao Python chamada 'executar' que: {descricao}"""
new_start = """prompt = ('Crie uma funcao Python chamada executar que: ' + repr(descricao) + '. ')"""
c = c.replace(old_start, new_start)

# Find where the prompt ends and replace with simple ending  
old_end = "return f'Encontrados {len(results)} arquivos'\"\"\""
new_end = "return resultado'"
c = c.replace(old_end, new_end)

# Replace the closing of the f-string
old_close = """        logica = self.ia.gerar(prompt, 0.6)"""
# Keep this line - it's fine

with open(r'E:\Projeto MCR\sandbox\mcr_scriptbuilder.py','w',encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'scriptbuilder.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
