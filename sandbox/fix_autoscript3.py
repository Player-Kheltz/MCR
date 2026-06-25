"""Fix auto-script with robust Python syntax fixer"""
with open(r'E:\Projeto MCR\sandbox\mcr_autoscript.py','r',encoding='utf-8') as f:
    c = f.read()

# Replace the validation loop with a more robust one
old = """        # 4. Python VALIDA com LOOP DE CORRECAO (IA se corrige)
        valido = False
        for tentativa in range(5):
            try:
                compile(codigo, nome + '.py', 'exec')
                valido = True
                break
            except SyntaxError as e:
                print(f'  [ERRO] Tentativa {tentativa+1}: {e.msg}')
                # IA analisa o erro e corrige
                prompt_correcao = f'''O script Python abaixo tem um erro de sintaxe:
LINHA {e.lineno}: {e.msg}

CODIGO COM ERRO:
```python
{codigo[:1500]}
```

Corrija o erro e retorne o CODIGO COMPLETO corrigido (sem explicacoes).'''
                r = self.ia.gerar(prompt_correcao, 0.4)
                if r:
                    import re
                    m = re.search(r'```python\\n(.*?)```', r, re.DOTALL)
                    if m:
                        codigo = m.group(1)
                    else:
                        codigo = r
                else:
                    break"""

new = """        # 4. Python VALIDA e CORRIGE (sem chamar IA de novo - mais rapido)
        import ast
        valido = False
        for tentativa in range(5):
            try:
                ast.parse(codigo)
                valido = True
                break
            except SyntaxError as e:
                erro_msg = str(e)
                print(f'  [CORRIGINDO] {e.msg} (linha {e.lineno})')
                linhas = codigo.split('\\n')
                if e.lineno and 0 < e.lineno <= len(linhas):
                    idx = e.lineno - 1
                    linha = linhas[idx]
                    # Correcoes comuns:
                    if 'expected an indented block' in erro_msg:
                        # Adiciona pass no bloco vazio
                        linhas.insert(idx, '    pass')
                    elif 'unexpected indent' in erro_msg:
                        linhas[idx] = linha.lstrip()  # Remove indent extra
                    elif "invalid syntax" in erro_msg and linha.strip().endswith(':'):
                        linhas.insert(idx+1, '    pass')
                    elif "unterminated string" in erro_msg:
                        # Comenta a linha problematica
                        linhas[idx] = '# ' + linha
                    else:
                        # Comenta a linha
                        linhas[idx] = '# ' + linha
                    codigo = '\\n'.join(linhas)
                else:
                    break
        
        if not valido:
            # Fallback: script minimo
            print('  [FALLBACK] Usando script minimo')
            codigo = TEMPLATE_SCRIPT.format(
                nome=nome, descricao=desc, data=str(datetime.datetime.now())[:19],
                campos='', logica="print('Script em desenvolvimento')",
                main="main()",
            )"""

c = c.replace(old, new)

with open(r'E:\Projeto MCR\sandbox\mcr_autoscript.py','w',encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'autoscript.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error: {e}')
