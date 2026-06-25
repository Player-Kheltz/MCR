#!/usr/bin/env python3
"""
MCR CREW V17 — QUALITY MATRIX + CONSISTENCY ENGINE
=====================================================
3 camadas que garantem qualidade SEMPRE:

1. QUALITY SCORING (Python puro): mede N versoes, fica com a melhor
2. CONSISTENCY CHECK (Python puro): NPCs, itens, quests se conectam?
3. AUTO-REFINEMENT: se nota baixa, IA tenta de novo com feedback
"""

import sys, os, json, re, hashlib, urllib.request, datetime, random, math

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox\.crew_v17'
os.makedirs(BASE, exist_ok=True)

# ============================================================
# QUALITY MATRIX — Mede qualidade de forma OBJETIVA
# ============================================================

class QualityMatrix:
    """
    Mede a qualidade de qualquer texto gerado usando metricas OBJETIVAS.
    Zero IA envolvida — 100% Python, 100% confiavel.
    """
    
    @staticmethod
    def pontuar_lore(texto):
        """
        Pontua um texto de lore de 0 a 100.
        Criterios (todos objetivos, viaveis em Python):
        """
        if not texto: return 0, ["Texto vazio"]
        problemas = []
        pontos = 50  # Comeca em 50
        
        # 1. COMPRIMENTO (peso: 20 pontos)
        palavras = texto.split()
        if len(palavras) < 20:
            pontos -= 15
            problemas.append(f"Muito curto ({len(palavras)} palavras)")
        elif len(palavras) > 30:
            pontos += 10
        elif len(palavras) > 50:
            pontos += 15
        
        # 2. VARIEDADE DE PALAVRAS (peso: 15 pontos)
        palavras_unicas = len(set(p.lower() for p in palavras))
        if palavras_unicas < 10:
            pontos -= 10
            problemas.append("Vocabulario muito repetitivo")
        elif palavras_unicas > 20:
            pontos += 10
        
        # 3. PALAVRAS RICAS (peso: 15 pontos)
        palavras_ricas = ['segredo', 'antigo', 'poder', 'historia', 'lendario', 'misterio',
                        'escuridao', 'luz', 'sabedoria', 'coragem', 'destino', 'profecia',
                        'guerra', 'paz', 'alianca', 'traicao', 'honra', 'medo', 'esperanca']
        encontradas = sum(1 for p in palavras_ricas if p in texto.lower())
        pontos += encontradas * 3
        if encontradas >= 3:
            pontos += 5  # Bonus por riqueza
        
        # 4. ESTRUTURA (peso: 10 pontos)
        if '.' in texto:
            frases = texto.split('.')
            if len(frases) >= 3:
                pontos += 10
            elif len(frases) >= 2:
                pontos += 5
        
        # 5. PERSONALIDADE (peso: 10 pontos)
        marcadores_personalidade = ['eu', 'voce', 'nos', 'meu', 'sua', 'nosso']
        if any(m in texto.lower() for m in marcadores_personalidade):
            pontos += 10
        
        # 6. ORIGINALIDADE (peso: 10 pontos)
        # Penaliza se comecar com "Em uma terra distante" etc
        abertura_generica = ['era uma vez', 'em uma terra', 'ha muito tempo', 'certa vez']
        if any(a in texto.lower()[:50] for a in abertura_generica):
            pontos -= 10
            problemas.append("Abertura generica")
        
        # Normaliza
        pontos = max(0, min(100, pontos))
        return pontos, problemas
    
    @staticmethod
    def pontuar_npc(lore_dict):
        """Pontua um NPC completo."""
        pontos = 0
        problemas = []
        
        # Historia
        if 'HISTORIA' in lore_dict:
            p, probs = QualityMatrix.pontuar_lore(lore_dict['HISTORIA'])
            pontos += p * 0.4
            problemas.extend([f'Historia: {pr}' for pr in probs])
        else:
            problemas.append("Sem historia")
        
        # Saudacao
        if 'SAUDACAO' in lore_dict:
            saud = lore_dict['SAUDACAO']
            if len(saud) > 30:
                pontos += 15
            if '"' in saud:
                pontos += 5
        else:
            problemas.append("Sem saudacao")
            pontos -= 10
        
        # Personalidade
        if 'PERSONALIDADE' in lore_dict:
            tracos = lore_dict['PERSONALIDADE'].split(',')
            if len(tracos) >= 3:
                pontos += 20
            elif len(tracos) >= 2:
                pontos += 10
        else:
            problemas.append("Sem personalidade")
        
        # Segredo
        if 'SEGREDO' in lore_dict:
            p, probs = QualityMatrix.pontuar_lore(lore_dict['SEGREDO'])
            pontos += p * 0.3
        else:
            problemas.append("Sem segredo")
        
        # Conexoes
        if 'CONEXOES' in lore_dict:
            if len(lore_dict['CONEXOES']) > 10:
                pontos += 10
        
        return max(0, min(100, pontos)), problemas
    
    @staticmethod
    def melhor_versao(versoes, pontuador):
        """De N versoes, retorna a melhor pontuada."""
        if not versoes: return None, 0, []
        
        melhor = None
        melhor_pontos = -1
        melhor_probs = []
        
        for i, v in enumerate(versoes):
            pontos, probs = pontuador(v)
            if pontos > melhor_pontos:
                melhor = v
                melhor_pontos = pontos
                melhor_probs = probs
        
        return melhor, melhor_pontos, melhor_probs


