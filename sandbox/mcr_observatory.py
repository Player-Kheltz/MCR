#!/usr/bin/env python3
"""
MCR-DevIA OBSERVATORY — Narrador em Tempo Real
=================================================
Um terminal vivo que mostra o que o MCR-DevIA esta pensando,
aprendendo, errando e descobrindo.

Funciona como um documentario:
  "MCR-DevIA esta escaneando o projeto..."
  "Ele percebeu que o template de monster esta desatualizado..."
  "Tentou se corrigir mas algo deu errado..."
  
Voce pode digitar perguntas enquanto ele trabalha.
"""

import sys, os, json, re, urllib.request, datetime, time, threading

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'
AUTO_LOG = os.path.join(SANDBOX, '.mcr_auto_log.json')
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')

def ia(prompt, temp=0.7):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':temp,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=60).read()).get('response','')
    except: return None


class Narrador:
    """
    Observa o MCR-DevIA e narra em tempo real.
    Ponte entre o sistema e o usuario.
    """
    
    def __init__(self):
        self.ultimo_estado = {}
        self.interacoes = 0
    
    def observar_e_narrar(self):
        """Um ciclo de observacao com narracao."""
        
        # 1. Verifica o que mudou no log de auto-reparo
        reparos = []
        if os.path.exists(AUTO_LOG):
            with open(AUTO_LOG, 'r') as f:
                log = json.load(f)
            reparos = log.get('reparos', [])
        
        # 2. Verifica o KG
        n_licoes = 0
        if os.path.exists(KG_PATH):
            try:
                with open(KG_PATH, 'r', encoding='utf-8', errors='replace') as f:
                    kg = json.load(f)
                n_licoes = len(kg.get('licoes', []))
            except: pass
        
        # 3. Gera a narracao
        novos_reparos = [r for r in reparos if r not in self.ultimo_estado.get('reparos_anteriores', [])]
        
        if novos_reparos:
            ultimo = novos_reparos[-1]
            if ultimo.get('resultado') == 'sucesso':
                self._narrar(f"MCR-DevIA conseguiu se reparar! Atualizou o template de {ultimo['tipo']} com {len(ultimo.get('funcoes_adicionadas',[]))} novas funcoes.")
            elif ultimo.get('resultado') == 'falha':
                self._narrar(f"MCR-DevIA tentou se reparar mas falhou: {ultimo.get('motivo','motivo desconhecido')}. Parece que ele precisa entender melhor o formato do arquivo.")
            else:
                self._narrar(f"MCR-DevIA fez {len(reparos)} tentativas de auto-reparo, mas nenhuma com resultado registrado. Talvez a IA nao esteja respondendo.")
        
        # Narracao periodica
        if self.interacoes % 6 == 0:  # A cada ~3 minutos
            prompt = f"MCR-DevIA tem {n_licoes} licoes de conhecimento. Teve {len(reparos)} tentativas de auto-reparo. Narre o estado atual dele em 1 paragrafo curto e interessante, como se fosse um documentario."
            narracao = ia(prompt, 0.8)
            if narracao:
                self._narrar(narracao[:300])
        
        self.ultimo_estado['reparos_anteriores'] = reparos
        self.interacoes += 1
    
    def _narrar(self, texto):
        """Narra com timestamp."""
        agora = datetime.datetime.now().strftime('%H:%M:%S')
        print(f'\n[{agora}] {texto}')
    
    def responder_pergunta(self, pergunta):
        """Responde a perguntas do usuario sobre o estado do sistema."""
        
        # Prepara contexto
        ctx = []
        if os.path.exists(KG_PATH):
            try:
                with open(KG_PATH, 'r', encoding='utf-8', errors='replace') as f:
                    kg = json.load(f)
                ctx.append(f"Knowledge Graph: {len(kg['licoes'])} licoes")
                ctx.append(f"Ultimas licoes: {', '.join([l.get('erro','')[:40] for l in kg['licoes'][-3:]])}")
            except: pass
        
        if os.path.exists(AUTO_LOG):
            with open(AUTO_LOG, 'r') as f:
                log = json.load(f)
            ctx.append(f"Auto-reparos: {len(log.get('reparos',[]))} tentativas")
        
        contexto = '\n'.join(ctx)
        prompt = f"{contexto}\n\nUsuario perguntou: {pergunta}\n\nComo narrador do MCR-DevIA, responda de forma clara e honesta sobre o que ele sabe, esta fazendo, ou aprendendo."
        
        resp = ia(prompt, 0.7)
        if resp:
            print(f'\n[Narrador] {resp[:400]}')
    
    def resumo_executivo(self):
        """Resumo rapido do estado atual."""
        n_licoes = 0
        n_reparos = 0
        if os.path.exists(KG_PATH):
            try:
                with open(KG_PATH, 'r', encoding='utf-8', errors='replace') as f:
                    kg = json.load(f)
                n_licoes = len(kg['licoes'])
            except: pass
        if os.path.exists(AUTO_LOG):
            with open(AUTO_LOG, 'r') as f:
                log = json.load(f)
            n_reparos = len(log.get('reparos',[]))
        
        print('\n' + '='*60)
        print('  MCR-DevIA OBSERVATORY')
        print(f'  {n_licoes} licoes | {n_reparos} auto-reparos')
        print('  Digite perguntas ou ENTER para observar')
        print('  Ctrl+C para sair')
        print('='*60)


def main():
    narrador = Narrador()
    narrador.resumo_executivo()
    
    # Thread de auto-observacao (a cada 30s)
    def loop_observacao():
        while True:
            time.sleep(30)
            narrador.observar_e_narrar()
    
    t = threading.Thread(target=loop_observacao, daemon=True)
    t.start()
    
    # Loop principal: aceita perguntas
    while True:
        try:
            entrada = input('\nVoce> ').strip()
            if not entrada:
                continue
            if entrada.lower() in ('sair', 'exit', 'quit'):
                print('Observatorio encerrado.')
                break
            narrador.responder_pergunta(entrada)
        except (EOFError, KeyboardInterrupt):
            print('\nObservatorio encerrado.')
            break

if __name__ == '__main__':
    main()
