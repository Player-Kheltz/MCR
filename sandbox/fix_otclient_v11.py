"""Fix OTClient module with template approach"""
with open(r'E:\Projeto MCR\sandbox\mcr_crew_v11.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the entire ModuloOTClient class and replace it
start = c.find("class ModuloOTClient(ModuloBase):")
end = c.find("\nclass ModuloNPC(ModuloBase):")

new_class = '''class ModuloOTClient(ModuloBase):
    """OTClient com template Python + IA criativa."""
    def executar(self, args):
        nome = args[0] if args else 'MinhaJanela'
        print(f'\\n[OTClient] Criando {nome}...')
        
        # IA gera APENAS os valores criativos
        p = self.prompt(
            "Defina os widgets para uma janela OTClient.",
            "TITULO: texto da janela\\nLABELS: label1, label2\\nBOTOES: botao1, botao2\\nLARGURA: numero\\nALTURA: numero"
        )
        r = self.ia.gerar(p, 0.7)
        
        if r:
            titulo = 'Janela'
            labels = ['Texto']
            botoes = ['Clique']
            largura = 300
            altura = 200
            
            for line in r.split('\\n'):
                line = line.strip()
                upper = line.upper()
                if upper.startswith('TITULO:'): titulo = line.split(':',1)[1].strip()
                elif upper.startswith('LABELS:'): 
                    labels = [x.strip() for x in line.split(':',1)[1].split(',') if x.strip()]
                elif upper.startswith('BOTOES:'):
                    botoes = [x.strip() for x in line.split(':',1)[1].split(',') if x.strip()]
                elif upper.startswith('LARGURA:'):
                    try: largura = int(re.search(r'\\d+', line).group())
                    except: pass
                elif upper.startswith('ALTURA:'):
                    try: altura = int(re.search(r'\\d+', line).group())
                    except: pass
            
            # Python monta o OTUI com template
            lines = []
            lines.append('<OTUI>')
            lines.append(f'  <Window name="{nome}" title="{titulo}">')
            lines.append(f'    <Panel name="main" width="{largura}" height="{altura}">')
            
            y = 10
            for i, label in enumerate(labels):
                lines.append(f'      <Label text="{label}" x="10" y="{y}" width="{largura-20}" height="30"/>')
                y += 35
            
            for i, botao in enumerate(botoes):
                lines.append(f'      <Button text="{botao}" x="10" y="{y}" width="100" height="30">')
                lines.append(f'        <onClick> {nome}.on{i}() </onClick>')
                lines.append(f'      </Button>')
                y += 40
            
            lines.append('    </Panel>')
            lines.append('  </Window>')
            lines.append('</OTUI>')
            otui = '\\n'.join(lines)
            
            path = f'E:\\Projeto MCR\\sandbox\\otclient_{nome}\\{nome}.otui'
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(otui)
            print(f'  [OK] OTUI gerado: {nome} ({len(labels)} labels, {len(botoes)} botoes)')
            self.fp.registrar(nome, 'acerto')
        else:
            print(f'  [ERRO] IA nao respondeu')
            self.fp.registrar(f'OTClient:{nome}', 'erro')
        print('  [CONCLUIDO]')
'''

c = c[:start] + new_class + c[end:]

with open(r'E:\Projeto MCR\sandbox\mcr_crew_v11.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'v11.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
