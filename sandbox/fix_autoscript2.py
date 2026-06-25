"""Add self-debugging loop to auto-script"""
with open(r'E:\Projeto MCR\sandbox\mcr_autoscript.py','r',encoding='utf-8') as f:
    c = f.read()

# Replace the validation section with a smarter loop
old = """        # 4. Python VALIDA (compila o codigo)
        try:
            compile(codigo, nome + '.py', 'exec')
            valido = True
        except SyntaxError as e:
            valido = False
            print(f'  [ERRO] Sintaxe: {e}')
            # Tenta corrigir
            codigo, valido = self._corrigir(codigo)"""

new = """        # 4. Python VALIDA com LOOP DE CORRECAO (IA se corrige)
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
                    # Extrai codigo de dentro de ``` se houver
                    import re
                    m = re.search(r'```python\\n(.*?)```', r, re.DOTALL)
                    if m:
                        codigo = m.group(1)
                    else:
                        codigo = r
                else:
                    break"""

c = c.replace(old, new)

with open(r'E:\Projeto MCR\sandbox\mcr_autoscript.py','w',encoding='utf-8') as f:
    f.write(c)
print('Auto-corretor aprimorado!')
