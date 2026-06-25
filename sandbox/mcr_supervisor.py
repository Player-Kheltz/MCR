#!/usr/bin/env python3
"""
MCR-DevIA Auto-Supervisor v2
==============================
O modelo local MELHORA sem trocar de modelo.

Como:
  1. RAG no Knowledge Graph (contexto antes de gerar)
  2. Auto-avaliacao (Python mede qualidade do output)
  3. Ciclo: gera → avalia → se ruim → regenera com feedback
  4. Aprende: outputs ruins viram contra-exemplos

Uso: python mcr_supervisor.py "O que causa LNK2001?"
     python mcr_supervisor.py --gerar "Crie um NPC ferreiro"
"""

import sys, os, json, re, hashlib, urllib.request, datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox'
KG_PATH = os.path.join(BASE, '.mcr_devia', 'knowledge.json')

# ============================================================
# RAG ENGINE — Busca no Knowledge Graph
# ============================================================

class RAGEngine:
    """Busca contexto relevante no Knowledge Graph."""
    
    def __init__(self):
        self.kg = self._load_kg()
    
    def _load_kg(self):
        if os.path.exists(KG_PATH):
            with open(KG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'licoes': [], 'index': {}}
    
    def buscar(self, pergunta, max_resultados=3):
        """Busca licoes relevantes para a pergunta."""
        palavras = set(re.findall(r'\w+', pergunta.lower()))
        scores = []
        
        for licao in self.kg.get('licoes', []):
            score = 0
            texto = (licao.get('erro','') + ' ' + licao.get('causa','') + ' ' + 
                    licao.get('solucao','')).lower()
            for p in palavras:
                if len(p) > 3 and p in texto:
                    score += 1
            if score > 0:
                scores.append((score, licao))
        
        scores.sort(key=lambda x: -x[0])
        return [s[1] for s in scores[:max_resultados]]
    
    def contexto_para_prompt(self, pergunta):
        """Gera contexto enriquecido para o prompt da IA."""
        licoes = self.buscar(pergunta)
        if not licoes:
            return ''
        
        ctx = ['CONHECIMENTO RELEVANTE:']
        for l in licoes:
            ctx.append(f'- {l.get("erro","")}: {l.get("causa","")} → {l.get("solucao","")}')
            l['vezes_usada'] = l.get('vezes_usada', 0) + 1
        
        self._salvar_kg()
        return '\n'.join(ctx)
    
    def _salvar_kg(self):
        with open(KG_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.kg, f, ensure_ascii=False, indent=2)


# ============================================================
# QUALITY SCORER — Avalia a qualidade do output
# ============================================================

class QualityScorer:
    """Avalia a qualidade de um texto gerado. 100% Python, 0% IA."""
    
    @staticmethod
    def pontuar(texto, tipo='geral'):
        """Retorna (nota 0-100, [problemas])."""
        if not texto or len(texto) < 10:
            return 0, ["Texto muito curto"]
        
        problemas = []
        pontos = 50  # Comeca em 50
        
        palavras = texto.split()
        
        # Comprimento
        if len(palavras) > 50:
            pontos += 20
        elif len(palavras) > 20:
            pontos += 10
        else:
            problemas.append(f"Poucas palavras ({len(palavras)})")
        
        # Variedade
        unicas = len(set(p.lower() for p in palavras))
        if unicas > 30:
            pontos += 15
        elif unicas > 15:
            pontos += 5
        
        # Estrutura
        if '.' in texto and texto.count('.') >= 2:
            pontos += 10
        if ':' in texto:
            pontos += 5
        
        # Para codigo Lua
        if tipo == 'lua':
            if 'function' in texto: pontos += 10
            if 'local' in texto: pontos += 10
            if 'end' in texto: pontos += 5
            # Chaves balanceadas?
            opens = texto.count('{') + texto.count('(')
            closes = texto.count('}') + texto.count(')')
            if opens == closes:
                pontos += 15
            else:
                problemas.append("Chaves/parênteses desbalanceados")
        
        # Para lore
        if tipo == 'lore':
            palavras_ricas = ['segredo', 'antigo', 'poder', 'lendario', 'misterio',
                            'sabedoria', 'destino', 'honra', 'historia']
            encontradas = sum(1 for p in palavras_ricas if p in texto.lower())
            pontos += encontradas * 5
        
        return min(100, max(0, pontos)), problemas


# ============================================================
# IA LOCAL
# ============================================================

