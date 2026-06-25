#!/usr/bin/env python3
"""
MCR-DevIA — BATIMENTO CARDIACO (Loop autonomo)
=================================================
O coracao do MCR-DevIA. Bate sozinho.
A cada 5 minutos ele:
  1. Escaneia o projeto (aprendizado passivo)
  2. Compara templates com codigo real
  3. Se houver discrepancia → tenta reparo
  4. Aprende com o resultado
  5. Dorme 5 minutos
  6. Repete

Nao precisa de voce, de mim, de ninguem.
"""

import sys, os, json, re, urllib.request, datetime, time, subprocess

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'
AUTO_LOG = os.path.join(SANDBOX, '.mcr_auto_log.json')
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
HEART_LOG = os.path.join(SANDBOX, '.mcr_heartbeat.log')

def ia(prompt):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':0.5,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=60).read()).get('response','')
    except: return None

def log(msg):
    """Log com timestamp."""
    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{t}] {msg}'
    # Salva no arquivo de log
    try:
        with open(HEART_LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except: pass
    print(line)

class Batimento:
    """O coracao que bate sozinho."""
    
    def __init__(self):
        self.batidas = 0
        self.ultimo_scan = ''
    
    def bater(self):
        """Um ciclo completo do batimento cardiaco."""
        self.batidas += 1
        log(f'--- Batida #{self.batidas} ---')
        
        # 1. Escaneia o projeto
        log('Escaneando projeto...')
        padroes_reais = self._escanear_padroes()
        
        # 2. Verifica templates
        templates = self._carregar_templates()
        discrepancias = self._comparar(padroes_reais, templates)
        
        # 3. Se houver discrepancia, tenta reparo
        if discrepancias:
            log(f'Discrepancia encontrada: {discrepancias[0]["tipo"]}')
            self._tentar_reparo(discrepancias[0])
        else:
            log('Templates atualizados. Nada a reparar.')
        
        # 4. Verifica saude geral
        self._verificar_saude()
        
        log(f'Batida #{self.batidas} concluida.')
    def _escanear_padroes(self):
        """Escaneia o projeto e extrai funcoes SET usadas."""
        padroes = {}
        base_dir = os.path.join(BASE, 'Canary', 'data-canary', 'scripts', 'MCR')
        if not os.path.exists(base_dir): return padroes
        
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                if not f.endswith('.lua'): continue
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8', errors='replace') as fp:
                        conteudo = fp.read()
                    tipo = None
                    if 'Monster(' in conteudo or 'mon:set' in conteudo: tipo = 'monster'
                    elif 'Item(' in conteudo or 'item:set' in conteudo: tipo = 'item'
                    elif 'NPC(' in conteudo or 'npc:set' in conteudo: tipo = 'npc'
                    if not tipo: continue
                    if tipo not in padroes: padroes[tipo] = {}
                    for m in re.finditer(rf'(?:npc|mon|item):(set\w+|add\w+)\(', conteudo):
                        func = m.group(1)
                        padroes[tipo][func] = padroes[tipo].get(func, 0) + 1
                except: pass
        
        for tipo, funcoes in padroes.items():
            comuns = {f:c for f,c in funcoes.items() if c >= 2}
            if comuns:
                log(f'  {tipo}: {", ".join(list(comuns.keys())[:5])}')
        
        return padroes
    
    def _carregar_templates(self):
        """Carrega templates do mcr_ultimate.py (se existir)."""
        path = os.path.join(SANDBOX, 'mcr_ultimate.py')
        if not os.path.exists(path): return {}
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            conteudo = f.read()
        templates = {}
        for tipo in ['npc', 'monster', 'item']:
            m = re.search(rf"'{tipo}':\s*{{[^}}]*'template':\s*'([^']+)'", conteudo, re.DOTALL)
            if m: templates[tipo] = m.group(1)
        return templates
    
    def _comparar(self, padroes, templates):
        """Compara padroes reais com templates."""
        discrepancias = []
        for tipo, funcoes in padroes.items():
            template = templates.get(tipo, '')
            comuns = {f for f,c in funcoes.items() if c >= 2}
            no_template = set(re.findall(f':(set\\w+|add\\w+)\\(', template))
            faltando = comuns - no_template
            if faltando:
                discrepancias.append({'tipo': tipo, 'faltando': list(faltando)})
        return discrepancias
    
    def _tentar_reparo(self, discrepancia):
        """Tenta reparar uma discrepancia."""
        tipo = discrepancia['tipo']
        faltando = discrepancia['faltando']
        log(f'Tentando reparar template de {tipo}...')
        
        # Chama IA pra gerar correcao
        funcs = ', '.join(faltando[:5])
        prompt = f"Gere linhas de template para {tipo}: {funcs}. Formato: mon:nomeFuncao(parametro)"
        novas = ia(prompt)
        
        if novas and len(novas.strip()) > 5:
            log(f'  IA gerou correcao. Atualizando template...')
            # Tenta aplicar (mesma logica do auto-reparo)
            try:
                subprocess.run([sys.executable, os.path.join(SANDBOX, 'mcr_auto_reparo.py')],
                             capture_output=True, timeout=30)
                log(f'  Auto-reparo executado.')
            except: pass
        else:
            log(f'  IA nao respondeu. Reparo adiado.')
    
    def _verificar_saude(self):
        """Verifica metricas de saude."""
        n_licoes = 0
        if os.path.exists(KG_PATH):
            try:
                with open(KG_PATH, 'r', encoding='utf-8', errors='replace') as f:
                    kg = json.load(f)
                n_licoes = len(kg.get('licoes', []))
            except: pass
        
        n_reparos = 0
        if os.path.exists(AUTO_LOG):
            try:
                with open(AUTO_LOG, 'r') as f:
                    n_reparos = len(json.load(f).get('reparos', []))
            except: pass
        
        log(f'Saude: {n_licoes} licoes, {n_reparos} reparos, batida #{self.batidas}')


if __name__ == '__main__':
    coracao = Batimento()
    intervalo = int(sys.argv[1]) * 60 if len(sys.argv) > 1 else 300  # padrao: 5 min
    
    log(f'MCR-DevIA BATIMENTO CARDIACO INICIADO')
    log(f'Intervalo: {intervalo//60} minutos')
    log(f'Aprendendo e se auto-reparando autonomamente...')
    
    try:
        while True:
            coracao.bater()
            time.sleep(intervalo)
    except KeyboardInterrupt:
        log('Batimento cardiaco parado.')
