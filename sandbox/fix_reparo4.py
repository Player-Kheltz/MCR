"""Rewrite the _auto_corrigir method completely"""
with open(r'E:\Projeto MCR\sandbox\mcr_auto_reparo.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find and replace the entire _auto_corrigir method
start = c.find('    def _auto_corrigir(self, discrepancias):')
end = c.find('    def _alimentar_kg(self, discrepancias):')

new_method = '''    def _auto_corrigir(self, discrepancias):
        """Auto-corrige os templates no mcr_ultimate.py."""
        print('\\n[4/4] Auto-corrigindo templates...')
        
        with open(ULTIMATE_PATH, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        backup_path = ULTIMATE_PATH + f'.bak_v{self.versoes}'
        shutil.copy2(ULTIMATE_PATH, backup_path)
        print(f'  Backup salvo: {backup_path}')
        
        for item in discrepancias:
            tipo = item['tipo']
            faltando = item['faltando']
            funcs_str = ', '.join(faltando[:8])
            
            prompt = "O template de " + str(tipo) + " esta desatualizado. Faltam: " + funcs_str + ". Gere linhas: mon:nomeFuncao(parametro)"
            novas_linhas = ia(prompt)
            if not novas_linhas: continue
            
            print(f'\\n  Corrigindo {tipo}...')
            
            # Encontra e insere no template
            padrao = re.compile(r"'" + str(tipo) + r"':\s*\{\s*'template':\s*'([^']+)'")
            m = padrao.search(conteudo)
            if m:
                template_atual = m.group(1)
                novas = '\\n'.join([l.strip() for l in novas_linhas.split('\\n') if l.strip() and '```' not in l])
                novo_template = template_atual + '\\n' + novas
                conteudo = conteudo.replace(template_atual, novo_template)
                print(f'    Template de {tipo} atualizado!')
                
                self.log['reparos'].append({
                    'versao': self.versoes, 'tipo': tipo,
                    'funcoes_adicionadas': faltando,
                    'data': str(datetime.datetime.now())[:19],
                })
                self.log['auto_aperfeicoamentos'] += 1
        
        with open(ULTIMATE_PATH, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f'\\n  mcr_ultimate.py atualizado!')
        self._alimentar_kg(discrepancias)
'''

c = c[:start] + new_method + c[end:]

with open(r'E:\Projeto MCR\sandbox\mcr_auto_reparo.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'auto_reparo.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
