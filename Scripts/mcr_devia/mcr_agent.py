#!/usr/bin/env python3
"""
MCR-DevIA AGENT — Modo Agente Autonomo
=========================================
Nao espera voce pedir. Ele VIGIA, DECIDE e AGE.

O que faz:
  - Escaneia logs de erro do servidor (canary-sln.exe)
  - Aprende erros novos automaticamente
  - Sugere correcoes proativas
  - Valida arquivos gerados na sandbox
  - Reporta problemas antes de voce perceber

Uso: python mcr_agent.py --scan          (escaneia uma vez)
     python mcr_agent.py --watch         (fica vigiando)
     python mcr_agent.py --daemon        (modo servico)
     python mcr_agent.py --report        (relatorio de saude)
"""

import sys, os, json, re, urllib.request, hashlib, datetime, time, subprocess

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
AGENT_LOG = os.path.join(SANDBOX, '.mcr_agent_log.json')

# ============================================================
# CONHECIMENTO
# ============================================================

class KG:
    def __init__(self):
        self.path = KG_PATH; self.data = self._load()
    def _load(self):
        if os.path.exists(self.path):
            with open(self.path,'r',encoding='utf-8') as f: return json.load(f)
        return {'versoes':0,'licoes':[],'metricas':{'licoes':0}}
    def salvar(self):
        self.data['versoes'] += 1; self.data['metricas']['licoes'] = len(self.data['licoes'])
        with open(self.path,'w',encoding='utf-8') as f: json.dump(self.data,f,ensure_ascii=False,indent=2)
    def aprender(self, erro, causa, sol, ctx='agent'):
        self.data['licoes'].append({'id':f'A{len(self.data["licoes"])+1:04d}','erro':erro,'causa':causa,'solucao':sol,'ctx':ctx,'usos':0})
        self.salvar()
        return f'Aprendido: {erro[:50]}'

class IA:
    def gerar(self, prompt, temp=0.5):
        try:
            from modulos.util import gerar as _gerar_ag
            return _gerar_ag(prompt, temp, "pesado") or ""
        except Exception as e:
            print(f"[Fix] ERRO: {e}")


# ============================================================
# AGENTE
# ============================================================

