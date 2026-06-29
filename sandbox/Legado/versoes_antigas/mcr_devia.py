#!/usr/bin/env python3
"""
MCR-DevIA — UNIFIED SYSTEM
============================
Tudo que o MCR-DevIA sabe fazer, num comando so.

Uso: python mcr_devia.py <comando> [args...]

COMANDOS:
  gerar     <tipo> [args...]    Gera NPC, quest, item, monster, spell
  lore      <tipo> <nome>       Gera lore profundo
  compilar  <projeto>           Compila e corrige automaticamente
  ensinar   <erro> <causa> <sol> Aprende uma nova licao
  perguntar <texto>             Responde com RAG + auto-supervisao
  status                        Mostra tudo que sabe
"""

import sys, os, json, re, hashlib, urllib.request, subprocess, shutil, datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR'
SANDBOX = r'E:\Projeto MCR\sandbox'
KG_DIR = os.path.join(SANDBOX, '.mcr_devia')
os.makedirs(KG_DIR, exist_ok=True)
KG_PATH = os.path.join(KG_DIR, 'knowledge.json')

# ============================================================
# KNOWLEDGE GRAPH — O cerebro
# ============================================================

class KnowledgeGraph:
    def __init__(self):
        self.path = KG_PATH
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'versoes': 0, 'licoes': self._licoes_iniciais(), 'index': {},
            'metricas': {'licoes': 12, 'usos': 0, 'geracoes': 0, 'compilacoes': 0}
        }
    
    def _licoes_iniciais(self):
        return [
            {'id':'L001','erro':'LNK2001 __std_*','causa':'ABI mismatch VS 2022 vs 2026','solucao':'Usar VS 2026 (toolset v145)','ctx':'compilar'},
            {'id':'L002','erro':'D9002 /std:c++latest','causa':'stdcpp23 no MSVC 14.41','solucao':'Mudar para stdcpp20 no vcxproj','ctx':'compilar'},
            {'id':'L003','erro':'string_view::contains','causa':'contains() e C++23, codigo usa C++20','solucao':'Substituir por find() != npos','ctx':'compilar'},
            {'id':'L004','erro':'canary-sln.exe ocupado','causa':'Processo rodando em BG','solucao':'taskkill /f /im canary-sln.exe','ctx':'runtime'},
            {'id':'L005','erro':'passiva nil value 40007','causa':'habilidade SHC sem efeito()','solucao':'Verificar hab.efeito antes de chamar','ctx':'runtime'},
            {'id':'L006','erro':'Bun crash GPU','causa':'Bun 1.3.14 + NVIDIA','solucao':'Downgrade OpenCode 1.17.9','ctx':'ferramenta'},
            {'id':'L007','erro':'HABILIDADES vazio','causa':'Arquivos de habilidade nao carregados','solucao':'Adicionar dofile no init','ctx':'runtime'},
            {'id':'L008','erro':'Motor sem tipos','causa':'projectile/melee/cone nao existiam','solucao':'Adicionar 9 tipos ao motor','ctx':'runtime'},
            {'id':'L009','erro':'IA gera em ingles','causa':'Qwen 7B tem bias ingles','solucao':'Detector de ingles + fallback tematico','ctx':'geracao'},
            {'id':'L010','erro':'Chaves Lua desbalanceadas','causa':'Template fechava na linha errada','solucao':'Abrir/fechar em linhas separadas','ctx':'geracao'},
            {'id':'L011','erro':'PowerShell Unicode','causa':'cp1252 encoding','solucao':'Nao usar emojis em prints','ctx':'ferramenta'},
            {'id':'L012','erro':'IA nao segue JSON','causa':'Modelo 7B tem dificuldade','solucao':'Usar formato TEXTO (NOME: valor)','ctx':'geracao'},
        ]
    
    def salvar(self):
        self.data['versoes'] += 1
        self.data['metricas']['licoes'] = len(self.data['licoes'])
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def buscar(self, texto, max_r=3):
        palavras = set(re.findall(r'\w+', texto.lower()))
        scores = []
        for l in self.data['licoes']:
            alvo = (l['erro']+' '+l['causa']+' '+l['solucao']).lower()
            score = sum(3 if p in l['erro'].lower() else 2 if p in l['causa'].lower() else 1 
                       for p in palavras if len(p) > 3 and p in alvo)
            if score > 0: scores.append((score, l))
        scores.sort(key=lambda x: -x[0])
        return [s[1] for s in scores[:max_r]]
    
    def aprender(self, erro, causa, solucao, ctx='geral'):
        self.data['licoes'].append({
            'id':f'L{len(self.data["licoes"])+1:04d}','erro':erro,'causa':causa,
            'solucao':solucao,'ctx':ctx,'usos':0})
        self.salvar()
        print(f'  [APRENDIDO] "{erro[:50]}..."')


