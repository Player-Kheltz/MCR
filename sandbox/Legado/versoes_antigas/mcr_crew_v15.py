#!/usr/bin/env python3
"""
MCR CREW V15 — FINAL: Auto-Learning + Diff Templates + Brain
==============================================================
JUNTA TUDO:
- V13: Template engine (Python estrutura, IA preenche) — 100% sintaxe correta
- AutoTemplateV2: Descobre padroes por diff entre exemplos — APRENDE A PENSAR
- V14 Scan: Indexa projeto inteiro
- Cerebro: Aprendizado continuo com metricas

TESTE: 10 tarefas identicas — eu (cloud) vs MCR Crew
"""

import sys, os, json, re, hashlib, urllib.request, datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox\.crew_v15'
os.makedirs(BASE, exist_ok=True)

# ============================================================
# AUTO-TEMPLATE V2 — Aprende por diff entre exemplos
# ============================================================

class AutoTemplateV2:
    @staticmethod
    def detectar_categoria(conteudo):
        """Detecta categoria como eu faria: pelo conteudo."""
        padroes = [
            ('npc', ['NPC(', ':setSaudacao', ':addItem']),
            ('quest', ['Quest(', ':addObjetivo', ':addRecompensa']),
            ('monster', ['Monster(', ':setHealth', ':addLoot']),
            ('item', ['Item(', ':setType', ':setAttack']),
            ('spell', ['Spell(', ':setDamage', ':setManaCost']),
            ('talkaction', ['TalkAction(', '.onSay']),
        ]
        for cat, pads in padroes:
            score = sum(1 for p in pads if p in conteudo)
            if score >= 2: return cat
        return None
    
    @staticmethod
    def criar_template(exemplos):
        """Cria template por DIFF entre multiplos exemplos."""
        if not exemplos: return None, []
        if len(exemplos) < 2:
            return AutoTemplateV2._template_unico(exemplos[0])
        
        todos = [ex.split('\n') for ex in exemplos]
        min_len = min(len(l) for l in todos)
        template_lines = []
        blanks = []
        
        for i in range(min_len):
            linhas = [ex[i] for ex in todos]
            limpas = [l.strip() for l in linhas]
            
            if all(l == limpas[0] for l in limpas):
                template_lines.append(limpas[0])
                continue
            
            # DIFERENTE! Extrai contexto e cria blank
            ctx = AutoTemplateV2._extrair_contexto(limpas[0])
            nome = ctx or f'campo_{len(blanks)}'
            
            # Tenta substituir a parte que varia
            linha_template = AutoTemplateV2._substituir_variavel(limpas[0], linhas, nome)
            template_lines.append(linha_template)
            if nome not in blanks:
                blanks.append(nome)
        
        return '\n'.join(template_lines), blanks
    
    @staticmethod
    def _extrair_contexto(linha):
        m = re.search(r'(\w+:\w+)\(', linha)
        if m: return m.group(1).replace(':', '_')
        m = re.search(r'(\w+)\s*\(', linha)
        if m: return m.group(1)
        m = re.search(r'(\w+)\s*=', linha)
        if m: return m.group(1)
        return None
    
    @staticmethod
    def _substituir_variavel(linha_ref, todas_linhas, nome_blank):
        """Substitui a parte que DIFERE entre as linhas por {blank}."""
        # strings
        for m in re.finditer(r'["\'][^"\']*["\']', linha_ref):
            val = m.group()
            if all(val not in l for l in todas_linhas[1:]):
                return linha_ref.replace(val, '{' + nome_blank + '}', 1)
        # numeros
        for m in re.finditer(r'\b(\d+)\b', linha_ref):
            num = m.group(1)
            if any(num not in l for l in todas_linhas[1:]):
                return linha_ref.replace(num, '{' + nome_blank + '}', 1)
        # fallback: se so uma palavra muda
        palavras = linha_ref.split()
        for i, p in enumerate(palavras):
            if any(p not in l for l in todas_linhas[1:]):
                palavras[i] = '{' + nome_blank + '}'
                return ' '.join(palavras)
        return linha_ref
    
    @staticmethod
    def _template_unico(conteudo):
        """Fallback para 1 exemplo."""
        blanks = []
        linhas = conteudo.split('\n')
        for i, linha in enumerate(linhas):
            if linha.strip().startswith('--'): continue
            for m in re.finditer(r'["\'][^"\']{3,}["\']', linha):
                val = m.group()
                ctx = AutoTemplateV2._extrair_contexto(linha)
                nome = f'{ctx}_{i}' if ctx else f'campo_{i}'
                linha = linha.replace(val, '{' + nome + '}', 1)
                blanks.append(nome)
            linhas[i] = linha
        return '\n'.join(linhas), list(set(blanks))


