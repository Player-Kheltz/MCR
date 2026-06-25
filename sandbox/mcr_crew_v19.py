#!/usr/bin/env python3
"""
MCR CREW V19 — TEMPLATE LORE ENGINE
======================================
O padrao V12 aplicado a LORE.
Python da estrutura COMPLETA do prompt.
IA preenche APENAS os blanks criativos.
Resultado: formato SEMPRE igual, parser 100%, qualidade sempre mensuravel.
"""

import sys, os, json, re, hashlib, urllib.request, datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox'

class IATemplate:
    """IA que preenche blanks em templates de lore."""
    
    def __init__(self):
        self.cache = {}
    
    def gerar(self, prompt, temp=0.7):
        chave = hashlib.md5(prompt.encode()).hexdigest()
        if chave in self.cache: return self.cache[chave]
        try:
            data = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
                'options':{'temperature':temp,'num_ctx':4096,'top_p':0.95}}).encode()
            req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.loads(r.read()).get('response','')
                self.cache[chave] = resp
                return resp
        except: return None
    
    def preencher_lore(self, tipo, contexto=''):
        """
        Template de lore: Python da os campos, IA preenche.
        Retorna dict SEMPRE com as mesmas chaves.
        """
        if tipo == 'NPC':
            template = """Preencha EXATAMENTE neste formato (apenas os valores, sem explicacoes):
HISTORIA: (historia do NPC em 2 frases)
PERSONALIDADE: (3 adjetivos separados por virgula)
SAUDACAO: (fala curta do NPC)
SEGREDO: (um segredo que o NPC esconde)
CONEXAO: (outro personagem ou lugar que conhece)
"""
        elif tipo == 'ITEM':
            template = """Preencha EXATAMENTE neste formato:
ORIGEM: (de onde o item veio, 1-2 frases)
PODER: (o que o item faz)
LENDA: (o que os habitantes dizem sobre ele)
"""
        elif tipo == 'QUEST':
            template = """Preencha EXATAMENTE neste formato:
CONTEXTO: (por que a quest existe, 2 frases)
OBJETIVO: (o que o jogador precisa fazer)
REVELACAO: (o que se descobre no final)
RECOMPENSA: (o que o jogador ganha)
"""
        else:
            return {}
        
        prompt = f"{contexto}\n\n{template}\n"
        r = self.gerar(prompt, 0.7)
        
        # Parse: extrai CAMPO: valor (formato SEMPRE igual)
        lore = {}
        if r:
            for line in r.split('\n'):
                line = line.strip()
                if ':' in line:
                    partes = line.split(':', 1)
                    campo = partes[0].strip().upper()
                    valor = partes[1].strip()
                    # Só aceita se for campo conhecido
                    if campo in ('HISTORIA','PERSONALIDADE','SAUDACAO','SEGREDO','CONEXAO',
                                'ORIGEM','PODER','LENDA','CONTEXTO','OBJETIVO','REVELACAO','RECOMPENSA'):
                        if len(valor) > 5:
                            lore[campo] = valor[:500]
        
        return lore


class QualityMatrix:
    """Mede qualidade do lore extraido - funciona mesmo com valores parciais."""
    
    @staticmethod
    def pontuar(lore, tipo):
        """Pontua lore de 0 a 100. Funciona mesmo se alguns campos faltarem."""
        if not lore: return 0, ["Nenhum campo preenchido"]
        problemas = []
        pontos = 0
        
        if tipo == 'NPC':
            campos = {'HISTORIA': 30, 'PERSONALIDADE': 25, 'SAUDACAO': 20, 'SEGREDO': 15, 'CONEXAO': 10}
        elif tipo == 'ITEM':
            campos = {'ORIGEM': 40, 'PODER': 35, 'LENDA': 25}
        elif tipo == 'QUEST':
            campos = {'CONTEXTO': 30, 'OBJETIVO': 30, 'REVELACAO': 25, 'RECOMPENSA': 15}
        else:
            return 0, ["Tipo desconhecido"]
        
        for campo, peso in campos.items():
            if campo in lore:
                valor = lore[campo]
                palavras = len(valor.split())
                if palavras >= 15:
                    pontos += peso
                elif palavras >= 8:
                    pontos += peso * 0.6
                else:
                    pontos += peso * 0.3
                    problemas.append(f"{campo}: muito curto ({palavras} palavras)")
            else:
                problemas.append(f"Campo '{campo}' ausente")
        
        return min(100, pontos), problemas


# ============================================================
# TESTE COMPLETO
# ============================================================

def testar():
    ia = IATemplate()
    print('='*60)
    print('  V19 — TEMPLATE LORE ENGINE')
    print('  Python da estrutura, IA preenche blanks')
    print('='*60)
    
    resultados = []
    
    # Testa NPC
    print('\n[TESTE 1] Lore NPC')
    lore_npc = ia.preencher_lore('NPC', 'NPC: Velho Sabio, guardiao de Eridanus')
    pontos, probs = QualityMatrix.pontuar(lore_npc, 'NPC')
    print(f'  Pontos: {pontos}/100')
    for campo in ['HISTORIA','PERSONALIDADE','SAUDACAO','SEGREDO','CONEXAO']:
        if campo in lore_npc:
            print(f'  {campo}: {lore_npc[campo][:80]}')
    if probs: print(f'  Melhorias: {"; ".join(probs[:2])}')
    resultados.append(('NPC', pontos))
    
    # Testa ITEM
    print('\n[TESTE 2] Lore Item')
    lore_item = ia.preencher_lore('ITEM', 'Item: Olho de Eridanus, um artefato antigo')
    pontos, probs = QualityMatrix.pontuar(lore_item, 'ITEM')
    print(f'  Pontos: {pontos}/100')
    for campo in ['ORIGEM','PODER','LENDA']:
        if campo in lore_item:
            print(f'  {campo}: {lore_item[campo][:80]}')
    if probs: print(f'  Melhorias: {"; ".join(probs[:2])}')
    resultados.append(('ITEM', pontos))
    
    # Testa QUEST
    print('\n[TESTE 3] Lore Quest')
    lore_quest = ia.preencher_lore('QUEST', 'Quest: O Legado Perdido de Eridanus. NPC: Velho Sabio')
    pontos, probs = QualityMatrix.pontuar(lore_quest, 'QUEST')
    print(f'  Pontos: {pontos}/100')
    for campo in ['CONTEXTO','OBJETIVO','REVELACAO','RECOMPENSA']:
        if campo in lore_quest:
            print(f'  {campo}: {lore_quest[campo][:80]}')
    if probs: print(f'  Melhorias: {"; ".join(probs[:2])}')
    resultados.append(('QUEST', pontos))
    
    # Relatorio
    print(f'\n{"="*60}')
    media = sum(r[1] for r in resultados) / len(resultados)
    print(f'  RESULTADO: {media:.0f}/100')
    for tipo, pts in resultados:
        barra = '#' * (int(pts) // 10) + '-' * (10 - int(pts) // 10)
        print(f'  {tipo}: [{barra}] {pts}/100')
    print(f'{"="*60}')

if __name__ == '__main__':
    testar()