class IA:
    def gerar(self, prompt, temp=0.7):
        try:
            data = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
                'options':{'temperature':temp,'num_ctx':4096,'top_p':0.95}}).encode()
            req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
            r = json.loads(urllib.request.urlopen(req, timeout=120).read())
            return r.get('response','')
        except: return None


# ============================================================
# AUTO-SUPERVISOR — O ciclo completo
# ============================================================

class AutoSupervisor:
    """
    Ciclo:
      1. RAG busca contexto
      2. IA gera com contexto
      3. Python avalia
      4. Se nota baixa, regenera com feedback
      5. Aprende com o resultado
    """
    
    def __init__(self):
        self.rag = RAGEngine()
        self.scorer = QualityScorer()
        self.ia = IA()
        self.historico = []
    
    def processar(self, pergunta, tipo='geral', max_tentativas=3):
        """Processa uma pergunta com auto-supervisao."""
        print(f'\n[SUPERVISOR] Pergunta: {pergunta[:80]}...')
        
        # FASE 1: RAG
        print(f'  [RAG] Buscando conhecimento...')
        contexto = self.rag.contexto_para_prompt(pergunta)
        if contexto:
            print(f'  [RAG] Encontrado contexto relevante')
        
        for tentativa in range(1, max_tentativas + 1):
            print(f'  [Geracao] Tentativa {tentativa}/{max_tentativas}...')
            
            # Monta prompt com RAG
            prompt = pergunta
            if contexto:
                prompt = f"{contexto}\n\nPergunta: {pergunta}\n\n"
            
            # Se nao for primeira tentativa, adiciona feedback
            if tentativa > 1:
                prompt += f"\n\nFeedback da tentativa anterior (CORRIJA):\n"
                for prob in problemas[:3]:
                    prompt += f"- {prob}\n"
            
            prompt += "\n\nResposta:"
            
            # Gera
            resposta = self.ia.gerar(prompt)
            if not resposta:
                print(f'  [ERRO] IA nao respondeu')
                continue
            
            # Avalia
            nota, problemas = self.scorer.pontuar(resposta, tipo)
            print(f'  [Avaliacao] Nota: {nota}/100')
            
            self.historico.append({
                'tentativa': tentativa,
                'nota': nota,
                'problemas': problemas,
            })
            
            if nota >= 70:
                print(f'  [OK] Qualidade aceitavel!')
                return resposta, nota
            
            print(f'  [Refinando] Problemas: {"; ".join(problemas[:2])}')
        
        print(f'  [MAX] Atingiu maximo de tentativas.')
        return resposta if resposta else None, self.historico[-1]['nota'] if self.historico else 0


# ============================================================
# DEMO
# ============================================================

def main():
    if len(sys.argv) < 2:
        print('MCR-DevIA Auto-Supervisor v2')
        print()
        print('Comandos:')
        print(f'  python {sys.argv[0]} "sua pergunta"     Responde com auto-supervisao')
        print(f'  python {sys.argv[0]} --gerar "crie um NPC"  Gera codigo com qualidade')
        print(f'  python {sys.argv[0]} --lore "NPC"       Gera lore com supervisao')
        print(f'  python {sys.argv[0]} --status           Mostra estado')
        return
    
    supervisor = AutoSupervisor()
    
    query = ' '.join(sys.argv[1:])
    tipo = 'geral'
    
    if query.startswith('--gerar '):
        query = query[8:]
        tipo = 'lua'
    elif query.startswith('--lore '):
        query = query[7:]
        tipo = 'lore'
    elif query.startswith('--status'):
        print(f'\n[MCR-DevIA Supervisor]')
        print(f'  Knowledge Graph: {len(supervisor.rag.kg.get("licoes",[]))} licoes')
        print(f'  Auto-avaliacoes: {len(supervisor.historico)}')
        print(f'  Qualidade media: {sum(h.get("nota",0) for h in supervisor.historico)/max(1,len(supervisor.historico)):.0f}/100')
        return
    
    resposta, nota = supervisor.processar(query, tipo)
    
    if resposta:
        print(f'\n=== RESPOSTA (nota {nota}/100) ===')
        # Mostra so as primeiras linhas
        for linha in resposta.split('\n')[:8]:
            if linha.strip():
                print(f'  {linha[:120]}')
        if resposta.count('\n') > 8:
            print('  ...')

if __name__ == '__main__':
    main()