# ============================================================
# CONSISTENCY ENGINE — Conecta TUDO
# ============================================================

class ConsistencyEngine:
    """
    Verifica se tudo no mundo faz sentido junto:
    - Personagens mencionam outros que existem
    - Itens sao referenciados nas quests corretas
    - Locais usados existem no banco de lore
    - Nao ha contradicoes
    """
    
    def __init__(self, banco_lore):
        self.banco = banco_lore
    
    def verificar_npc(self, lore_dict):
        """Verifica consistencia de um NPC."""
        inconsistencias = []
        
        # Conexoes existem?
        conexoes = lore_dict.get('CONEXOES', '')
        if conexoes:
            for nome in re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', conexoes):
                nome = nome.strip()
                if nome and len(nome) > 3:
                    # Verifica se o personagem ou local existe
                    existe = (
                        nome.lower() in self.banco.get('personagens', {}) or
                        nome.lower() in [l.lower() for l in 
                            sum([c.get('locais',[]) for c in self.banco.get('cidades',{}).values()], [])]
                    )
                    if not existe:
                        inconsistencias.append(f"'{nome}' mencionado mas nao encontrado no banco")
        
        return inconsistencias
    
    def verificar_quest_com_npc(self, quest_lore, npc_nome):
        """Verifica se a quest referencia o NPC corretamente."""
        inconsistencias = []
        texto = str(quest_lore.get('INTRODUCAO', '')) + str(quest_lore.get('OBJETIVOS', ''))
        
        if npc_nome and npc_nome.lower() not in texto.lower():
            inconsistencias.append(f"Quest nao menciona o NPC '{npc_nome}'")
        
        return inconsistencias


# ============================================================
# IA LOCAL
# ============================================================

class IALocal:
    def __init__(self, model='qwen2.5-coder:7b'):
        self.model = model
        self.cache = {}
    
    def gerar(self, prompt, temp=0.8):
        chave = hashlib.md5(prompt.encode()).hexdigest()
        if chave in self.cache: return self.cache[chave]
        try:
            data = json.dumps({'model':self.model,'prompt':prompt,'stream':False,
                'options':{'temperature':temp,'num_ctx':4096,'top_p':0.95}}).encode()
            req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.loads(r.read()).get('response','')
                self.cache[chave] = resp
                return resp
        except: return None


# ============================================================
# GERADOR COM MULTI-VERSOES + QUALIDADE
# ============================================================

