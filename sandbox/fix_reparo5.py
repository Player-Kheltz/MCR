"""Fix the regex and test auto-repair properly"""
with open(r'E:\Projeto MCR\sandbox\mcr_auto_reparo.py', 'r', encoding='utf-8') as f:
    c = f.read()

# The old regex expects single-line template but mcr_ultimate.py uses multi-line
# Fix: use a more flexible approach - find the TEMPLATES dict and replace within it
old_pattern = """            padrao = re.compile(r"'" + str(tipo) + r"':\\s*\\{\\s*'template':\\s*'([^']+)'")
            m = padrao.search(conteudo)
            if m:
                template_atual = m.group(1)
                novas = '\\n'.join([l.strip() for l in novas_linhas.split('\\n') if l.strip() and '\`\`\`' not in l])
                novo_template = template_atual + '\\n' + novas
                conteudo = conteudo.replace(template_atual, novo_template)
                print(f'    Template de {tipo} atualizado!')"""

new_pattern = """            # Procura o template no formato multi-linha do TEMPLATES dict
            marker = f"'{tipo}': {{"
            idx = conteudo.find(marker)
            if idx > 0:
                # Encontra 'template': e seu valor
                tmpl_marker = "'template':"
                tmpl_start = conteudo.find(tmpl_marker, idx)
                if tmpl_start > 0:
                    # Pula aspas e encontra o inicio do valor do template
                    quote_start = conteudo.find(\"'\", tmpl_start + len(tmpl_marker))
                    if quote_start > 0:
                        quote_end = conteudo.find(\"'\", quote_start + 1)
                        if quote_end > quote_start:
                            template_atual = conteudo[quote_start+1:quote_end]
                            novas = '\\\\n'.join([l.strip() for l in novas_linhas.split('\\\\n') if l.strip() and '\`\`\`' not in l])
                            # Insere novas funcoes antes do print
                            print_marker = 'print('
                            print_idx = template_atual.find(print_marker)
                            if print_idx > 0:
                                before_print = template_atual[:print_idx]
                                after_print = template_atual[print_idx:]
                                novo_template = before_print + novas + '\\\\n' + after_print
                                conteudo = conteudo.replace(template_atual, novo_template)
                                print(f'    Template de {tipo} atualizado!')
                            else:
                                novo_template = template_atual + '\\\\n' + novas
                                conteudo = conteudo.replace(template_atual, novo_template)
                                print(f'    Template de {tipo} atualizado (append)!')"""

c = c.replace(old_pattern, new_pattern)

with open(r'E:\Projeto MCR\sandbox\mcr_auto_reparo.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'auto_reparo.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error: {e}')