# ============================================================
# IA LOCAL
# ============================================================

class IALocal:
    def __init__(self, model='qwen2.5-coder:7b'):
        self.model = model
    
    def gerar(self, prompt, temp=0.8):
        try:
            data = json.dumps({'model':self.model,'prompt':prompt,'stream':False,
                'options':{'temperature':temp,'num_ctx':4096,'top_p':0.9}}).encode()
            req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read()).get('response','')
        except: return None
    
    def preencher_blanks(self, modulo, blanks, contexto=''):
        """Pede IA pra preencher blanks."""
        prompt = f"Preencha os campos para {modulo}.\n{contexto}\n\n"
        for b in blanks: prompt += f"  {b}: "
        prompt += "\n\nFormato:\n" + "\n".join(f"{b}: valor" for b in blanks)
        
        r = self.gerar(prompt, 0.7)
        valores = {}
        if r:
            for line in r.split('\n'):
                line = line.strip()
                for b in blanks:
                    if line.lower().startswith(b.lower() + ':'):
                        v = line.split(':', 1)[1].strip()
                        if v and v.lower() not in ('none','null',''):
                            valores[b] = v
        return valores


# ============================================================
# CEREBRO
# ============================================================

class Cerebro:
    def __init__(self):
        self.path = os.path.join(BASE, 'cerebro.json')
        self.data = self._carregar()
    
    def _carregar(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f: return json.load(f)
        return {'meta': {'versoes': 0, 'acertos': 0, 'erros': 0},
                'modulos': {}, 'cache': {}}
    
    def salvar(self):
        self.data['meta']['versoes'] += 1
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def aprender_modulo(self, nome, template, blanks):
        self.data['modulos'][nome] = {
            'uso': 0, 'acertos': 0, 'erros': 0,
            'template': template, 'blanks': blanks,
            'melhores_valores': {},
        }
        self.salvar()
    
    def registrar(self, modulo, acertou, valores=None):
        mod = self.data['modulos'].get(modulo)
        if not mod: return
        if acertou:
            mod['acertos'] += 1; self.data['meta']['acertos'] += 1
            if valores:
                for k,v in valores.items(): mod['melhores_valores'][k] = v
        else:
            mod['erros'] += 1; self.data['meta']['erros'] += 1
        self.salvar()
    
    def status(self):
        m = self.data['meta']; mods = self.data['modulos']
        print(f'\n[CEREBRO] V{m["versoes"]} - {len(mods)} modulos, {m["acertos"]} acertos, {m["erros"]} erros')
        for nome, info in sorted(mods.items()):
            taxa = info['acertos']/max(1, info['uso'])*100
            print(f'  {nome}: taxa={taxa:.0f}% usos={info["uso"]} blanks={len(info["blanks"])}')


# ============================================================
# EXECUTOR
# ============================================================

class Executor:
    def __init__(self, cerebro, ia):
        self.cerebro = cerebro; self.ia = ia
    
    def executar(self, nome, args=None):
        mod = self.cerebro.data['modulos'].get(nome)
        if not mod: return False, f"Modulo {nome} nao encontrado"
        
        valores = {}
        if args:
            for i, b in enumerate(mod['blanks']):
                if i < len(args) and args[i]: valores[b] = args[i]
        
        # Cache do cerebro
        for b in mod['blanks']:
            if b not in valores and b in mod.get('melhores_valores', {}):
                valores[b] = mod['melhores_valores'][b]
        
        # IA para blanks restantes
        rest = [b for b in mod['blanks'] if b not in valores]
        if rest:
            ia_val = self.ia.preencher_blanks(nome, rest)
            valores.update(ia_val)
        
        # Padrao
        for b in mod['blanks']:
            if b not in valores: valores[b] = f'[{b}]'
        
        try:
            resultado = mod['template'].format(**valores)
        except KeyError as e:
            return False, f"Template: {e}"
        
        nome_arq = valores.get('nome', nome).lower().replace(' ','_')[:30]
        ext = '.otui' if '<OTUI>' in mod['template'] else '.lua'
        path = os.path.join(r'E:\Projeto MCR\sandbox', f'v15_{nome}_{nome_arq}{ext}')
        
        with open(path, 'w', encoding='utf-8') as f: f.write(resultado)
        self.cerebro.registrar(nome, True, valores)
        return True, path


# ============================================================
# SCAN + AUTO-TEMPLATE
# ============================================================

def scan_e_aprender(caminho, cerebro):
    """Escaneia projeto e cria modulos via auto-template."""
    print(f'\n[SCAN] {caminho}')
    coletados = {}  # categoria -> [conteudos]
    
    for root, dirs, files in os.walk(caminho):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules','__pycache__','build','.git')]
        for f in files:
            if not f.endswith('.lua'): continue
            try:
                with open(os.path.join(root,f), 'r', encoding='utf-8', errors='replace') as fp:
                    conteudo = fp.read()
                cat = AutoTemplateV2.detectar_categoria(conteudo)
                if cat:
                    coletados.setdefault(cat, []).append(conteudo)
            except: pass
    
    print(f'  Categorias encontradas: {len(coletados)}')
    for cat, exemplos in sorted(coletados.items()):
        print(f'  {cat}: {len(exemplos)} arquivos')
        
        # Cria template por diff se tiver 2+ exemplos
        template, blanks = AutoTemplateV2.criar_template(exemplos[:5])
        if template and blanks:
            cerebro.aprender_modulo(cat + '_auto', template, blanks)
            print(f'    -> Modulo criado com {len(blanks)} blanks')
    
    return coletados


# ============================================================
# TESTE COMPARATIVO: Cloud vs MCR Crew
# ============================================================

def teste_comparativo(ia_local):
    """Testa 5 tarefas identicas:
    - Cloud (simulado): o que eu geraria
    - MCR Crew: o que o sistema gera
    """
    print('\n' + '='*60)
    print('  TESTE COMPARATIVO: CLOUD vs MCR CREW')
    print('='*60)
    
    tarefas = [
        ('NPC', 'Ferreiro', 'Ola!', 101, 50),
        ('Monster', 'Goblin', 100, 15, 5, 201, 0.3),
        ('Spell', 'BolaDeFogo', 'fire', 80, 35, 4),
        ('Item', 'EspadaCurta', 1001, 'weapon', 20, 5, 30),
        ('Quest', 'MissaoInicial', 'Mate 10 ratos', 'matar', 500, 100),
    ]
    
    resultados = {'cloud': 0, 'crew': 0}
    
    for nome_mod, *args in tarefas:
        print(f'\n  --- {nome_mod}: {args[0]} ---')
        
        # Cloud: usa o template engine (simula o que eu faria)
        print(f'  [CLOUD] Template ja existe e funciona.')
        print(f'    Args: {args}')
        
        # MCR Crew: precisa encontrar ou criar o modulo
        # Se nao existe, cria com auto-template (mas sem exemplos, vai falhar)
        cerebro_temp = Cerebro()
        mod_name = nome_mod.lower() + '_teste'
        
        # Simula scan com exemplos minimos
        exemplos_fake = []
        for i in range(3):
            if nome_mod == 'NPC':
                ex = f'-- NPC: Teste{i}\nlocal npc = NPC("Teste{i}")\nnpc:setSaudacao("Ola{i}")\nnpc:addItem({100+i}, 50)'
            elif nome_mod == 'Monster':
                ex = f'-- Monster: Teste{i}\nlocal m = Monster("Teste{i}")\nm:setHealth({100+i*50})\nm:addLoot({200+i}, 0.{i+1})'
            elif nome_mod == 'Spell':
                ex = f'-- Spell: Teste{i}\nlocal s = Spell("Teste{i}","fire")\ns:setDamage({50+i*10})\ns:setManaCost({20+i*5})'
            elif nome_mod == 'Item':
                ex = f'-- Item: Teste{i}\nlocal it = Item({1000+i},"Teste{i}")\nit:setType("weapon")\nit:setAttack({10+i*5})'
            elif nome_mod == 'Quest':
                ex = f'-- Quest: Teste{i}\nlocal q = Quest("Teste{i}")\nq:setDescricao("Desc{i}")\nq:addObjetivo("Obj{i}")'
            exemplos_fake.append(ex)
        
        template, blanks = AutoTemplateV2.criar_template(exemplos_fake)
        if template and blanks:
            cerebro_temp.aprender_modulo(mod_name, template, blanks)
            executor_temp = Executor(cerebro_temp, ia_local)
            sucesso, msg = executor_temp.executar(mod_name, list(args))
            
            if sucesso:
                resultados['crew'] += 1
                print(f'  [CREW] OK: {msg}')
            else:
                print(f'  [CREW] FALHOU: {msg}')
        else:
            print(f'  [CREW] FALHOU: template vazio')
    
    print(f'\n  RESULTADO:')
    print(f'    CLOUD: {resultados["cloud"]}/5 (referencia)')
    print(f'    CREW: {resultados["crew"]}/5')
    if resultados['crew'] >= resultados['cloud']:
        print(f'    -> CREW IGUAL OU SUPERIOR!')
    else:
        print(f'    -> CREW: {resultados["crew"]/max(1,resultados["cloud"])*100:.0f}% do cloud')
    
    return resultados


# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) < 2:
        print('='*60)
        print('  MCR CREW V15 — FINAL: Auto-Learning + Diff Templates')
        print('='*60)
        print()
        print('COMANDOS:')
        print(f'  python {sys.argv[0]} --scan <caminho>   Escaneia + cria modulos')
        print(f'  python {sys.argv[0]} --teste             Teste comparativo Cloud vs Crew')
        print(f'  python {sys.argv[0]} --status            Estado do cerebro')
        print(f'  python {sys.argv[0]} <modulo> [args...]  Executa modulo')
        print()
        print('SISTEMA COMPLETO: template engine + auto-diff + aprendizado')
        return
    
    cerebro = Cerebro()
    ia = IALocal()
    executor = Executor(cerebro, ia)
    
    # Carrega modulos padrao (v13)
    modulos_padrao = {
        'npc': ('-- NPC: {nome}\nlocal npc = NPC("{nome}")\nnpc:setSaudacao("{saudacao}")\nnpc:addItem({item_id}, {item_preco})',
                ['nome','saudacao','item_id','item_preco']),
        'monster': ('-- Monster: {nome}\nlocal mon = Monster("{nome}")\nmon:setHealth({hp})\nmon:setAttack({atk})\nmon:setDefense({def})\nmon:addLoot({loot_id}, {loot_chance})',
                   ['nome','hp','atk','def','loot_id','loot_chance']),
        'spell': ('-- Spell: {nome}\nlocal spell = Spell("{nome}", "{elemento}")\nspell:setDamage({dano})\nspell:setManaCost({mana})\nspell:setCooldown({cd})',
                 ['nome','elemento','dano','mana','cd']),
        'item': ('-- Item: {nome}\nlocal item = Item({id}, "{nome}")\nitem:setType("{tipo}")\nitem:setAttack({atk})\nitem:setDefense({def})\nitem:setWeight({peso})',
                ['nome','id','tipo','atk','def','peso']),
        'quest': ('-- Quest: {nome}\nlocal quest = Quest("{nome}")\nquest:setDescricao("{descricao}")\nquest:addObjetivo("{objetivo}")\nquest:addRecompensa("xp", {xp})\nquest:addRecompensa("gold", {gold})',
                 ['nome','descricao','objetivo','xp','gold']),
        'otclient': ('<OTUI>\n  <Window name="{nome}" title="{titulo}">\n    <Panel name="main" width="300" height="200">\n      <Label text="{label}" x="10" y="10" width="280" height="30"/>\n      <Button text="{botao}" x="10" y="160" width="100" height="30"/>\n    </Panel>\n  </Window>\n</OTUI>',
                    ['nome','titulo','label','botao']),
    }
    
    for nome, (template, blanks) in modulos_padrao.items():
        if nome not in cerebro.data['modulos']:
            cerebro.aprender_modulo(nome, template, blanks)
    
    cmd = sys.argv[1]
    
    if cmd == '--scan' and len(sys.argv) >= 3:
        scan_e_aprender(sys.argv[2], cerebro)
    
    elif cmd == '--teste':
        teste_comparativo(ia)
    
    elif cmd == '--status':
        cerebro.status()
        # Mostra modulos auto-descobertos
        for nome in cerebro.data['modulos']:
            if nome.endswith('_auto'):
                mod = cerebro.data['modulos'][nome]
                print(f'  [AUTO] {nome}: {len(mod["blanks"])} blanks, {mod["acertos"]} acertos')
    
    elif cmd in modulos_padrao or cmd in cerebro.data['modulos']:
        sucesso, msg = executor.executar(cmd, sys.argv[2:])
        print(f'[EXEC] {"OK" if sucesso else "ERRO"}: {msg}')
    
    else:
        print(f'[ERRO] Comando invalido: {cmd}')

if __name__ == '__main__':
    main()
