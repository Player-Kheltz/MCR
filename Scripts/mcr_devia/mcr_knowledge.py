#!/usr/bin/env python3
"""
MCR-DevIA — Knowledge Farmer (V12 Universal)
==============================================
Aplica o padrao V12 para ALIMENTAR o Knowledge Graph
com QUALQUER dominio de conhecimento.

Python estrutura o prompt.
IA local gera as licoes.
KG armazena para sempre.

Uso: python mcr_knowledge.py --domain "filosofia" --count 10
     python mcr_knowledge.py --domain "economia" --count 10
     python mcr_knowledge.py --domain "python" --count 10
     python mcr_knowledge.py --all (todos os dominios, 5 cada)
"""

import sys, os, json, re, urllib.request, hashlib, datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
SANDBOX = r'E:\Projeto MCR\sandbox'
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')

# === TEMPLATES DE DOMINIO (V12: Python estrutura, IA preenche) ===

DOMINIOS = {
    'filosofia': {
        'temas': ['Socrates', 'Platao', 'Aristoteles', 'Nietzsche', 'Kant',
                  'Etica', 'Logica', 'Metafisica', 'Existencialismo', 'Estoicismo'],
        'prompt': "Crie uma licao de filosofia sobre {tema}. Responda:\nPERGUNTA: (uma pergunta filosofica)\nRESPOSTA: (explicacao em 2-3 frases)\nAUTOR: (filosofo relacionado)",
    },
    'economia': {
        'temas': ['Inflacao', 'Juros', 'PIB', 'Oferta e Demanda', 'Mercado de Acoes',
                  'Bitcoin', 'Keynes', 'Capitalismo', 'Socialismo', 'Crise de 1929'],
        'prompt': "Crie uma licao de economia sobre {tema}. Responda:\nPERGUNTA: (o que e)\nRESPOSTA: (explicacao simples)\nEXEMPLO: (exemplo pratico)",
    },
    'python': {
        'temas': ['List Comprehension', 'Decorators', 'Generators', 'Context Managers',
                  'Async/Await', 'Type Hints', 'Dunder Methods', 'Packaging',
                  'Testing', 'Performance Tips'],
        'prompt': "Crie uma licao de Python sobre {tema}. Responda:\nPERGUNTA: (o que e)\nRESPOSTA: (explicacao)\nEXEMPLO: (codigo exemplo)",
    },
    'programacao': {
        'temas': ['OOP', 'SOLID', 'Design Patterns', 'Clean Code', 'Git',
                  'Algorithm Complexity', 'Database Indexing', 'REST APIs',
                  'Microservices', 'Test Driven Development'],
        'prompt': "Crie uma licao de programacao sobre {tema}. Responda:\nPERGUNTA: (conceito)\nRESPOSTA: (explicacao)\nEXEMPLO: (exemplo pratico)",
    },
    'git': {
        'temas': ['Branch', 'Merge', 'Rebase', 'Cherry-pick', 'Stash',
                  'Reset vs Revert', 'Pull Request', 'Git Flow', 'Hooks', 'Bisect'],
        'prompt': "Crie uma licao de Git sobre {tema}. Responda:\nPERGUNTA: (comando/conceito)\nRESPOSTA: (para que serve)\nEXEMPLO: (comando exemplo)",
    },
    'financas': {
        'temas': ['Juros Compostos', 'Tesouro Direto', 'Acoes', 'Fundos Imobiliarios',
                  'Reserva de Emergencia', 'Diversificacao', 'Imposto de Renda',
                  'Inflacao', 'CDI', 'Selic'],
        'prompt': "Crie uma licao de financas sobre {tema}. Responda:\nPERGUNTA: (conceito)\nRESPOSTA: (explicacao simples)\nDICA: (dica pratica)",
    },
    'produtividade': {
        'temas': ['Pomodoro', 'GTD', 'Kanban', 'Deep Work', 'Atomic Habits',
                  'Eisenhower Matrix', 'Time Blocking', 'Bullet Journal',
                  'Parkinson Law', 'Pareto Principle'],
        'prompt': "Crie uma licao de produtividade sobre {tema}. Responda:\nPERGUNTA: (metodo)\nRESPOSTA: (como funciona)\nDICA: (como aplicar)",
    },
}


# ============================================================
# CONHECIMENTO
# ============================================================

