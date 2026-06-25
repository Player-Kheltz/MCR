#!/usr/bin/env python3
"""
MCR-DevIA — AUTO-REPARO (apenas a si mesmo)
==============================================
Ele MONITORA sua propria geracao.
Se detectar que seus templates estao defasados em relacao ao projeto REAL,
ele SE AUTO-CORRIGE — reescreve seus proprios templates.

Sem interferencia minha. So age dentro de si mesmo.
"""

import sys, os, json, re, urllib.request, datetime, shutil

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
ULTIMATE_PATH = os.path.join(SANDBOX, 'mcr_ultimate.py')
AUTO_LOG = os.path.join(SANDBOX, '.mcr_auto_log.json')

def ia(prompt):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':0.4,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=120).read()).get('response','')
    except: return None


class AutoReparo:
    """
    Monitora a propria geracao e se auto-corrige.
    So mexe em si mesmo (mcr_ultimate.py, KG).
    """
    
    def __init__(self):
        self.log = self._carregar_log()
        self.versoes = self.log.get('versoes', 0)
        print(f'[AUTO-REPARO] Versao {self.versoes}')
    
    def _carregar_log(self):
        if os.path.exists(AUTO_LOG):
            with open(AUTO_LOG, 'r') as f:
                return json.load(f)
        return {'versoes': 0, 'reparos': [], 'auto_aperfeicoamentos': 0}
    
    def _salvar_log(self):
        with open(AUTO_LOG, 'w') as f:
            json.dump(self.log, f, indent=2)
    
    def auto_reparar(self):
        """Ciclo completo de auto-reparo."""
        print('\n[AUTO-REPARO] Iniciando ciclo de auto-verificacao...')
        self.versoes += 1
        self.log['versoes'] = self.versoes
        
        # 1. Escaneia padroes reais do projeto
        padroes_reais = self._escanear_padroes_reais()
        
        # 2. Carrega templates atuais
        templates_atuais = self._carregar_templates_atuais()
        
        # 3. Compara e identifica discrepancias
        discrepancias = self._comparar(padroes_reais, templates_atuais)
        
        # 4. Se houver discrepancias, auto-corrige
        if discrepancias:
            print(f'\n  Discrepancias encontradas: {len(discrepancias)}')
            self._auto_corrigir(discrepancias)
        else:
            print('\n  Nenhuma discrepancia. Templates atualizados.')
        
        # 5. Relatorio
        print(f'\n  Auto-reparos realizados: {self.log["auto_aperfeicoamentos"]}')
        self._salvar_log()
    
    def _escanear_padroes_reais(self):
        """Escaneia projeto e extrai funcoes SET usadas em cada tipo."""
        print('\n[1/4] Escaneando padroes reais do projeto...')
        padroes = {}
        
        for root, dirs, files in os.walk(os.path.join(BASE, 'Canary', 'data-canary', 'scripts', 'MCR')):
            for f in files:
                if not f.endswith('.lua'): continue
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8', errors='replace') as fp:
                        conteudo = fp.read()
                    
                    # Detecta tipo
                    tipo = None
                    if re.search(r'NPC\(|npc:setSaudacao', conteudo): tipo = 'npc'
                    elif re.search(r'Monster\(|mon:setHealth', conteudo): tipo = 'monster'
                    elif re.search(r'Item\(|item:setType', conteudo): tipo = 'item'
                    
                    if not tipo: continue
                    
                    if tipo not in padroes: padroes[tipo] = {}
                    
                    for m in re.finditer(rf'(?:npc|mon|item):(set\w+|add\w+)\(', conteudo):
                        func = m.group(1)
                        padroes[tipo][func] = padroes[tipo].get(func, 0) + 1
                except: pass
        
        for tipo, funcoes in padroes.items():
            comuns = {f:c for f,c in funcoes.items() if c >= 2}
            print(f'  {tipo}: {len(comuns)} funcoes comuns - {", ".join(list(comuns.keys())[:5])}')
        
        return padroes
    
    def _carregar_templates_atuais(self):
        """Carrega os templates do mcr_ultimate.py."""
        print('\n[2/4] Carregando templates atuais...')
        if not os.path.exists(ULTIMATE_PATH):
            print('  mcr_ultimate.py nao encontrado')
            return {}
        
        with open(ULTIMATE_PATH, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Extrai templates do dicionario TEMPLATES
        templates = {}
        for tipo in ['npc', 'monster', 'item', 'quest', 'spell']:
            m = re.search(rf"'{tipo}':\s*{{[^}}]*'template':\s*'([^']+)'", conteudo, re.DOTALL)
            if m:
                templates[tipo] = m.group(1)
                print(f'  {tipo}: template carregado')
        
        return templates
    
    def _comparar(self, padroes_reais, templates_atuais):
        """Compara padroes reais com templates e identifica o que falta."""
        print('\n[3/4] Comparando templates com padroes reais...')
        discrepancias = []
        
        for tipo, funcoes_reais in padroes_reais.items():
            template = templates_atuais.get(tipo, '')
            
            # Funcoes que o projeto real USA (2+ ocorrencias)
            funcoes_comuns = {f for f, c in funcoes_reais.items() if c >= 2}
            
            # Funcoes que o template TEM
            funcoes_no_template = set(re.findall(f':(set\\w+|add\\w+)\\(', template))
            
            # Funcoes FALTANDO no template
            faltando = funcoes_comuns - funcoes_no_template
            
            if faltando:
                discrepancias.append({
                    'tipo': tipo,
                    'faltando': list(faltando),
                    'funcoes_reais': funcoes_reais,
                })
                print(f'  {tipo}: faltam {len(faltando)} funcoes - {", ".join(list(faltando)[:5])}')
            else:
                print(f'  {tipo}: completo')
        
        return discrepancias
    
    def _auto_corrigir(self, discrepancias):
        """Auto-corrige os templates no mcr_ultimate.py."""
        print('\n[4/4] Auto-corrigindo templates...')
        
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
            
            print(f'\n  Corrigindo {tipo}...')
            
            # Encontra e insere no template
            padrao = re.compile(r"'" + str(tipo) + r"':\s*\{\s*'template':\s*'([^']+)'")
            m = padrao.search(conteudo)
            if m:
                template_atual = m.group(1)
                novas = '\n'.join([l.strip() for l in novas_linhas.split('\n') if l.strip() and '```' not in l])
                novo_template = template_atual + '\n' + novas
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
        print(f'\n  mcr_ultimate.py atualizado!')
        self._alimentar_kg(discrepancias)
    def _alimentar_kg(self, discrepancias):
        """Registra o aprendizado no Knowledge Graph."""
        if not os.path.exists(KG_PATH): return
        
        with open(KG_PATH, 'r', encoding='utf-8') as f:
            kg = json.load(f)
        
        for item in discrepancias:
            kg['licoes'].append({
                'id': f'AR{len(kg["licoes"])+1:04d}',
                'erro': f'Template de {item["tipo"]} desatualizado no mcr_ultimate.py',
                'causa': f'Faltavam {len(item["faltando"])} funcoes usadas no projeto real',
                'solucao': f'Adicionadas: {", ".join(item["faltando"][:5])}',
                'ctx': 'auto_reparo',
                'usos': 0,
            })
        
        kg['versoes'] += 1
        with open(KG_PATH, 'w', encoding='utf-8') as f:
            json.dump(kg, f, ensure_ascii=False, indent=2)
        print(f'  KG atualizado: {len(kg["licoes"])} licoes')
    
    def status(self):
        print(f'\n[AUTO-REPARO] Status:')
        print(f'  Versao: {self.versoes}')
        print(f'  Reparos realizados: {self.log["auto_aperfeicoamentos"]}')
        print(f'  Ultimos reparos:')
        for r in self.log.get('reparos', [])[-3:]:
            print(f'    V{r["versao"]}: {r["tipo"]} +{len(r["funcoes_adicionadas"])} funcoes ({r["data"]})')


if __name__ == '__main__':
    reparo = AutoReparo()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--status':
        reparo.status()
    else:
        reparo.auto_reparar()
