"""Fix - better auto-correction for generated scripts"""
with open(r'E:\Projeto MCR\sandbox\mcr_autoscript.py','r',encoding='utf-8') as f:
    c = f.read()

old = """    def _corrigir(self, codigo):
        \"\"\"Tenta corrigir erros de sintaxe simples.\"\"\"
        # Remove linhas problematicas
        linhas = codigo.split('\\n')
        corrigido = []
        for linha in linhas:
            # Linhas com "..." ou "pass" solto
            if linha.strip() in ('...', 'pass', '', 'main()'):
                continue
            corrigido.append(linha)
        
        codigo = '\\n'.join(corrigido)
        try:
            compile(codigo, 'corrigido.py', 'exec')
            print('  [CORRIGIDO] Erro de sintaxe resolvido')
            return codigo, True
        except:
            return codigo, False"""

new = """    def _corrigir(self, codigo):
        \"\"\"Tenta corrigir erros de sintaxe simples.\"\"\"
        import ast
        linhas = codigo.split('\\n')
        
        for tentativa in range(5):
            try:
                ast.parse(codigo)
                return codigo, True
            except SyntaxError as e:
                erro_linha = e.lineno - 1 if e.lineno else 0
                if 0 <= erro_linha < len(linhas):
                    linha_erro = linhas[erro_linha]
                    # Tenta correcoes comuns
                    if linha_erro.strip().startswith('...'):
                        linhas[erro_linha] = '# ' + linha_erro
                    elif linha_erro.strip() in ('', 'pass'):
                        linhas.pop(erro_linha)
                    elif ':' in linha_erro and not linha_erro.strip().endswith(':'):
                        # Linha de atribuicao com valor estranho
                        linhas[erro_linha] = '# ' + linha_erro
                    else:
                        # Remove a linha problematica
                        linhas[erro_linha] = '#' + linha_erro
                    codigo = '\\n'.join(linhas)
                else:
                    break
        
        return codigo, False"""

c = c.replace(old, new)

with open(r'E:\Projeto MCR\sandbox\mcr_autoscript.py','w',encoding='utf-8') as f:
    f.write(c)
print('OK!')
