#!/usr/bin/env python3
"""
MCR-DevIA AGENT V2 — Contextual + Args
=========================================
Aprendeu a ser contextual. Agora ele PRIORIZA.

Args definem o contexto:
  --escopo  rapido|completo   (o quanto escanear)
  --foco    sintaxe|runtime|estilo|tudo  (o que importa)
  --urgencia alta|media|baixa  (so o que importa agora)
  --aprender                  (aprende com o que voce prioriza)

Uso: python mcr_agent_v2.py --escopo rapido --foco sintaxe
     python mcr_agent_v2.py --escopo completo --foco runtime
     python mcr_agent_v2.py --aprender "chaves" "ALTA"
"""

import sys, os, json, re, datetime, argparse

BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
PRIORIDADES_PATH = os.path.join(SANDBOX, '.mcr_prioridades.json')

class ContextoAgent:
    """Agente que aprende a priorizar com args."""
    
    def __init__(self, args):
        self.args = args
        self.prioridades = self._carregar_prioridades()
        self.resultados = []
    
    def _carregar_prioridades(self):
        """Carrega prioridades que aprendeu."""
        if os.path.exists(PRIORIDADES_PATH):
            with open(PRIORIDADES_PATH,'r',encoding='utf-8') as f:
                return json.load(f)
        # Prioridades INICIAIS (o que o Cloud considera importante)
        return {
            'sempre_alta': ['chaves_desbalanceadas', 'erro_runtime', 'template_quebrado'],
            'sempre_baixa': ['print_debug', 'linha_longa', 'arquivo_grande'],
            'aprendidas': {},
            'metricas': {'vezes_usado': 0},
        }
    
    def salvar_prioridades(self):
        self.prioridades['metricas']['vezes_usado'] += 1
        with open(PRIORIDADES_PATH,'w',encoding='utf-8') as f:
            json.dump(self.prioridades,f,ensure_ascii=False,indent=2)
    
    def aprender_prioridade(self, tipo, severidade):
        """Aprende que um tipo de problema tem certa prioridade."""
        if tipo not in self.prioridades['sempre_alta'] and tipo not in self.prioridades['sempre_baixa']:
            self.prioridades['aprendidas'][tipo] = severidade
            self.salvar_prioridades()
            print(f'  [APRENDI] {tipo} -> {severidade}')
    
    def classificar(self, tipo, severidade_padrao):
        """Classifica um item de acordo com o que aprendeu."""
        if tipo in self.prioridades['sempre_alta']: return 'ALTA'
        if tipo in self.prioridades['sempre_baixa']: return 'BAIXA'
        if tipo in self.prioridades.get('aprendidas', {}):
            return self.prioridades['aprendidas'][tipo]
        return severidade_padrao
    
    def adicionar(self, tipo, severidade, arquivo, detalhe):
        """Adiciona um item ja classificado pelo contexto."""
        severidade_real = self.classificar(tipo, severidade)
        
        # Filtra por urgencia
        if self.args.urgencia:
            niveis = {'alta':0, 'media':1, 'baixa':2}
            if niveis.get(severidade_real.lower(), 0) > niveis.get(self.args.urgencia, 0):
                return  # Pula se for menos urgente que o minimo
        
        # Filtra por foco
        if self.args.foco != 'tudo' and tipo != self.args.foco:
            return
        
        self.resultados.append({
            'tipo': tipo, 'severidade': severidade_real,
            'arquivo': arquivo, 'detalhe': detalhe[:120],
        })
    
    def escanear(self):
        """Escaneia com o escopo definido."""
        print(f'\n[AGENTE V2] Contexto: escopo={self.args.escopo}, foco={self.args.foco}, urgencia={self.args.urgencia or "todas"}')
        print(f'  Prioridades: {len(self.prioridades["sempre_alta"])} sempre altas, {len(self.prioridades["sempre_baixa"])} sempre baixas')
        
        # Escopo RAPIDO: so os scripts principais
        if self.args.escopo == 'rapido':
            scripts = ['mcr_devia.py','mcr_chat.py','mcr_agent.py','mcr_ultimate.py',
                      'mcr_agent_v2.py','mcr_auditor.py']
            for s in scripts:
                path = os.path.join(SANDBOX, s)
                if not os.path.exists(path):
                    self.adicionar('arquivo_ausente', 'ALTA', s, 'Arquivo nao encontrado')
            
            # Health check do KG
            kg_path = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
            if os.path.exists(kg_path):
                with open(kg_path,'r',encoding='utf-8') as f: kg = json.load(f)
                self.adicionar('kg', 'INFO', 'KG', f'{len(kg["licoes"])} licoes')
            
            print(f'  Escopo rapido: {len(self.resultados)} itens')
            return self.resultados
        
        # Escopo COMPLETO: escaneia TUDO
        print('  Escopo completo: escaneando...')
        
        # Scripts MCR
        base = os.path.join(BASE, 'Canary', 'data-canary', 'scripts', 'MCR')
        if os.path.exists(base):
            for root, dirs, files in os.walk(base):
                for f in files:
                    if not f.endswith('.lua'): continue
                    path = os.path.join(root, f)
                    try:
                        with open(path,'r',encoding='utf-8',errors='replace') as fp:
                            conteudo = fp.read()
                        opens, closes = conteudo.count('{'), conteudo.count('}')
                        if opens != closes:
                            self.adicionar('chaves_desbalanceadas', 'ALTA', path.replace(BASE,''), f'{opens}/{closes}')
                        if 'TODO' in conteudo or 'FIXME' in conteudo:
                            self.adicionar('todo_fixme', 'MEDIA', path.replace(BASE,''), 'Codigo nao finalizado')
                        if 'print(' in conteudo and 'DEBUG' in conteudo:
                            self.adicionar('print_debug', 'BAIXA', path.replace(BASE,''), 'Debug esquecido')
                    except: pass
        
        # Logs
        log_path = os.path.join(BASE, 'Canary', 'startup_log.txt')
        if os.path.exists(log_path):
            with open(log_path,'r',encoding='utf-8',errors='replace') as f:
                log = f.read()
            erros_passiva = len(re.findall(r'Erro ao aplicar passiva', log))
            if erros_passiva:
                self.adicionar('erro_runtime', 'ALTA', 'startup_log.txt', f'{erros_passiva} erros de passiva')
        
        print(f'  Escopo completo: {len(self.resultados)} itens')
        return self.resultados