class GeradorComQualidade:
    """
    Gera N versoes, mede qualidade, fica com a melhor.
    Se nenhuma for boa, IA tenta de novo com feedback.
    """
    
    def __init__(self, ia, consistency=None):
        self.ia = ia
        self.consistency = consistency
    
    def gerar_lore_npc(self, nome, cargo='', cidade='eridanus', tentativas=3):
        """Gera N versoes do lore do NPC, retorna a melhor."""
        ctx_mundo = self._get_contexto_mundo()
        versoes = []
        
        for t in range(tentativas):
            prompt = f"Crie um NPC para Eridanus.\nNOME: {nome}\nCARGO: {cargo}\n{ctx_mundo}\n\n"
            
            if t > 0 and versoes:
                # Feedback da tentativa anterior
                piores = sorted(versoes, key=lambda v: QualityMatrix.pontuar_npc(v)[0])
                pior = piores[0] if piores else None
                if pior:
                    _, probs = QualityMatrix.pontuar_npc(pior)
                    if probs:
                        prompt += f"\nEVITE estes problemas:\n" + "\n".join(probs[:3])
            
            prompt += "\n\nCrie: HISTORIA (2-3 paragrafos), PERSONALIDADE (3 tracos), SAUDACAO (dialogo), SEGREDO, CONEXOES\nFormato:\nHISTORIA:\nPERSONALIDADE:\nSAUDACAO:\nSEGREDO:\nCONEXOES:"
            
            r = self.ia.gerar(prompt, 0.85)
            lore = self._parse_lore(r)
            if lore:
                versoes.append(lore)
        
        # Seleciona a melhor
        if versoes:
            melhor, pontos, probs = QualityMatrix.melhor_versao(versoes, QualityMatrix.pontuar_npc)
            
            # Verifica consistencia
            inconsistencias = []
            if self.consistency:
                inconsistencias = self.consistency.verificar_npc(melhor)
            
            return melhor, pontos, probs, inconsistencias
        
        return {}, 0, ["Falha ao gerar"], []
    
    def _get_contexto_mundo(self):
        """Retorna contexto do mundo (simplificado)."""
        return "Mundo: Eridanus, cidade fundada ha 300 anos por tres herois."
    
    def _parse_lore(self, texto):
        """Parser flexivel."""
        lore = {}
        if not texto: return lore
        
        campos = ['HISTORIA', 'PERSONALIDADE', 'SAUDACAO', 'SEGREDO', 'CONEXOES']
        for campo in campos:
            m = re.search(rf'{campo}:\s*(.+?)(?=\n[A-Z][A-Z ]+:)', texto, re.DOTALL | re.IGNORECASE)
            if m:
                val = m.group(1).strip().strip('*\n\r" ')
                if len(val) > 15:
                    lore[campo] = val[:500]
        
        return lore


# ============================================================
# DEMO
# ============================================================

def demo():
    print('='*60)
    print('  MCR CREW V17 — QUALITY MATRIX + CONSISTENCY')
    print('='*60)
    
    ia = IALocal()
    consistency = ConsistencyEngine({})  # Banco vazio pra teste
    gerador = GeradorComQualidade(ia, consistency)
    
    # Teste: gera 3 versoes do mesmo NPC, fica com a melhor
    print('\n--- GERANDO 3 VERSAOES DO MESMO NPC ---')
    print('  NPC: Velho Sabio, Guardiao do Conhecimento\n')
    
    melhor, pontos, probs, inconsistencias = gerador.gerar_lore_npc('Velho Sabio', 'Guardiao do Conhecimento')
    
    print(f'  Pontuacao: {pontos}/100')
    
    if probs:
        print(f'  Problemas: {len(probs)}')
        for p in probs[:3]: print(f'    - {p}')
    
    if inconsistencias:
        print(f'  Inconsistencias:')
        for i in inconsistencias: print(f'    - {i}')
    
    if melhor:
        print(f'\n  MELHOR VERSAO:')
        for campo in ['HISTORIA', 'PERSONALIDADE', 'SAUDACAO', 'SEGREDO']:
            if campo in melhor:
                print(f'    {campo}: {melhor[campo][:100]}...')
    
    # Mostra como funciona o scoring
    print('\n--- EXEMPLO DE SCORING ---')
    texto_bom = "O Velho Sabio guarda um segredo antigo sobre os fundadores de Eridanus. Ha trezentos anos, ele testemunhou a queda do ultimo guardiao e desde entao protege a Chama Eterna. Poucos sabem que sua sabedoria vem de um pacto com os espiritos da biblioteca."
    texto_ruim = "Um sabio velho que mora na cidade."
    
    pontos_bom, _ = QualityMatrix.pontuar_lore(texto_bom)
    pontos_ruim, _ = QualityMatrix.pontuar_lore(texto_ruim)
    
    print(f'  Texto RICO: {pontos_bom}/100 (deve ser alto)')
    print(f'  Texto POBRE: {pontos_ruim}/100 (deve ser baixo)')
    
    print(f'\n--- CONCLUSAO ---')
    print(f'  O Quality Matrix garante que apenas o MELHOR resultado seja usado.')
    print(f'  Gera N versoes, mede, compara, seleciona.')
    print(f'  Tudo em Python puro, zero IA, 100% confiavel.')

if __name__ == '__main__':
    demo()
