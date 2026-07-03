#!/usr/bin/env python3
"""
MCR-DevIA CHAT — Terminal Interativo Local
============================================
Igual ao OpenCode, mas 100% local, zero cloud.

Modos:
  [Chat]  — Conversa livre com IA + RAG
  [Build] — Executa acoes (gerar, compilar, lore)
  [Plan]  — Planeja sistemas complexos

Uso: python mcr_chat.py
     python mcr_chat.py --modo plan
"""

import sys, os, json, re, urllib.request, hashlib, datetime, glob

OLLAMA_URL = 'http://localhost:11434/api/generate'
SANDBOX = r'E:\Projeto MCR\sandbox'
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
HIST_PATH = os.path.join(SANDBOX, '.mcr_chat_history.json')

# Cores (ANSI)
VERDE = '\033[92m'
AZUL = '\033[94m'
AMARELO = '\033[93m'
VERMELHO = '\033[91m'
MAGENTA = '\033[95m'
CIANO = '\033[96m'
RESET = '\033[0m'
NEGRITO = '\033[1m'

# ============================================================
# KNOWLEDGE GRAPH
# ============================================================

class KG:
    def __init__(self):
        self.path = KG_PATH; self.data = self._load()
    def _load(self):
        if os.path.exists(self.path):
            with open(self.path,'r',encoding='utf-8') as f: return json.load(f)
        return {'versoes':0,'licoes':[],'index':{},'metricas':{'licoes':0,'usos':0,'geracoes':0,'compilacoes':0}}
    def salvar(self):
        self.data['versoes'] += 1; self.data['metricas']['licoes'] = len(self.data['licoes'])
        with open(self.path,'w',encoding='utf-8') as f: json.dump(self.data,f,ensure_ascii=False,indent=2)
    def buscar(self, texto, max_r=3):
        palavras = set(re.findall(r'\w+',texto.lower()))
        scores = []
        for l in self.data['licoes']:
            alvo = (l.get('erro','')+' '+l.get('causa','')+' '+l.get('solucao','')).lower()
            score = sum(3 if p in l.get('erro','').lower() else 2 if p in l.get('causa','').lower() else 1
                       for p in palavras if len(p)>3 and p in alvo)
            if score>0: scores.append((score,l))
        scores.sort(key=lambda x:-x[0])
        return [s[1] for s in scores[:max_r]]
    def aprender(self, erro, causa, sol, ctx='geral'):
        self.data['licoes'].append({'id':f'L{len(self.data["licoes"])+1:04d}','erro':erro,'causa':causa,'solucao':sol,'ctx':ctx,'usos':0})
        self.salvar()
        return f'Aprendi: {erro[:50]}...'


# ============================================================
# IA LOCAL
# ============================================================

class IA:
    def gerar(self, prompt, temp=0.7):
        try:
            d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
                'options':{'temperature':temp,'num_ctx':4096,'top_p':0.95}}).encode()
            r = urllib.request.Request(OLLAMA_URL, data=d, headers={'Content-Type':'application/json'})
            resp = json.loads(urllib.request.urlopen(r,timeout=120).read()).get('response','')
            return resp
        except Exception as e: return f'[ERRO IA] {e}'


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = {
    'npc': ('-- NPC: {nome}\nlocal n = NPC("{nome}")\nn:setSaudacao("{saudacao}")\nn:addItem({item_id},{item_preco})\nprint("NPC {nome} carregado.")',['nome','saudacao','item_id','item_preco']),
    'monster': ('-- Monster: {nome}\nlocal m = Monster("{nome}")\nm:setHealth({hp})\nm:setAttack({atk})\nm:setDefense({def})\nm:addLoot({loot_id},{loot_chance})\nprint("Monster {nome} carregado.")',['nome','hp','atk','def','loot_id','loot_chance']),
    'quest': ('-- Quest: {nome}\nlocal q = Quest("{nome}")\nq:setDescricao("{desc}")\nq:addObjetivo("{obj}")\nq:addRecompensa("xp",{xp})\nprint("Quest {nome} carregada.")',['nome','desc','obj','xp']),
    'item': ('-- Item: {nome}\nlocal i = Item({id},"{nome}")\ni:setType("{tipo}")\ni:setWeight({peso})\nprint("Item {nome} carregado.")',['nome','id','tipo','peso']),
    'spell': ('-- Spell: {nome}\nlocal s = Spell("{nome}","{elem}")\ns:setDamage({dano})\ns:setManaCost({mana})\ns:setCooldown({cd})\nprint("Spell {nome} carregada.")',['nome','elem','dano','mana','cd']),
}