# ============================================================
# IA LOCAL
# ============================================================

class IA:
    def gerar(self, prompt, temp=0.7):
        try:
            d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
                'options':{'temperature':temp,'num_ctx':4096,'top_p':0.95}}).encode()
            r = urllib.request.Request(OLLAMA_URL, data=d, headers={'Content-Type':'application/json'})
            return json.loads(urllib.request.urlopen(r, timeout=120).read()).get('response','')
        except: return None


# ============================================================
# TEMPLATE ENGINE (V12-V15)
# ============================================================

TEMPLATES = {
    'npc': ('-- NPC: {nome}\nlocal npc = NPC("{nome}")\nnpc:setSaudacao("{saudacao}")\nnpc:addItem({item_id}, {item_preco})\nprint("NPC {nome} carregado.")',
            ['nome','saudacao','item_id','item_preco']),
    'monster': ('-- Monster: {nome}\nlocal mon = Monster("{nome}")\nmon:setHealth({hp})\nmon:setAttack({atk})\nmon:setDefense({def})\nmon:addLoot({loot_id}, {loot_chance})\nprint("Monster {nome} carregado.")',
                ['nome','hp','atk','def','loot_id','loot_chance']),
    'quest': ('-- Quest: {nome}\nlocal quest = Quest("{nome}")\nquest:setDescricao("{desc}")\nquest:addObjetivo("{obj}")\nquest:addRecompensa("xp", {xp})\nprint("Quest {nome} carregada.")',
              ['nome','desc','obj','xp']),
    'item': ('-- Item: {nome}\nlocal item = Item({id}, "{nome}")\nitem:setType("{tipo}")\nitem:setAttack({atk})\nitem:setDefense({def})\nitem:setWeight({peso})\nprint("Item {nome} carregado.")',
             ['nome','id','tipo','atk','def','peso']),
    'spell': ('-- Spell: {nome}\nlocal spell = Spell("{nome}", "{elem}")\nspell:setDamage({dano})\nspell:setManaCost({mana})\nspell:setCooldown({cd})\nprint("Spell {nome} carregada.")',
              ['nome','elem','dano','mana','cd']),
}

class Gerador:
    def __init__(self, ia, kg):
        self.ia = ia; self.kg = kg
    
    def gerar(self, tipo, args_str):
        if tipo not in TEMPLATES:
            print(f'Tipos: {", ".join(TEMPLATES.keys())}'); return
        info = TEMPLATES[tipo]; template = info[0]; blanks = info[1]
        args = args_str.split() if isinstance(args_str, str) else []
        
        vals = {}
        for i, b in enumerate(blanks):
            if i < len(args) and args[i]: vals[b] = args[i]
        
        rest = [b for b in blanks if b not in vals]
        if rest:
            ctx_parts = self.kg.buscar(f'gerar {tipo}')
            ctx = ''
            if ctx_parts:
                ctx = 'Baseado em experiencias anteriores:\n' + '\n'.join(f'- {l["solucao"]}' for l in ctx_parts)
            prompt = f"{ctx}\n\nPreencha para {tipo}:\n" + '\n'.join(f"  {b}: " for b in rest)
            r = self.ia.gerar(prompt)
            if r:
                for line in r.split('\n'):
                    for b in rest:
                        if line.lower().startswith(b.lower()+':'):
                            v = line.split(':',1)[1].strip().strip('"\'')
                            if v and v.lower() not in ('none','null',''): vals[b] = v
        
        padroes = {'nome':tipo,'saudacao':'Ola!','item_id':'101','item_preco':'50','hp':'200','atk':'20',
                   'def':'10','loot_id':'201','loot_chance':'0.3','desc':'Descricao','obj':'Objetivo',
                   'xp':'500','id':'1001','tipo':'quest','atk':'0','def':'0','peso':'5',
                   'elem':'fire','dano':'100','mana':'50','cd':'5'}
        for b in blanks:
            if b not in vals: vals[b] = padroes.get(b, f'[{b}]')
        
        try: resultado = template.format(**vals)
        except KeyError as e: print(f'Erro: {e}'); return
        
        path = os.path.join(SANDBOX, f'devia_{tipo}_{vals["nome"][:20]}.lua')
        with open(path, 'w', encoding='utf-8') as f: f.write(resultado)
        print(f'  [OK] {path}')
        self.kg.data['metricas']['geracoes'] += 1; self.kg.salvar()