def main():
    parser = argparse.ArgumentParser(description='MCR-DevIA Agent V2 - Contextual')
    parser.add_argument('--escopo', choices=['rapido','completo'], default='rapido')
    parser.add_argument('--foco', choices=['sintaxe','runtime','estilo','tudo'], default='tudo')
    parser.add_argument('--urgencia', choices=['alta','media','baixa'], help='Filtrar por urgencia minima')
    parser.add_argument('--aprender', nargs=2, metavar=('TIPO','SEVERIDADE'), help='Ensinar prioridade')
    args = parser.parse_args()
    
    if args.aprender:
        # Modo aprendizado
        prioridades = {}
        if os.path.exists(PRIORIDADES_PATH):
            with open(PRIORIDADES_PATH,'r',encoding='utf-8') as f:
                prioridades = json.load(f)
        prioridades.setdefault('aprendidas', {})[args.aprender[0]] = args.aprender[1].upper()
        with open(PRIORIDADES_PATH,'w',encoding='utf-8') as f:
            json.dump(prioridades,f,ensure_ascii=False,indent=2)
        print(f'Aprendido: {args.aprender[0]} -> {args.aprender[1].upper()}')
        return
    
    agent = ContextoAgent(args)
    agent.escanear()
    
    print(f'\n{"="*60}')
    print(f'  RESULTADO: {len(agent.resultados)} itens')
    print(f'{"="*60}')
    
    for severidade in ['ALTA','MEDIA','BAIXA','INFO']:
        itens = [r for r in agent.resultados if r['severidade'] == severidade]
        if itens:
            print(f'\n  [{severidade}] {len(itens)} itens:')
            for item in itens[:5]:
                print(f'    {item["tipo"]}: {item["detalhe"][:100]}')
                print(f'      -> {item["arquivo"]}')
            if len(itens) > 5:
                print(f'    ... e mais {len(itens)-5}')
    
    agent.salvar_prioridades()

if __name__ == '__main__':
    main()
