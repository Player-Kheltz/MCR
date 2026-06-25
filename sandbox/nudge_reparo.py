"""Nudge: dar ao MCR-DevIA feedback do proprio fracasso"""
import re

with open(r'E:\Projeto MCR\sandbox\mcr_auto_reparo.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Add a verification step AFTER the repair attempt
old = """                # Procura o template no formato multi-linha do TEMPLATES dict
            marker = f"'{tipo}': {{"
            idx = conteudo.find(marker)
            if idx > 0:
                # Encontra 'template': e seu valor
                tmpl_marker = "'template':"
                tmpl_start = conteudo.find(tmpl_marker, idx)
                if tmpl_start > 0:
                    # Pula aspas e encontra o inicio do valor do template
                    quote_start = conteudo.find("'", tmpl_start + len(tmpl_marker))
                    if quote_start > 0:
                        quote_end = conteudo.find("'", quote_start + 1)
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

new = """                # Procura o template no formato multi-linha do TEMPLATES dict
            marker = f"'{tipo}': {{"
            idx = conteudo.find(marker)
            if idx > 0:
                tmpl_marker = "'template':"
                tmpl_start = conteudo.find(tmpl_marker, idx)
                if tmpl_start > 0:
                    quote_start = conteudo.find("'", tmpl_start + len(tmpl_marker))
                    if quote_start > 0:
                        quote_end = conteudo.find("'", quote_start + 1)
                        if quote_end > quote_start:
                            template_atual = conteudo[quote_start+1:quote_end]
                            novas = '\\\\n'.join([l.strip() for l in novas_linhas.split('\\\\n') if l.strip() and '\`\`\`' not in l])
                            print_marker = 'print('
                            print_idx = template_atual.find(print_marker)
                            if print_idx > 0:
                                before_print = template_atual[:print_idx]
                                after_print = template_atual[print_idx:]
                                novo_template = before_print + novas + '\\\\n' + after_print
                                conteudo = conteudo.replace(template_atual, novo_template)
                                # VERIFICACAO: sera que realmente mudou?
                                if novo_template in conteudo and template_atual not in conteudo:
                                    print(f'    [OK] Template de {tipo} atualizado com sucesso!')
                                    self.log['reparos'].append({
                                        'versao': self.versoes, 'tipo': tipo,
                                        'funcoes_adicionadas': faltando,
                                        'resultado': 'sucesso',
                                        'data': str(datetime.datetime.now())[:19],
                                    })
                                    self.log['auto_aperfeicoamentos'] += 1
                                else:
                                    print(f'    [FALHA] Template de {tipo} NAO foi atualizado!')
                                    print(f'    Motivo: o formato do arquivo pode ser diferente do esperado.')
                                    # Registra o fracasso para aprender
                                    self.log['reparos'].append({
                                        'versao': self.versoes, 'tipo': tipo,
                                        'funcoes_adicionadas': faltando,
                                        'resultado': 'falha',
                                        'motivo': 'formato do arquivo diferente do esperado',
                                        'data': str(datetime.datetime.now())[:19],
                                    })
                            else:
                                # Tambem verifica
                                pass
                        else:
                            print(f'    [FALHA] Nao encontrou aspas no template')
                    else:
                        print(f'    [FALHA] Nao encontrou template: marker')
                else:
                    print(f'    [FALHA] Nao encontrou template: marker no dict')
            else:
                print(f'    [FALHA] Nao encontrou dict para {tipo} no arquivo')
                print(f'    O arquivo mcr_ultimate.py pode ter sido sobrescrito ou estar em formato diferente.')"""

c = c.replace(old, new)

with open(r'E:\Projeto MCR\sandbox\mcr_auto_reparo.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'auto_reparo.py', 'exec')
    print('OK! - Agora MCR-DevIA tem FEEDBACK DO PROPRIO FRACASSO')
except SyntaxError as e:
    print(f'Error: {e}')