# ============================================================
# LORE ENGINE (V19)
# ============================================================

class LoreGen:
    def __init__(self, ia): self.ia = ia
    
    def gerar(self, tipo, nome):
        prompts = {
            'npc': f"Crie lore para NPC '{nome}'. HISTORIA: (2 frases) PERSONALIDADE: (3 adjetivos) SAUDACAO: (fala) SEGREDO: (segredo)",
            'item': f"Crie lore para item '{nome}'. ORIGEM: (de onde veio) PODER: (o que faz) LENDA: (o que dizem)",
            'local': f"Crie lore para local '{nome}'. APARENCIA: (como parece) HISTORIA: (o que aconteceu) PERIGO: (o que espreita)",
        }
        prompt = prompts.get(tipo, f"Crie lore sobre {nome}:")
        r = self.ia.gerar(prompt, 0.8)
        if r:
            path = os.path.join(SANDBOX, f'devia_lore_{tipo}_{nome[:15]}.txt')
            with open(path, 'w', encoding='utf-8') as f: f.write(r)
            print(f'  [OK] Lore salvo em {path}')
            # Mostra preview
            for line in r.split('\n')[:4]:
                if line.strip(): print(f'    {line[:100]}')


# ============================================================
# COMPILADOR + CORRETOR
# ============================================================

class Builder:
    def __init__(self, kg, ia):
        self.kg = kg; self.ia = ia
    
    def compilar(self, projeto='canary'):
        msbuild = self._encontrar_msbuild()
        if not msbuild: return
        
        sln_map = {
            'canary': os.path.join(BASE, 'Canary', 'vcproj', 'canary.sln'),
            'otclient': os.path.join(BASE, 'OTClient', 'vc17', 'otclient-vc17.sln'),
        }
        sln = sln_map.get(projeto)
        if not sln or not os.path.exists(sln):
            print(f'[ERRO] Solucao {projeto} nao encontrada'); return
        
        print(f'[COMPILAR] {projeto}...')
        for tentativa in range(1, 4):
            cmd = f'"{msbuild}" "{sln}" /p:Configuration=Release /p:Platform=x64 /t:Build /m 2>&1'
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=600)
                erros = [l for l in (r.stdout+r.stderr).split('\n') if any(e in l for e in ['error','fatal','LNK'])]
                if r.returncode == 0 and not erros:
                    print(f'  [OK] Compilado! Tentativa {tentativa}')
                    self.kg.data['metricas']['compilacoes'] += 1; self.kg.salvar()
                    return
                print(f'  Erros: {len(erros)}')
                if not self._corrigir(erros[:3]):
                    print('  Nao foi possivel corrigir automaticamente.'); return
            except subprocess.TimeoutExpired:
                print('  TIMEOUT'); return
    
    def _encontrar_msbuild(self):
        for path in [
            r'C:\Program Files\Microsoft Visual Studio\2026\Community\MSBuild\Current\Bin\amd64\MSBuild.exe',
            r'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\amd64\MSBuild.exe',
        ]:
            if os.path.exists(path): return path
        print('[ERRO] MSBuild nao encontrado'); return None
    
    def _corrigir(self, erros):
        for erro in erros:
            licoes = self.kg.buscar(erro)
            for l in licoes:
                print(f'  Lição: {l["solucao"][:80]}')
                l['usos'] = l.get('usos',0)+1
                if 'stdcpplatest' in erro and 'stdcpp20' in l['solucao']:
                    for root, dirs, files in os.walk(os.path.join(BASE,'OTClient','vc17')):
                        for f in files:
                            if f.endswith('.vcxproj'):
                                p = os.path.join(root,f)
                                with open(p,'r',encoding='utf-8',errors='replace') as fp:
                                    c = fp.read()
                                if 'stdcpplatest' in c:
                                    shutil.copy2(p,p+'.bak')
                                    with open(p,'w',encoding='utf-8') as fp:
                                        fp.write(c.replace('stdcpplatest','stdcpp20'))
                                    print(f'     [FIX] Aplicado em {f}')
                                    return True
            if not licoes:
                # IA tenta diagnosticar
                prompt = f"SOLUCAO para: {erro[:200]}\n\nResponda: CAUSA: SOLUCAO:"
                r = self.ia.gerar(prompt, 0.4)
                if r:
                    for line in r.split('\n'):
                        if 'CAUSA:' in line: causa = line.split(':',1)[1].strip()
                        elif 'SOLUCAO:' in line: sol = line.split(':',1)[1].strip()
                    if causa and sol:
                        self.kg.aprender(erro[:80], causa, sol, 'compilar')
        return False


