"""Fix Sistemas module - simpler prompt"""
with open(r'E:\Projeto MCR\sandbox\mcr_crew.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix the sistemas prompt to be simpler
old = """        if tarefa == 'projetar':
            prompt = (
                f"Projete um sistema para o servidor Tibia MCR.\\n"
                f"Descricao: {descricao}\\n"
                f"Linguagem: {linguagem}\\n"
                f"{fp_ctx}\\n\\n"
                f"Responda JSON:\\n"
                f'{{"arquitetura":"descricao da arquitetura","arquivos":["path1","path2"],"api":"descricao da API","notas":"observacoes"}}'
            )"""

new = """        if tarefa == 'projetar':
            prompt = (
                "Projete um sistema simples para o servidor Tibia MCR.\\n"
                f"Descricao: {descricao}\\n"
                f"Linguagem: {linguagem}\\n"
                f"{fp_ctx}\\n\\n"
                "Responda JSON com 3 campos:\\n"
                '{\\n'
                '  "nome": "nome do sistema",\\n'
                '  "descricao": "o que faz em 1 frase",\\n'
                '  "arquivos": ["caminho/arquivo1.lua", "caminho/arquivo2.cpp"]\\n'
                '}\\n\\n'
                "Exemplo: {\\"nome\\":\\"Sistema de Crafting\\",\\"descricao\\":\\"Combina recursos em equipamentos\\",\\"arquivos\\":[\\"data/scripts/crafting.lua\\"]}\\n"
                "Seja CONCISO."
            )"""

c = c.replace(old, new)

with open(r'E:\Projeto MCR\sandbox\mcr_crew.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'mcr_crew.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error: {e}')
