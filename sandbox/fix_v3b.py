"""Fix V3 - move nome_dominio into function"""
with open(r'E:\Projeto MCR\sandbox\gerador_shc_v3.py', 'r', encoding='utf-8') as f:
    c = f.read()
# Remove the bad line at module level
c = c.replace("    nome_dominio = args.dominio\n\n    linhas.append('')\n    nome_dominio = args.dominio", "    linhas.append('')")
# Put it inside the function  
c = c.replace("def montar_todas_habilidades(slots, criativos_dict, cfg):", "def montar_todas_habilidades(slots, criativos_dict, cfg, nome_arquivo):")
c = c.replace('f">> SPA: habilidades/{nome_dominio}.lua carregado"', 'f">> SPA: habilidades/{nome_arquivo}.lua carregado"')
# Fix the call site  
c = c.replace('conteudo = montar_todas_habilidades(slots, criativos, cfg)', 'conteudo = montar_todas_habilidades(slots, criativos, cfg, args.dominio)')
with open(r'E:\Projeto MCR\sandbox\gerador_shc_v3.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Fixed!')
