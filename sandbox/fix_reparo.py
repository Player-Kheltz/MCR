"""Fix the f-string in auto_reparo.py"""
with open(r'E:\Projeto MCR\sandbox\mcr_auto_reparo.py', 'r', encoding='utf-8') as f:
    c = f.read()

# The problematic line was a complex f-string with unescaped braces
# Replace the entire prompt generation
old = """            prompt = ('O template de ' + str(tipo) + ' no mcr_ultimate.py esta desatualizado.\\n' + 'Faltam: ' + ', '.join(faltando[:8]) + '\\n' + 'Gere as linhas NOVAS, uma por linha.')
            novas_linhas = ia(prompt)"""

new = """            prompt = "O template de " + str(tipo) + " esta desatualizado. Faltam: " + ", ".join(faltando[:8]) + ". Gere uma linha de template para cada funcao faltante."
            novas_linhas = ia(prompt)"""

c = c.replace(old, new)

with open(r'E:\Projeto MCR\sandbox\mcr_auto_reparo.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'auto_reparo.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error: {e}')
