"""
MCR-DevIA — Bio-Inspired Engine
=================================
Conceitos biologicos aplicados a aprendizado de maquina:
- Mutacao: evolui detectores que falham
- Quorum: detecta padroes sistemicos
- Tropismo: move scanner para areas mais problematicas
- Simbiose: usa CPU ociosa
"""

import os, re, json, random, time, hashlib, urllib.request

OLLAMA_URL = 'http://localhost:11434/api/generate'
KG_PATH = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'
BRAIN_PATH = r'E:\Projeto MCR\sandbox\.mcr_ml_brain.json'

class BioEngine:
    """
    Motor bio-inspirado que faz MCR-DevIA:
    - Mutar detectores que nunca funcionam
    - Detectar padroes em multiplos arquivos
    - Migrar para areas mais problematicas
    """
    
    def __init__(self):
        self.mutacoes = 0
        self.padroes = {}
    
    def mutar_detector(self, codigo_atual, tentativas, sucessos):
        """
        Se um detector nunca funcionou, MUTA ele.
        Usa IA pra gerar uma variacao.
        """
        if tentativas >= 5 and sucessos == 0:
            print(f'  [MUTACAO] Detector com 0/{tentativas} sucessos. Mutando...')
            prompt = f"""O detector abaixo nunca encontrou problemas validos em {tentativas} tentativas.

DETECTOR ATUAL:
{codigo_atual[:500]}

Gere uma VERSAO MODIFICADA deste detector que tente uma abordagem DIFERENTE.
Mude a regex, a logica, ou o padrao de busca.
Retorne APENAS o codigo da nova funcao."""
            
            try:
                d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
                    'options':{'temperature':0.9,'num_ctx':4096}}).encode()
                r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
                novo = json.loads(urllib.request.urlopen(r,timeout=60).read()).get('response','')
                if novo:
                    self.mutacoes += 1
                    return novo
            except: pass
        
        return None
    
    def quorum_sensing(self, resultados):
        """
        Se 3+ arquivos tem o MESMO problema, e um padrao sistemico.
        """
        problemas = {}
        for arquivo, probs in resultados:
            for p in probs:
                problemas[p] = problemas.get(p, 0) + 1
        
        padroes = {p: n for p, n in problemas.items() if n >= 3}
        
        for padrao, count in padroes.items():
            if padrao not in self.padroes:
                self.padroes[padrao] = count
                print(f'  [QUORUM] {padrao}: {count} arquivos afetados')
        
        return padroes
    
    def tropismo(self, scan_history):
        """
        Move scanner para areas com mais problemas.
        Se uma pasta sempre tem 0 problemas, escaneia ela menos.
        Se uma pasta sempre tem problemas, escaneia ela mais.
        """
        pesos = {}
        for pasta, problemas in scan_history:
            if problemas > 0:
                pesos[pasta] = pesos.get(pasta, 1) * 1.5  # Reforco
            else:
                pesos[pasta] = pesos.get(pasta, 1) * 0.8  # Enfraquece
        
        return pesos


class DetectorEvolutivo:
    """
    Detector que MELHORA com o tempo.
    Cada geracao, so os melhores sobrevivem.
    """
    
    def __init__(self, nome, func_code, taxa_sucesso=0.0):
        self.nome = nome
        self.func_code = func_code
        self.taxa_sucesso = taxa_sucesso
        self.geracao = 0
        self.historico = []
    
    def registrar_tentativa(self, sucesso):
        self.historico.append(sucesso)
        if len(self.historico) > 20:
            self.historico.pop(0)
        self.taxa_sucesso = sum(self.historico) / max(1, len(self.historico))
    
    def precisa_mutar(self):
        """Precisa de mutacao se taxa < 10% apos 10 tentativas."""
        return len(self.historico) >= 10 and self.taxa_sucesso < 0.1
    
    def sobreviveu(self):
        """Sobrevive se taxa > 5%."""
        return len(self.historico) < 5 or self.taxa_sucesso > 0.05


if __name__ == '__main__':
    bio = BioEngine()
    print('=== MCR-DevIA BIO ENGINE ===')
    print(f'Mutacoes: {bio.mutacoes}')
    print(f'Padroes sistemicos: {len(bio.padroes)}')
    print(f'Conceitos: mutacao, quorum, tropismo')
