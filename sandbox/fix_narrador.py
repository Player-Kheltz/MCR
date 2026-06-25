"""Fix narrator - make it technical like me"""
with open(r'E:\Projeto MCR\sandbox\mcr_observatory.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace the flowery narration prompt with a technical one
old = """            prompt = f"MCR-DevIA tem {n_licoes} licoes de conhecimento. Teve {len(reparos)} tentativas de auto-reparo. Narre o estado atual dele em 1 paragrafo curto e interessante, como se fosse um documentario."
            narracao = ia(prompt, 0.8)"""

new = """            prompt = f"MCR-DevIA tem {n_licoes} licoes de conhecimento. Teve {len(reparos)} tentativas de auto-reparo. Faca um relatorio TECNICO do estado atual: o que ele aprendeu, o que esta tentando fazer, o que esta travando. Seja direto e especifico, sem metaforas. Foque em dados e fatos."
            narracao = ia(prompt, 0.6)"""

c = c.replace(old, new)

# Replace the generic response prompt
old2 = """        prompt = f"{contexto}\n\nUsuario perguntou: {pergunta}\n\nComo narrador do MCR-DevIA, responda de forma clara e honesta sobre o que ele sabe, esta fazendo, ou aprendendo.""""

new2 = """        prompt = f"{contexto}\n\nUsuario perguntou: {pergunta}\n\nVoce e um assistente TECNICO especializado no MCR-DevIA. Responda de forma direta, com dados especificos: numeros de licoes, nomes de templates, funcoes descobertas. Seja util e preciso. Sem floreios.""""

c = c.replace(old2, new2)

with open(r'E:\Projeto MCR\sandbox\mcr_observatory.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'observatory.py', 'exec')
    print('OK! Narrador agora e TECNICO como o Cloud.')
except SyntaxError as e:
    print(f'Error: {e}')
