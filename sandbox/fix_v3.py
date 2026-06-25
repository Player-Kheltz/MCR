"""Fix V3 generator"""
with open(r'E:\Projeto MCR\sandbox\gerador_shc_v3.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix: the DOMINIOS key was corrupted
c = c.replace("'{args.dominio}': {", "'clavas_leves': {")

# Fix: the print line  
c = c.replace('f">> SPA: habilidades/{args.dominio}.lua carregado"', 'f">> SPA: habilidades/{nome_dominio}.lua carregado"')
# Add nome_dominio variable
c = c.replace("linhas.append('')", "linhas.append('')\n    nome_dominio = args.dominio", 1)

with open(r'E:\Projeto MCR\sandbox\gerador_shc_v3.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('V3 fixed!')
