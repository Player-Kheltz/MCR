"""
MCR-DevIA — Cerebro ML (aprendizado por reforco)
==================================================
Rastreia taxa de sucesso de cada detector e prompt,
decide qual estrategia usar, e melhora com o tempo.
"""
import json, os, time, random
from collections import defaultdict

PATH = r'E:\Projeto MCR\sandbox\.mcr_ml_brain.json'

class CerebroML:
    def __init__(self):
        self.data = self._carregar()
    
    def _carregar(self):
        if os.path.exists(PATH):
            with open(PATH, 'r') as f:
                return json.load(f)
        return {
            'detectores': {},    # nome -> {tentativas, acertos, taxa}
            'prompts': {},       # tipo -> {tentativas, sucessos, taxa}
            'estrategias': {     # qual estrategia usar quando
                'ciclos_estagnados': 0,
                'ultima_mudanca': 0,
                'modo_exploracao': True,
            },
            'metricas': {
                'total_ciclos': 0,
                'total_deteccoes': 0,
                'total_correcoes': 0,
                'total_same_code': 0,
            }
        }
    
    def salvar(self):
        with open(PATH, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def registrar_deteccao(self, detector, funcionou):
        """Registra se um detector funcionou."""
        if detector not in self.data['detectores']:
            self.data['detectores'][detector] = {'tentativas': 0, 'acertos': 0, 'taxa': 0.0}
        d = self.data['detectores'][detector]
        d['tentativas'] += 1
        if funcionou:
            d['acertos'] += 1
        d['taxa'] = d['acertos'] / max(1, d['tentativas'])
        self.data['metricas']['total_deteccoes'] += 1
        self.salvar()
    
    def registrar_prompt(self, tipo, sucesso):
        """Registra se um prompt de correcao funcionou."""
        if tipo not in self.data['prompts']:
            self.data['prompts'][tipo] = {'tentativas': 0, 'sucessos': 0, 'taxa': 0.0}
        p = self.data['prompts'][tipo]
        p['tentativas'] += 1
        if sucesso:
            p['sucessos'] += 1
            self.data['metricas']['total_correcoes'] += 1
        else:
            self.data['metricas']['total_same_code'] += 1
        p['taxa'] = p['sucessos'] / max(1, p['tentativas'])
        self.salvar()
    
    def escolher_prompt(self, problema):
        """Escolhe o melhor prompt para um problema baseado em historico."""
        # Sempre tenta o prompt com maior taxa de sucesso primeiro
        melhores = sorted(
            self.data['prompts'].items(),
            key=lambda x: x[1]['taxa'],
            reverse=True
        )
        
        # Exploration: 20% das vezes, tenta um prompt aleatorio
        if random.random() < 0.2:
            return 'explorar'
        
        if melhores and melhores[0][1]['taxa'] > 0:
            return melhores[0][0]
        
        return 'corrigir'
    
    def detectar_estagnacao(self):
        """Detecta se o aprendizado estagnou."""
        e = self.data['estrategias']
        e['ciclos_estagnados'] += 1
        return e['ciclos_estagnados'] >= 5
    
    def resetar_estagnacao(self):
        self.data['estrategias']['ciclos_estagnados'] = 0
        self.data['estrategias']['ultima_mudanca'] = time.time()
        self.salvar()
    
    def melhores_detectores(self, top_n=5):
        """Retorna os detectores com maior taxa de sucesso."""
        ordenados = sorted(
            self.data['detectores'].items(),
            key=lambda x: x[1]['taxa'],
            reverse=True
        )
        return ordenados[:top_n]
    
    def status(self):
        return {
            'detectores': len(self.data['detectores']),
            'prompts': len(self.data['prompts']),
            'ciclos': self.data['metricas']['total_ciclos'],
            'deteccoes': self.data['metricas']['total_deteccoes'],
            'correcoes': self.data['metricas']['total_correcoes'],
            'same_code': self.data['metricas']['total_same_code'],
        }
