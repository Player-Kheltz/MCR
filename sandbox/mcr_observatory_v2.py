#!/usr/bin/env python3
"""
MCR-DevIA OBSERVATORY V2 — Tempo Real
========================================
Nao espera 30s. Mostra TUDO na hora que acontece.
Fica vigiando o log do batimento cardiaco e exibe em tempo real.
Como um 'tail -f' do que o MCR-DevIA esta pensando.
"""

import sys, os, time, threading, datetime

HEART_LOG = r'E:\Projeto MCR\sandbox\.mcr_heartbeat.log'

class ObservatorioTempoReal:
    """Mostra em tempo real o que o MCR-DevIA esta fazendo."""
    
    def __init__(self):
        self.ultimo_tamanho = 0
        self.rodando = True
    
    def _cabeçalho(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print('='*60)
        print('  MCR-DevIA — TEMPO REAL')
        print('  Mostrando o que ele esta pensando AGORA')
        print('  Digite algo e pressione Enter para perguntar')
        print('  Ctrl+C para sair')
        print('='*60)
        print()
    
    def _vigiar_log(self):
        """Fica vigiando o log e mostra novas linhas em tempo real."""
        while self.rodando:
            try:
                if not os.path.exists(HEART_LOG):
                    time.sleep(1)
                    continue
                
                tamanho_atual = os.path.getsize(HEART_LOG)
                
                if tamanho_atual > self.ultimo_tamanho:
                    with open(HEART_LOG, 'r', encoding='utf-8', errors='replace') as f:
                        f.seek(self.ultimo_tamanho)
                        novas_linhas = f.read()
                    
                    if novas_linhas:
                        # Mostra com timestamp formatado
                        for linha in novas_linhas.split('\n'):
                            linha = linha.strip()
                            if not linha: continue
                            # Remove o timestamp do log e adiciona cor visual
                            if '--- Batida' in linha:
                                print(f'\n{"="*50}')
                                print(f'  {linha}')
                                print(f'{"="*50}')
                            elif 'Saude:' in linha:
                                print(f'  [SAUDE] {linha.split("Saude:")[1].strip()}')
                            elif 'Escaneando' in linha:
                                print(f'  [SCAN] {linha.split("] ")[-1] if "] " in linha else linha}')
                            elif 'Discrepancia' in linha:
                                print(f'  [!] {linha.split("] ")[-1] if "] " in linha else linha}')
                            elif 'Tentando reparar' in linha:
                                print(f'  [REPARO] {linha.split("] ")[-1] if "] " in linha else linha}')
                            elif 'IA gerou' in linha:
                                print(f'  [IA] {linha.split("] ")[-1] if "] " in linha else linha}')
                            elif 'Nada a reparar' in linha:
                                print(f'  [OK] Templates atualizados.')
                            else:
                                print(f'  {linha.split("] ")[-1] if "] " in linha else linha}')
                    
                    self.ultimo_tamanho = tamanho_atual
                
                time.sleep(0.5)  # Verifica a cada 0.5s
            except:
                time.sleep(1)
    
    def perguntar(self, pergunta):
        """Faz uma pergunta e obtem resposta."""
        prompt = f"MCR-DevIA esta ativo. Estado atual: {self._estado_atual()}\n\nUsuario: {pergunta}\n\nResponda de forma TECNICA e DIRETA sobre o estado do MCR-DevIA."
        
        try:
            import urllib.request, json
            d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
                'options':{'temperature':0.5,'num_ctx':4096}}).encode()
            r = urllib.request.Request('http://localhost:11434/api/generate',data=d,headers={'Content-Type':'application/json'})
            resp = json.loads(urllib.request.urlopen(r,timeout=60).read()).get('response','')
            if resp:
                print(f'\n[Narrador] {resp[:500]}')
        except:
            print('\n[Narrador] (IA ocupada)')
    
    def _estado_atual(self):
        """Pega o estado atual do sistema."""
        try:
            if os.path.exists(HEART_LOG):
                with open(HEART_LOG, 'r', encoding='utf-8', errors='replace') as f:
                    linhas = f.readlines()
                ultimas = [l for l in linhas if 'Saude:' in l]
                if ultimas:
                    return ultimas[-1].strip()
        except: pass
        return 'desconhecido'
    
    def rodar(self):
        self._cabeçalho()
        print(f'  Aguardando MCR-DevIA fazer algo...\n')
        
        # Thread que vigia o log
        t = threading.Thread(target=self._vigiar_log, daemon=True)
        t.start()
        
        # Loop principal: aceita input do usuario
        while True:
            try:
                entrada = input('\n> ').strip()
                if not entrada:
                    continue
                if entrada.lower() in ('sair', 'exit', 'quit'):
                    break
                self.perguntar(entrada)
            except (KeyboardInterrupt, EOFError):
                break
        
        self.rodando = False
        print('\nObservatorio encerrado.')


if __name__ == '__main__':
    obs = ObservatorioTempoReal()
    obs.rodar()