class Executor:
    def __init__(self, ia, kg):
        self.ia = ia; self.kg = kg
    def gerar(self, tipo, kwargs_str=''):
        if tipo not in TEMPLATES: return f'Tipo: {", ".join(TEMPLATES.keys())}'
        info = TEMPLATES[tipo]; t = info[0]; blanks = info[1]
        kwargs = {}
        if kwargs_str:
            partes = kwargs_str.split()
            for i,b in enumerate(blanks):
                if i < len(partes): kwargs[b] = partes[i]
        rest = [b for b in blanks if b not in kwargs]
        if rest:
            prompt = f"Preencha para {tipo}:\n" + '\n'.join(f"  {b}: " for b in rest)
            r = self.ia.gerar(prompt)
            if r:
                for line in r.split('\n'):
                    for b in rest:
                        if line.lower().startswith(b.lower()+':'):
                            v = line.split(':',1)[1].strip().strip('"\'')
                            if v and v.lower() not in ('none','null',''): kwargs[b] = v
        padroes = {'nome':tipo,'saudacao':'Ola!','item_id':'101','item_preco':'50',
                   'hp':'200','atk':'20','def':'10','loot_id':'201','loot_chance':'0.3',
                   'desc':'Descricao','obj':'Objetivo','xp':'500','id':'1001','tipo':'quest',
                   'peso':'5','elem':'fire','dano':'100','mana':'50','cd':'5'}
        for b in blanks:
            if b not in kwargs: kwargs[b] = padroes.get(b, f'[{b}]')
        try: resultado = t.format(**kwargs)
        except KeyError as e: return f'Erro no template: {e}'
        nome_arq = kwargs.get('nome',tipo).replace(' ','_')[:20]
        path = os.path.join(SANDBOX,f'chat_{tipo}_{nome_arq}.lua')
        with open(path,'w',encoding='utf-8') as f: f.write(resultado)
        self.kg.data['metricas']['geracoes'] +=1; self.kg.salvar()
        return f'[OK] {path}\n{resultado[:200]}'
    def lore(self, tipo, nome):
        prompt = f"Crie lore para {tipo} '{nome}'. Seja criativo e detalhado (3-5 frases)."
        r = self.ia.gerar(prompt, 0.8)
        if r:
            path = os.path.join(SANDBOX,f'chat_lore_{tipo}_{nome[:15]}.txt')
            with open(path,'w',encoding='utf-8') as f: f.write(r)
            return f'[OK] Lore salvo\n{r[:300]}'
        return '[ERRO] Falha ao gerar lore'
    def perguntar(self, texto):
        ctx_parts = self.kg.buscar(texto)
        ctx = ''
        if ctx_parts:
            ctx = 'Conhecimento relevante:\n' + '\n'.join(f'- {l["erro"]}: {l["solucao"]}' for l in ctx_parts) + '\n\n'
        prompt = f"{ctx}Usuario: {texto}\n\nAssistente MCR-DevIA:"
        r = self.ia.gerar(prompt)
        return r or '[ERRO]'
    def compilar(self, projeto='canary'):
        msbuild_paths = [
            r'C:\Program Files\Microsoft Visual Studio\2026\Community\MSBuild\Current\Bin\amd64\MSBuild.exe',
            r'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\amd64\MSBuild.exe',
        ]
        msbuild = None
        for p in msbuild_paths:
            if os.path.exists(p): msbuild = p; break
        if not msbuild: return '[ERRO] MSBuild nao encontrado'
        slns = {'canary': r'E:\Projeto MCR\Canary\vcproj\canary.sln',
                'otclient': r'E:\Projeto MCR\OTClient\vc17\otclient-vc17.sln'}
        sln = slns.get(projeto)
        if not sln or not os.path.exists(sln): return f'[ERRO] Solucao {projeto} nao encontrada'
        import subprocess
        try:
            r = subprocess.run(f'"{msbuild}" "{sln}" /p:Configuration=Release /p:Platform=x64 /t:Build /m',
                             capture_output=True,text=True,shell=True,timeout=600)
            erros = [l for l in (r.stdout+r.stderr).split('\n') if any(e in l for e in ['error','fatal','LNK'])]
            if r.returncode==0 and not erros: return '[OK] Compilado com sucesso!'
            return f'[ERRO] {len(erros)} erros\n{chr(10).join(erros[:3])}'
        except Exception as e: return f'[ERRO] {e}'