class KG:
    def __init__(self):
        self.path = KG_PATH
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(self.path):
            with open(self.path,'r',encoding='utf-8') as f:
                return json.load(f)
        return {'versoes':0,'licoes':[],'metricas':{'licoes':0}}
    
    def salvar(self):
        self.data['versoes'] += 1
        self.data['metricas']['licoes'] = len(self.data['licoes'])
        with open(self.path,'w',encoding='utf-8') as f:
            json.dump(self.data,f,ensure_ascii=False,indent=2)
    
    def adicionar_licao(self, pergunta, resposta, dominio, fonte='knowledge_farmer'):
        """Adiciona uma licao de QUALQUER dominio."""
        # Verifica se ja existe similar
        for l in self.data['licoes']:
            if l.get('erro','').lower() == pergunta.lower()[:50]:
                return False  # Ja existe
        
        self.data['licoes'].append({
            'id': f'K{len(self.data["licoes"])+1:04d}',
            'erro': pergunta[:100],
            'causa': f'[Dominio: {dominio}]',
            'solucao': resposta[:300],
            'ctx': dominio,
            'fonte': fonte,
            'usos': 0,
            'criada_em': str(datetime.datetime.now())[:10],
        })
        self.salvar()
        return True


# ============================================================
# IA LOCAL
# ============================================================

class IA:
    def gerar(self, prompt, temp=0.7):
        try:
            d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
                'options':{'temperature':temp,'num_ctx':4096}}).encode()
            r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
            resp = json.loads(urllib.request.urlopen(r,timeout=120).read()).get('response','')
            return resp
        except: return None


# ============================================================
# KNOWLEDGE FARMER
# ============================================================

class KnowledgeFarmer:
    def __init__(self):
        self.ia = IA()
        self.kg = KG()
    
    def cultivar(self, dominio, quantidade=5):
        """Planta conhecimento no KG."""
        if dominio not in DOMINIOS:
            print(f'Dominios: {", ".join(DOMINIOS.keys())}')
            return 0
        
        info = DOMINIOS[dominio]
        temas = info['temas'][:quantidade]
        template = info['prompt']
        
        print(f'\n[CULTIVAR] {dominio.upper()} - {len(temas)} licoes')
        contador = 0
        
        for tema in temas:
            # V12: Python estrutura o prompt, IA preenche
            prompt = template.replace('{tema}', tema)
            
            r = self.ia.gerar(prompt, 0.7)
            if not r: continue
            
            # Extrai pergunta e resposta
            pergunta = ''
            resposta = ''
            for line in r.split('\n'):
                if 'PERGUNTA:' in line:
                    pergunta = line.split(':',1)[1].strip()[:100]
                elif 'RESPOSTA:' in line:
                    resposta = line.split(':',1)[1].strip()[:300]
                elif 'DICA:' in line and not resposta:
                    resposta = line.split(':',1)[1].strip()[:300]
            
            if pergunta and resposta:
                if self.kg.adicionar_licao(pergunta, resposta, dominio):
                    contador += 1
                    print(f'  [+] {pergunta[:60]}...')
        
        print(f'  Total: {contador} novas licoes em {dominio}')
        return contador


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--domain', help='Dominio para cultivar')
    parser.add_argument('--count', type=int, default=5, help='Quantas licoes')
    parser.add_argument('--all', action='store_true', help='Todos os dominios')
    args = parser.parse_args()
    
    farmer = KnowledgeFarmer()
    
    kg_antes = len(farmer.kg.data['licoes'])
    
    if args.all:
        total = 0
        for dominio in DOMINIOS:
            total += farmer.cultivar(dominio, min(5, len(DOMINIOS[dominio]['temas'])))
        print(f'\n{"="*60}')
        print(f'  TOTAL: {total} novas licoes em {len(DOMINIOS)} dominios')
        print(f'{"="*60}')
    
    elif args.domain:
        farmer.cultivar(args.domain, args.count)
    
    else:
        print(__doc__)
        return
    
    kg_depois = len(farmer.kg.data['licoes'])
    print(f'\n  Knowledge Graph: {kg_antes} -> {kg_depois} licoes (+{kg_depois - kg_antes})')
    print(f'  Versao: V{farmer.kg.data["versoes"]}')

if __name__ == '__main__':
    main()