class Agente:
    def __init__(self):
        self.kg = KG()
        self.ia = IA()
        self.log = self._carregar_log()
    
    def _carregar_log(self):
        if os.path.exists(AGENT_LOG):
            with open(AGENT_LOG,'r',encoding='utf-8') as f: return json.load(f)
        return {'execucoes':0,'acoes':0, 'problemas':[], 'solucoes':[]}
    
    def _salvar_log(self):
        with open(AGENT_LOG,'w',encoding='utf-8') as f: json.dump(self.log,f,ensure_ascii=False,indent=2)
    
    def escanear_logs_servidor(self):
        """Escaneia logs do servidor em busca de erros."""
        logs_path = os.path.join(BASE, 'Canary', 'startup_log.txt')
        if not os.path.exists(logs_path): return []
        
        erros = []
        with open(logs_path,'r',encoding='utf-8',errors='replace') as f:
            for line in f:
                if 'error' in line.lower() or 'Erro' in line or 'fail' in line.lower():
                    erros.append(line.strip())
        return erros[:10]
    
    def escanear_sandbox(self):
        """Escaneia sandbox por arquivos recentes."""
        agora = datetime.datetime.now()
        limite = agora - datetime.timedelta(hours=24)
        arquivos = []
        for f in os.listdir(SANDBOX):
            path = os.path.join(SANDBOX, f)
            if os.path.isfile(path):
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
                if mtime > limite and f.endswith(('.lua','.txt','.otui')):
                    arquivos.append({'nome':f, 'modificado':str(mtime)[:19], 'tamanho':os.path.getsize(path)})
        return arquivos
    
    def validar_arquivos(self, arquivos):
        """Valida arquivos Lua gerados."""
        problemas = []
        for arq in arquivos:
            if not arq['nome'].endswith('.lua'): continue
            path = os.path.join(SANDBOX, arq['nome'])
            try:
                with open(path,'r',encoding='utf-8') as f: conteudo = f.read()
                opens = conteudo.count('{') + conteudo.count('(')
                closes = conteudo.count('}') + conteudo.count(')')
                if opens != closes:
                    problemas.append(f'{arq["nome"]}: chaves desbalanceadas ({opens}/{closes})')
            except Exception as e:
                problemas.append(f'{arq["nome"]}: erro de leitura - {e}')
        return problemas
    
    def analisar_erro_com_ia(self, erro):
        """IA analisa um erro desconhecido."""
        if not self.ia: return 'IA indisponivel'
        prompt = f"Analise este erro e sugira causa e solucao:\n\nERRO: {erro[:300]}\n\nResponda:\nCAUSA:\nSOLUCAO:\n"
        r = self.ia.gerar(prompt, 0.4)
        causa = ''; sol = ''
        if r:
            for line in r.split('\n'):
                if 'CAUSA:' in line: causa = line.split(':',1)[1].strip()
                elif 'SOLUCAO:' in line: sol = line.split(':',1)[1].strip()
        return causa, sol
    
    def executar_ciclo(self):
        """Um ciclo completo do agente."""
        print(f'\n[AGENTE] Ciclo #{self.log["execucoes"]+1} - {str(datetime.datetime.now())[:19]}')
        self.log['execucoes'] += 1
        acoes = 0
        
        # 1. Escanear logs do servidor
        erros = self.escanear_logs_servidor()
        if erros:
            print(f'  Logs: {len(erros)} erros encontrados')
            for erro in erros[:3]:
                # Verifica se ja conhece
                conhecido = False
                for l in self.kg.data['licoes']:
                    if any(p in erro.lower() for p in l.get('erro','').lower().split()[:3]):
                        conhecido = True
                        break
                if not conhecido:
                    if self.ia:
                        causa, sol = self.analisar_erro_com_ia(erro)
                        if causa and sol:
                            self.kg.aprender(erro[:80], causa, sol, 'agent_scan')
                            acoes += 1
                            self.log['solucoes'].append({'erro':erro[:80],'causa':causa,'data':str(datetime.datetime.now())[:19]})
                            print(f'    Novo erro aprendido!')
        
        # 2. Escanear sandbox
        arquivos = self.escanear_sandbox()
        if arquivos:
            print(f'  Sandbox: {len(arquivos)} arquivos recentes')
            problemas = self.validar_arquivos(arquivos)
            for p in problemas:
                print(f'    Problema: {p}')
                self.log['problemas'].append({'problema':p,'data':str(datetime.datetime.now())[:19]})
                acoes += 1
        
        # 3. Verificar saude do KG
        n_licoes = len(self.kg.data['licoes'])
        print(f'  KG: {n_licoes} licoes, V{self.kg.data["versoes"]}')
        
        self.log['acoes'] += acoes
        self._salvar_log()
        return acoes
    
    def relatorio(self):
        """Relatorio de saude do projeto."""
        print(f'\n{"="*60}')
        print(f'  RELATORIO DO AGENTE MCR-DevIA')
        print(f'{"="*60}')
        print(f'  Execucoes: {self.log["execucoes"]}')
        print(f'  Acoes tomadas: {self.log["acoes"]}')
        print(f'  Problemas encontrados: {len(self.log["problemas"])}')
        print(f'  Solucoes aprendidas: {len(self.log["solucoes"])}')
        print(f'  Knowledge Graph: {len(self.kg.data["licoes"])} licoes (V{self.kg.data["versoes"]})')
        
        if self.log['problemas']:
            print(f'\n  Ultimos problemas:')
            for p in self.log['problemas'][-5:]:
                print(f'    {p["problema"]} ({p["data"]})')
        
        if self.log['solucoes']:
            print(f'\n  Ultimas solucoes:')
            for s in self.log['solucoes'][-5:]:
                print(f'    {s["erro"]} -> {s["causa"][:40]}...')
        
        print(f'\n  Saude do projeto: ', end='')
        problemas_recentes = [p for p in self.log['problemas'] if '24h' not in str(datetime.datetime.now() - datetime.timedelta(hours=24))]
        if len(problemas_recentes) < 3:
            print('[OK]')
        else:
            print(f'{len(problemas_recentes)} problemas recentes')
        
        print(f'{"="*60}')


# ============================================================
# MAIN
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--scan', action='store_true', help='Escaneia uma vez')
    parser.add_argument('--watch', action='store_true', help='Fica vigiando')
    parser.add_argument('--daemon', type=int, default=0, help='Intervalo em minutos')
    parser.add_argument('--report', action='store_true', help='Relatorio de saude')
    args = parser.parse_args()
    
    agente = Agente()
    
    if args.report:
        agente.relatorio()
        return
    
    if args.scan:
        agente.executar_ciclo()
        agente.relatorio()
        return
    
    if args.watch or args.daemon:
        intervalo = args.daemon * 60 if args.daemon else 300
        print(f'[AGENTE] Vigiando a cada {intervalo}s. Ctrl+C para parar.')
        try:
            while True:
                agente.executar_ciclo()
                time.sleep(intervalo)
        except KeyboardInterrupt:
            print('\n[AGENTE] Parou.')
        return
    
    print('MCR-DevIA AGENT - Modo Autonomo')
    print()
    print('Comandos:')
    print('  --scan        Escaneia uma vez e reporta')
    print('  --watch       Fica vigiando (a cada 5min)')
    print('  --daemon N    Vigiando a cada N minutos')
    print('  --report      Relatorio de saude')
    print()
    print('Ex: python mcr_agent.py --scan')
    print('    python mcr_agent.py --daemon 10')

if __name__ == '__main__':
    main()