# ============================================================
# CHAT INTERATIVO
# ============================================================

class Chat:
    def __init__(self):
        self.ia = IA()
        self.kg = KG()
        self.exec = Executor(self.ia, self.kg)
        self.modo = 'chat'
        self.historico = []
        self.todos = []
        self._carregar_historico()
    
    def _carregar_historico(self):
        if os.path.exists(HIST_PATH):
            with open(HIST_PATH,'r',encoding='utf-8') as f:
                data = json.load(f)
                self.historico = data.get('historico',[])
                self.todos = data.get('todos',[])
    
    def _salvar_historico(self):
        with open(HIST_PATH,'w',encoding='utf-8') as f:
            json.dump({'historico':self.historico[-100:],'todos':self.todos},f,ensure_ascii=False,indent=2)
    
    def _cabeçalho(self):
        m = self.kg.data['metricas']
        self._limpar()
        print(f'{CIANO}{NEGRITO}{"="*60}{RESET}')
        print(f'{CIANO}  MCR-DevIA CHAT  |  Modo: [{self.modo.upper()}]  |  V{self.kg.data["versoes"]}{RESET}')
        print(f'{AZUL}  {m["licoes"]} licoes | {m["geracoes"]} geracoes | {m["compilacoes"]} compilacoes{RESET}')
        print(f'{CIANO}{"="*60}{RESET}')
        print(f'{AMARELO}  Comandos: /modo chat|build|plan  /limpar  /todos  /sair{RESET}')
        print()
    
    def _limpar(self):
        os.system('cls' if os.name=='nt' else 'clear')
    
    def _processar_comando(self, cmd):
        if cmd == '/sair': return False
        if cmd == '/limpar': self._cabeçalho(); return True
        if cmd.startswith('/modo '):
            m = cmd[6:].strip().lower()
            if m in ('chat','build','plan'):
                self.modo = m
                print(f'  Modo alterado para: {m.upper()}')
            return True
        if cmd == '/todos':
            if self.todos:
                print(f'{AMARELO}TODOS:{RESET}')
                for i,t in enumerate(self.todos,1):
                    status = '[x]' if t.get('done') else '[ ]'
                    print(f'  {status} {i}. {t.get("texto","")}')
            else:
                print('  Nenhum todo.')
            return True
        if cmd.startswith('/todo '):
            self.todos.append({'texto':cmd[6:].strip(),'done':False,'data':str(datetime.datetime.now())[:10]})
            self._salvar_historico()
            print(f'  Todo adicionado.')
            return True
        if cmd.startswith('/done '):
            idx = int(cmd[6:].strip())-1
            if 0 <= idx < len(self.todos):
                self.todos[idx]['done'] = True
                self._salvar_historico()
                print(f'  Todo #{idx+1} concluido!')
            return True
        return None  # Nao e comando
    
    def _processar_mensagem(self, msg):
        self.historico.append({'role':'user','msg':msg,'modo':self.modo,'data':str(datetime.datetime.now())})
        
        if self.modo == 'build':
            # Interpreta como acao
            msg_lower = msg.lower()
            if 'gerar' in msg_lower or 'criar' in msg_lower or 'npc' in msg_lower:
                for tipo in TEMPLATES:
                    if tipo in msg_lower:
                        # Extrai nome (palavra depois do tipo)
                        partes = msg.split()
                        for i,p in enumerate(partes):
                            if p.lower() == tipo and i+1 < len(partes):
                                kwargs = partes[i+1] if i+1 < len(partes) else ''
                                resp = self.exec.gerar(tipo, kwargs)
                                self.historico.append({'role':'assistant','msg':resp})
                                return resp
                resp = self.exec.gerar('npc', '')
                self.historico.append({'role':'assistant','msg':resp})
                return resp
            elif 'lore' in msg_lower:
                tipo = 'npc'
                nome = 'Personagem'
                for t in ['npc','item','local']:
                    if t in msg_lower: tipo = t
                # Tenta extrair nome
                partes = msg.split()
                for i,p in enumerate(partes):
                    if p.lower() == 'chamado' and i+1 < len(partes):
                        nome = partes[i+1]; break
                resp = self.exec.lore(tipo, nome)
                self.historico.append({'role':'assistant','msg':resp})
                return resp
            elif 'compilar' in msg_lower or 'build' in msg_lower:
                proj = 'canary'
                if 'otclient' in msg_lower: proj = 'otclient'
                resp = self.exec.compilar(proj)
                self.historico.append({'role':'assistant','msg':resp})
                return resp
            else:
                resp = self.exec.perguntar(msg)
                self.historico.append({'role':'assistant','msg':resp})
                return resp
        
        elif self.modo == 'plan':
            # Modo planejamento: IA pensa na estrutura
            ctx_parts = self.kg.buscar(msg)
            ctx = ''
            if ctx_parts:
                ctx = 'Baseado em experiencias anteriores:\n' + '\n'.join(f'- {l["solucao"]}' for l in ctx_parts) + '\n\n'
            prompt = f"{ctx}Voce e um arquiteto de sistemas para o projeto MCR (Tibia).\n\n"
            prompt += f"O usuario quer: {msg}\n\n"
            prompt += "Pense na estrutura necessaria:\n"
            prompt += "- Quantos NPCs? (nomes, papeis)\n"
            prompt += "- Quantos monsters? (stats aproximados)\n"
            prompt += "- Quantos itens? (IDs, tipos)\n"
            prompt += "- Ha quest envolvida?\n"
            prompt += "- Ha lore necessario?\n\n"
            prompt += "Responda de forma CONCRETA e ACAO-VEL."
            resp = self.ia.gerar(prompt, 0.8)
            self.historico.append({'role':'assistant','msg':resp})
            return resp
        
        else:  # chat
            ctx_parts = self.kg.buscar(msg)
            ctx = ''
            if ctx_parts:
                ctx = 'Conhecimento relevante:\n' + '\n'.join(f'- {l["solucao"]}' for l in ctx_parts) + '\n\n'
            prompt = f"{ctx}Historico recente:\n"
            for h in self.historico[-4:]:
                papel = 'Usuario' if h['role']=='user' else 'Assistente'
                prompt += f"{papel}: {h['msg'][:100]}\n"
            prompt += f"\nAssistente MCR-DevIA (responda de forma natural e util):"
            resp = self.ia.gerar(prompt)
            self.historico.append({'role':'assistant','msg':resp})
            return resp
    
    def rodar(self):
        self._cabeçalho()
        print(f'{VERDE}MCR-DevIA pronto! Como posso ajudar?{RESET}\n')
        
        while True:
            try:
                entrada = input(f'{NEGRITO}{MAGENTA}MCR-DevIA [{self.modo.upper()}]> {RESET}').strip()
            except (EOFError, KeyboardInterrupt):
                print('\nAte logo!')
                break
            
            if not entrada: continue
            
            # Comando?
            if entrada.startswith('/'):
                if not self._processar_comando(entrada): break
                continue
            
            # Mensagem
            resp = self._processar_mensagem(entrada)
            print(f'\n{AZUL}{NEGRITO}MCR-DevIA:{RESET} {AZUL}{resp[:500]}{RESET}\n')
            
            self._salvar_historico()


if __name__ == '__main__':
    chat = Chat()
    chat.rodar()
