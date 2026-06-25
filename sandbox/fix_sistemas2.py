"""Fix Sistemas - text mode instead of JSON"""
with open(r'E:\Projeto MCR\sandbox\mcr_crew.py', 'r', encoding='utf-8') as f:
    c = f.read()

old = """        if tarefa == 'projetar':
            prompt = (
                "Projete um sistema simples para o servidor Tibia MCR.\\n"
                f"Descricao: {descricao}\\n"
                f"Linguagem: {linguagem}\\n"
                f"{fp_ctx}\\n\\n"
                "Responda JSON com 3 campos:\\n"
                '{\\n'
                '  "nome": "nome do sistema",\\n'
                '  "descricao": "o que faz em 1 frase",\\n'
                '  "arquivos": ["caminho/arquivo1.lua", "caminho/arquivo2.cpp"]\\n'
                '}\\n\\n'
                "Exemplo: {\\"nome\\":\\"Sistema de Crafting\\",\\"descricao\\":\\"Combina recursos em equipamentos\\",\\"arquivos\\":[\\"data/scripts/crafting.lua\\"]}\\n"
                "Seja CONCISO."
            )"""

new = """        if tarefa == 'projetar':
            # Modo texto: IA responde em texto, Python extrai info
            prompt = (
                "Projete um sistema para o servidor Tibia MCR.\\n"
                f"Descricao: {descricao}\\n"
                f"Linguagem: {linguagem}\\n"
                f"{fp_ctx}\\n\\n"
                "Formato da resposta (siga exatamente):\\n"
                "NOME: nome_do_sistema\\n"
                "DESCRICAO: descricao em 1 linha\\n"
                "ARQUIVOS: arquivo1.lua, arquivo2.cpp\\n"
            )"""

c = c.replace(old, new)

# Also fix the parsing part
old_parse = """        r = self.ia.gerar(prompt, 0.7)
        dados = self.ia.extrair_json(r) if r else None
        
        if isinstance(dados, dict):
            print(f'  Arquitetura: {str(dados.get("arquitetura","?"))[:100]}')
            arquivos = dados.get('arquivos', [])
            for arq in arquivos:
                if isinstance(arq, dict):
                    path = arq.get('path', '')
                    codigo = arq.get('codigo', '')
                    if path and codigo:
                        full_path = os.path.join(r'E:\\Projeto MCR', path)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(codigo)
                        print(f'  Arquivo: {path}')
            self.fp.registrar_acerto(descricao[:50])
        else:
            print('  ERRO: IA nao gerou JSON valido')
            self.fp.registrar_erro(descricao[:50], 'JSON invalido')"""

new_parse = """        r = self.ia.gerar(prompt, 0.7)
        
        if r:
            # Extrai informacoes do texto
            nome = ''
            desc = ''
            arquivos = []
            for line in r.split('\\n'):
                line = line.strip()
                if line.startswith('NOME:'):
                    nome = line[5:].strip()
                elif line.startswith('DESCRICAO:'):
                    desc = line[9:].strip()
                elif line.startswith('ARQUIVOS:'):
                    arqs = line[9:].strip()
                    arquivos = [a.strip() for a in arqs.split(',') if a.strip()]
            
            if nome:
                print(f'  Sistema: {nome}')
                print(f'  Descricao: {desc[:80]}')
                print(f'  Arquivos: {len(arquivos)}')
                self.fp.registrar_acerto(nome)
            else:
                print('  ERRO: IA nao seguiu o formato')
                self.fp.registrar_erro(descricao[:30], 'formato invalido')
        else:
            print('  ERRO: IA nao respondeu')"""

c = c.replace(old_parse, new_parse)

with open(r'E:\Projeto MCR\sandbox\mcr_crew.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'mcr_crew.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error: {e}')
