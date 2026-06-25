#!/usr/bin/env python3
"""
AUDITORIA CLOUD — Independente, sem ver resultados do MCR-DevIA
================================================================
Eu (cloud) vasculho o projeto com MEUS proprios criterios.
"""

import sys, os, json, re, datetime

BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'

class AuditorCloud:
    def __init__(self):
        self.resultados = []
        self.total_arquivos = 0
    
    def add(self, tipo, severidade, arquivo, detalhe):
        self.resultados.append({
            'tipo': tipo, 'severidade': severidade,
            'arquivo': arquivo, 'detalhe': detalhe[:120],
        })
    
    def auditar(self):
        print('[AUDITOR CLOUD] Auditoria independente...\n')
        
        # 1. Health check dos scripts principais
        print('[1/6] Scripts principais...')
        principais = ['mcr_devia.py', 'mcr_chat.py', 'mcr_agent.py', 'mcr_ultimate.py',
                      'pista_a.py', 'pista_b.py', 'mcr_auditor.py', 'mcr_supervisor.py',
                      'mcr_builder_v2.py', 'mcr_env.py', 'mcr_autobuild.py']
        for p in principais:
            path = os.path.join(SANDBOX, p)
            if os.path.exists(path):
                size = os.path.getsize(path)
                if size < 1000:
                    self.add('tamanho', 'MEDIA', p, f'Muito pequeno ({size} bytes)')
                elif size > 50000:
                    self.add('tamanho', 'INFO', p, f'Muito grande ({size//1000}KB)')
            else:
                self.add('ausente', 'ALTA', p, 'Nao encontrado')
        print(f'  {len(principais)} scripts verificados')
        
        # 2. Conexoes entre modulos
        print('[2/6] Dependencias entre modulos...')
        for p in principais:
            path = os.path.join(SANDBOX, p)
            if not os.path.exists(path): continue
            with open(path,'r',encoding='utf-8',errors='replace') as f:
                conteudo = f.read()
            # Verifica se importa de outros modulos
            imports = re.findall(r'(?:from|import)\s+(\w+)', conteudo)
            for imp in imports:
                if imp not in ('sys','os','json','re','subprocess','urllib','hashlib','datetime','time','glob','math','random','shutil','textwrap','argparse'):
                    self.add('dependencia', 'INFO', p, f'Importa: {imp}')
        print(f'  Dependencias mapeadas')
        
        # 3. Qualidade dos templates
        print('[3/6] Qualidade dos templates...')
        for root, dirs, files in os.walk(os.path.join(BASE, 'Canary', 'data-canary', 'scripts', 'MCR', 'SPA', 'habilidades')):
            for f in files:
                if not f.endswith('.lua'): continue
                path = os.path.join(root, f)
                with open(path,'r',encoding='utf-8',errors='replace') as fp:
                    conteudo = fp.read()
                # Verifica HABILIDADES[n] = { tem chave fechada correspondente
                opens = conteudo.count('{')
                closes = conteudo.count('}')
                if opens != closes:
                    diff = opens - closes
                    self.add('sintaxe', 'ALTA', f'spa/habilidades/{f}', f'Chaves: {opens}/{closes} (diff {diff})')
        print(f'  Templates verificados')
        
        # 4. Qualidade dos arquivos gerados (sandbox)
        print('[4/6] Arquivos na sandbox...')
        arquivos_lua = [f for f in os.listdir(SANDBOX) if f.endswith('.lua')]
        for f in arquivos_lua:
            path = os.path.join(SANDBOX, f)
            with open(path,'r',encoding='utf-8',errors='replace') as fp:
                conteudo = fp.read()
            # Verifica se tem conteudo ou so template vazio
            if len(conteudo) < 50:
                self.add('qualidade', 'BAIXA', f, 'Arquivo muito pequeno')
            # Verifica placeholders nao preenchidos
            if '{' in conteudo and '}' in conteudo and 'nome' in conteudo:
                if '{nome}' in conteudo or '{saudacao}' in conteudo:
                    self.add('template', 'ALTA', f, 'Placeholder nao preenchido')
        print(f'  {len(arquivos_lua)} arquivos .lua verificados')
        
        # 5. Erros conhecidos nao corrigidos
        print('[5/6] Erros conhecidos...')
        # Logs do servidor
        log_path = os.path.join(BASE, 'Canary', 'startup_log.txt')
        if os.path.exists(log_path):
            with open(log_path,'r',encoding='utf-8',errors='replace') as f:
                log_content = f.read()
            erros_passiva = re.findall(r'Erro ao aplicar passiva \d+', log_content)
            if erros_passiva:
                self.add('runtime', 'MEDIA', 'startup_log.txt', f'{len(erros_passiva)} erros de passiva')
        print(f'  Logs verificados')
        
        # 6. Knowledge Graph
        print('[6/6] Knowledge Graph...')
        kg_path = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
        if os.path.exists(kg_path):
            with open(kg_path,'r',encoding='utf-8') as f: kg = json.load(f)
            self.add('kg', 'INFO', 'KG', f'{len(kg["licoes"])} licoes, V{kg["versoes"]}')
            # Verifica licoes irmas (duplicadas)
            erros = [l['erro'] for l in kg['licoes']]
            if len(erros) != len(set(erros)):
                self.add('kg', 'BAIXA', 'KG', 'Licoes duplicadas')
        print(f'  KG verificado')
        
        return self.resultados
    
    def relatorio(self):
        print(f'\n{"="*60}')
        print(f'  RELATORIO DO AUDITOR CLOUD')
        print(f'  Total: {len(self.resultados)} itens encontrados')
        print(f'{"="*60}')
        
        for severidade in ['ALTA','MEDIA','BAIXA','INFO']:
            itens = [r for r in self.resultados if r['severidade'] == severidade]
            if itens:
                print(f'\n  [{severidade}] {len(itens)} itens:')
                for item in itens[:8]:
                    print(f'    {item["tipo"]}: {item["detalhe"][:100]}')
                    if item['arquivo']: print(f'      -> {item["arquivo"]}')
                if len(itens) > 8:
                    print(f'    ... e mais {len(itens)-8}')
        
        print(f'\n  Resumo:')
        for s in ['ALTA','MEDIA','BAIXA','INFO']:
            print(f'    {s}: {len([r for r in self.resultados if r["severidade"]==s])}')
        
        path = os.path.join(SANDBOX, '.mcr_auditoria_cloud.json')
        with open(path,'w',encoding='utf-8') as f: json.dump(self.resultados,f,ensure_ascii=False,indent=2)
        print(f'\n  Salvo em: {path}')
        print(f'{"="*60}')


if __name__ == '__main__':
    a = AuditorCloud()
    a.auditar()
    a.relatorio()