# ============================================================
# SUPERVISOR (RAG + Auto-avaliacao)
# ============================================================

class Supervisor:
    def __init__(self, ia, kg):
        self.ia = ia; self.kg = kg
    
    def perguntar(self, texto):
        print(f'[SUPERVISOR] "{texto[:80]}..."')
        contexto = self.kg.buscar(texto)
        ctx = ''
        if contexto:
            ctx = 'Sei disso:\n' + '\n'.join(f'- {l["solucao"]}' for l in contexto) + '\n\n'
        
        for t in range(3):
            prompt = f"{ctx}Pergunta: {texto}\n\nResposta:"
            if t > 0: prompt += f"\n\nFeedback: resposta anterior foi muito curta ou generica. Seja mais especifico."
            
            r = self.ia.gerar(prompt)
            if not r: continue
            
            nota = min(100, len(r.split()) * 2 + (10 if ':' in r else 0) + (20 if len(r) > 200 else 0))
            print(f'  Nota: {nota}/100')
            if nota >= 60:
                print(f'\n{r[:500]}')
                return r
        print('[Supervisor] Nao consegui resposta de qualidade.')


# ============================================================
# MAIN — Orquestrador Unico
# ============================================================

def main():
    kg = KnowledgeGraph()
    ia = IA()
    
    if len(sys.argv) < 2:
        print(__doc__)
        print(f'Licoes: {kg.data["metricas"]["licoes"]} | Geração: {kg.data["metricas"]["geracoes"]}'
              f' | Compilação: {kg.data["metricas"]["compilacoes"]}')
        return
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    if cmd == 'status':
        m = kg.data['metricas']
        print(f'\n[MCR-DevIA] V{kg.data["versoes"]}')
        print(f'  Licoes: {m["licoes"]}')
        print(f'  Gerações: {m["geracoes"]}')
        print(f'  Compilações: {m["compilacoes"]}')
        print(f'  Usos: {m["usos"]}')
        print(f'\nLicoes:')
        for l in kg.data['licoes'][:5]:
            print(f'  {l["id"]}: {l["erro"][:50]}... [{l.get("usos",0)}x]')
        print(f'\nComandos: gerar, lore, compilar, ensinar, perguntar')
    
    elif cmd == 'gerar' and len(args) >= 1:
        tipo = args[0]; resto = ' '.join(args[1:])
        g = Gerador(ia, kg)
        g.gerar(tipo, resto)
    
    elif cmd == 'lore' and len(args) >= 2:
        l = LoreGen(ia)
        l.gerar(args[0], ' '.join(args[1:]))
    
    elif cmd == 'compilar':
        projeto = args[0] if args else 'canary'
        b = Builder(kg, ia)
        b.compilar(projeto)
    
    elif cmd == 'ensinar' and len(args) >= 3:
        kg.aprender(args[0], args[1], args[2], args[3] if len(args) > 3 else 'geral')
    
    elif cmd == 'perguntar' and len(args) >= 1:
        s = Supervisor(ia, kg)
        s.perguntar(' '.join(args))
    
    else:
        print(f'Comando invalido: {cmd}')
        print('Use: gerar, lore, compilar, ensinar, perguntar, status')

if __name__ == '__main__':
    main()
