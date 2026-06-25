"""Fix auto_reparo.py prompt"""
with open(r'E:\Projeto MCR\sandbox\mcr_auto_reparo.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find and replace the problematic section
old = '''            prompt = f"""O template de {tipo} no mcr_ultimate.py esta desatualizado.
Faltam estas funcoes (usadas no projeto real):
{", ".join(faltando[:8])}

O template atual esta em TEMPLATES['{tipo}'].

Gere APENAS as linhas NOVAS no formato:
    mon:{func}({{{param}}})\\n
para cada funcao faltando. Use nomes de parametros em ingles."""'''

new = '''            prompt = "O template de " + str(tipo) + " esta desatualizado. Faltam: " + ", ".join(faltando[:8]) + ". Gere linhas no formato mon:nomeFuncao(parametro)."'''

c = c.replace(old, new)

with open(r'E:\Projeto MCR\sandbox\mcr_auto_reparo.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'auto_reparo.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error: {e}')
