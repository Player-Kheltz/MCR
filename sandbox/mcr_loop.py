#!/usr/bin/env python3
"""
MCR-DevIA — LOOP DE RESOLUCAO (OODA Continuo)
================================================
Cada ciclo:
  1. INICIAR — "O que eu sei?"
  2. PENSAR — "O que esta errado?"
  3. EXECUTAR — "Tentar consertar"
  4. APRENDER — "Funcionou?"
  5. CONSOLIDAR — "O que aprendi?"
  6. REPETIR — Se nao resolveu, volta pro 1.
  
  Nao espera 2 minutos. Bate sem parar ate resolver.
  Quando nao tem nada pra fazer, descansa 10s e verifica de novo.
"""

import sys, os, json, re, urllib.request, datetime, time, subprocess

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'
LOG_PATH = os.path.join(SANDBOX, '.mcr_heartbeat.log')

def log(msg):
    t = datetime.datetime.now().strftime('%H:%M:%S')
    line = f'[{t}] {msg}'
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except: pass
    print(line)

class CicloCompleto:
    """Cada ciclo e uma tentativa completa de aprender e resolver."""
    
    def __init__(self):
        self.ciclo = 0
        self.problema_atual = None
        self.problemas_consecutivos = 0
    
    def rodar(self):
        log('='*50)
        log('MCR-DevIA INICIADO — Modo Resolucao Continua')
        log('='*50)
        
        while True:
            self.ciclo += 1
            resolveu = self._ciclo_unico()
            
            if resolveu:
                log(f'[CICLO {self.ciclo}] Problema resolvido! Descansando 10s...')
                time.sleep(10)
            else:
                log(f'[CICLO {self.ciclo}] Nao resolveu. Tentando de novo IMEDIATAMENTE...')
                time.sleep(1)  # So 1s pra nao sobrecarregar a IA
    
    def _ciclo_unico(self):
        """Um ciclo OODA completo."""
        log(f'')
        log(f'[CICLO {self.ciclo}] {"="*40}')
        
        # 1. INICIAR: carregar estado atual
        log(f'[1/6] INICIAR — Carregando estado...')
        n_licoes, n_reparos, kg = self._carregar_estado()
        log(f'  KG: {n_licoes} licoes | Reparos: {n_reparos}')
        
        # 2. PENSAR: escanear e identificar problemas
        log(f'[2/6] PENSAR — Escaneando projeto...')
        discrepancias = self._pensar()
        
        if not discrepancias:
            log(f'[3/6] DECIDIR — Nada a fazer. Sistema OK.')
            log(f'[4/6] EXECUTAR — Pulando.')
            log(f'[5/6] APRENDER — Nada novo.')
            log(f'[6/6] CONSOLIDAR — Sistema estavel.')
            return True  # Resolveu (nada pra resolver = resolvido)
        
        # 3. DECIDIR: qual problema atacar
        log(f'[3/6] DECIDIR — Problema: {discrepancias[0]["tipo"]}')
        if self.problema_atual == discrepancias[0]['tipo']:
            self.problemas_consecutivos += 1
        else:
            self.problemas_consecutivos = 1
            self.problema_atual = discrepancias[0]['tipo']
        
        log(f'  Tentativa #{self.problemas_consecutivos} de resolver {self.problema_atual}')
        
        # 4. EXECUTAR: tentar resolver
        log(f'[4/6] EXECUTAR — Tentando reparo...')
        resultado = self._executar(discrepancias[0])
        
        # 5. APRENDER: registrar o que aconteceu
        log(f'[5/6] APRENDER — Registrando aprendizado...')
        if resultado:
            log(f'  [OK] Reparo aplicado. Verificando no proximo ciclo.')
        else:
            log(f'  [FALHA] Reparo nao funcionou. Motivo: {resultado}')
        
        # 6. CONSOLIDAR: atualizar KG com o resultado
        log(f'[6/6] CONSOLIDAR — Atualizando conhecimento...')
        if self.problemas_consecutivos >= 3:
            log(f'  [TOQUE] Ja tentei {self.problemas_consecutivos}x resolver {self.problema_atual}.')
            log(f'  [TOQUE] Preciso de uma abordagem DIFERENTE.')
            # Aqui ele poderia tentar uma abordagem alternativa
        
        return resultado
    
    def _carregar_estado(self):
        """Carrega o estado atual do sistema."""
        n_licoes = 0
        n_reparos = 0
        kg = {}
        
        kg_path = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
        if os.path.exists(kg_path):
            try:
                with open(kg_path, 'r', encoding='utf-8', errors='replace') as f:
                    kg = json.load(f)
                n_licoes = len(kg.get('licoes', []))
            except: pass
        
        auto_path = os.path.join(SANDBOX, '.mcr_auto_log.json')
        if os.path.exists(auto_path):
            try:
                with open(auto_path, 'r') as f:
                    n_reparos = len(json.load(f).get('reparos', []))
            except: pass
        
        return n_licoes, n_reparos, kg
    
    def _pensar(self):
        """Escaneia o projeto e encontra discrepancias."""
        padroes = {}
        base = os.path.join(BASE, 'Canary', 'data-canary', 'scripts', 'MCR')
        if not os.path.exists(base): return []
        
        for root, dirs, files in os.walk(base):
            for f in files:
                if not f.endswith('.lua'): continue
                try:
                    with open(os.path.join(root, f), 'r', encoding='utf-8', errors='replace') as fp:
                        conteudo = fp.read()
                    tipo = None
                    if 'Monster(' in conteudo: tipo = 'monster'
                    elif 'Item(' in conteudo: tipo = 'item'
                    elif 'NPC(' in conteudo: tipo = 'npc'
                    if not tipo: continue
                    if tipo not in padroes: padroes[tipo] = {}
                    for m in re.finditer(rf'(?:npc|mon|item):(set\\w+|add\\w+)\(', conteudo):
                        padroes[tipo][m.group(1)] = padroes[tipo].get(m.group(1), 0) + 1
                except: pass
        
        # Compara com templates
        discrepancias = []
        ult_path = os.path.join(SANDBOX, 'mcr_ultimate.py')
        if os.path.exists(ult_path):
            with open(ult_path, 'r', encoding='utf-8', errors='replace') as f:
                ult_conteudo = f.read()
            
            for tipo, funcoes in padroes.items():
                comuns = {f for f,c in funcoes.items() if c >= 2}
                no_template = set(re.findall(rf':(set\\w+|add\\w+)\(', ult_conteudo))
                faltando = comuns - no_template
                if faltando:
                    discrepancias.append({'tipo': tipo, 'faltando': list(faltando)})
        
        return discrepancias
    
    def _executar(self, discrepancia):
        """Tenta executar um reparo."""
        tipo = discrepancia['tipo']
        # Chama IA
        prompt = f"Gere linhas de template para {tipo}: {', '.join(discrepancia['faltando'][:5])}. Formato: mon:nomeFunc(parametro)"
        try:
            d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
                'options':{'temperature':0.5,'num_ctx':4096}}).encode()
            r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
            resp = json.loads(urllib.request.urlopen(r,timeout=30).read()).get('response','')
            if resp and len(resp.strip()) > 5:
                log(f'  IA respondeu. Tentando auto-reparo...')
                subprocess.run([sys.executable, os.path.join(SANDBOX, 'mcr_auto_reparo.py')],
                             capture_output=True, timeout=30)
                return True
        except:
            pass
        return False


if __name__ == '__main__':
    ciclo = CicloCompleto()
    ciclo.rodar()
