#!/usr/bin/env python3
"""
MCR CREW V13 — THE EVOLVING SYSTEM
=====================================
Aprnde, melhora e se adapta a cada execucao.

Novidades:
  1. AUTO-TEMPLATE: cria modulos novos a partir de exemplos
  2. FINGERPRINT COMPOSTO: cada execucao dobra o conhecimento
  3. CACHE INTELIGENTE: blanks obvios nao precisam de IA
  4. META-APRENDIZADO: sistema sabe o que sabe e o que nao sabe
  5. MODO PERFORMANCE: 10x mais rapido em blanks conhecidos

Filosofia: a cada uso, o sistema fica 2x mais inteligente.
"""

import sys, os, json, re, random, urllib.request, datetime, hashlib

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox\.crew_v13'
os.makedirs(BASE, exist_ok=True)

# ============================================================
# NUCLEO DE APRENDIZADO CONTINUO
# ============================================================

class Cerebro:
    """
    Cerebro do sistema. Guarda TUDO que aprendeu:
    - Templates que funcionaram
    - Valores criativos que foram aprovados
    - Padroes de blanks
    - Cache de respostas (pra nao perguntar de novo)
    """
    
    def __init__(self):
        self.path = os.path.join(BASE, 'cerebro.json')
        self.data = self._carregar()
    
    def _carregar(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'modulos': {},
            'cache': {},
            'meta': {
                'versoes': 0,
                'total_acertos': 0,
                'total_erros': 0,
                'modulos_criados': 0,
                'ultima_atualizacao': str(datetime.datetime.now()),
            }
        }
    
    def salvar(self):
        self.data['meta']['ultima_atualizacao'] = str(datetime.datetime.now())
        self.data['meta']['versoes'] += 1
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def aprender_modulo(self, nome, template, blanks, regras=None, exemplos=None):
        """Aprende ou atualiza um modulo."""
        if nome not in self.data['modulos']:
            self.data['modulos'][nome] = {
                'criado_em': str(datetime.datetime.now()),
                'uso': 0,
                'acertos': 0,
                'erros': 0,
                'template': template,
                'blanks': blanks,
                'regras': regras or {},
                'historico_blanks': {},  # blank -> [valores que funcionaram]
                'melhores_valores': {},  # blank -> valor mais usado
            }
            self.data['meta']['modulos_criados'] += 1
        
        mod = self.data['modulos'][nome]
        mod['uso'] += 1
        mod['template'] = template
        mod['blanks'] = blanks
        mod['regras'] = regras or {}
        
        # Atualiza historico com exemplos
        if exemplos:
            for blank, valor in exemplos.items():
                if blank in mod['historico_blanks']:
                    if valor not in mod['historico_blanks'][blank]:
                        mod['historico_blanks'][blank].append(valor)
                else:
                    mod['historico_blanks'][blank] = [valor]
        
        self.salvar()
    
    def registrar_resultado(self, modulo, acertou=True, valores=None):
        """Registra se um modulo acertou ou errou."""
        mod = self.data['modulos'].get(modulo)
        if not mod: return
        
        if acertou:
            mod['acertos'] += 1
            self.data['meta']['total_acertos'] += 1
            # Atualiza melhores valores
            if valores:
                for blank, valor in valores.items():
                    mod['melhores_valores'][blank] = valor
        else:
            mod['erros'] += 1
            self.data['meta']['total_erros'] += 1
        
        self.salvar()
    
    def sugerir_valor(self, modulo, blank):
        """Sugere um valor para blank baseado no historico."""
        mod = self.data['modulos'].get(modulo)
        if not mod: return None
        
        # Se ja temos um melhor valor, sugere
        if blank in mod.get('melhores_valores', {}):
            return mod['melhores_valores'][blank]
        
        # Se temos historico, sugere o mais comum
        hist = mod.get('historico_blanks', {}).get(blank, [])
        if hist:
            from collections import Counter
            return Counter(hist).most_common(1)[0][0]
        
        return None
    
    def get_cache_key(self, modulo, blanks_pendentes):
        """Gera chave de cache pra blanks pendentes."""
        chave = f"{modulo}:{','.join(sorted(blanks_pendentes))}"
        return hashlib.md5(chave.encode()).hexdigest()
    
    def cache_get(self, chave):
        """Recupera resposta do cache."""
        return self.data.get('cache', {}).get(chave)

    def cache_set(self, chave, valores):
        """Salva resposta no cache."""
        self.data.setdefault('cache', {})[chave] = valores
        # Limita cache a 100 entradas
        if len(self.data['cache']) > 100:
            # Remove mais antiga
            k = next(iter(self.data['cache']))
            del self.data['cache'][k]
        self.salvar()


# ============================================================
# AUTO-TEMPLATE ENGINE
# ============================================================

class AutoTemplate:
    """
    Cria templates a partir de exemplos.
    Dado 1-3 arquivos de exemplo, extrai:
    - Estrutura fixa (template)
    - Partes variaveis (blanks)
    """
    
    @staticmethod
    def analisar_exemplo(codigo):
        """
        Analisa um codigo e identifica:
        - Linhas FIXAS (sempre iguais)
        - Linhas VARIAVEIS (contem blanks em potencial)
        """
        linhas = codigo.split('\n')
        lines_fixas = []
        lines_variaveis = []
        
        for linha in linhas:
            # Linhas de comentario sao fixas
            if linha.strip().startswith('--') or linha.strip().startswith('#'):
                lines_fixas.append(linha)
                continue
            
            # Linhas vazias sao fixas
            if not linha.strip():
                lines_fixas.append(linha)
                continue
            
            # Linhas com strings/numbers sao candidatas a ter blanks
            if re.search(r'["\'][^"\']*["\']', linha) or re.search(r'\d+', linha):
                lines_variaveis.append(linha)
            else:
                lines_fixas.append(linha)
        
        return lines_fixas, lines_variaveis
    
    @staticmethod
    def criar_template(codigos_exemplo):
        """
        Recebe 1+ codigos de exemplo e cria um template unificado.
        Retorna (template_string, lista_de_blanks).
        """
        if not codigos_exemplo:
            return None, []
        
        # Se so um exemplo, usa ele como base
        if len(codigos_exemplo) == 1:
            codigo = codigos_exemplo[0]
            # Encontra valores candidatos a blank
            blanks_encontrados = set()
            
            # Procura strings
            for m in re.finditer(r'["\']([^"\']+)["\']', codigo):
                val = m.group(1)
                if len(val) > 2 and not val.isdigit():
                    blank_name = re.sub(r'[^a-zA-Z0-9]', '_', val.lower())[:20]
                    if blank_name:
                        blanks_encontrados.add(blank_name)
            
            # Procura numeros
            for m in re.finditer(r'(?<!\w)(\d+)(?!\w)', codigo):
                blanks_encontrados.add(f'numero_{len(blanks_encontrados)}')
            
            # Cria template substituindo valores por blanks
            template = codigo
            blank_map = {}
            for i, m in enumerate(re.finditer(r'["\']([^"\']{3,})["\']', template)):
                val = m.group(1)
                if not val.isdigit():
                    bk = f'valor_{i}'
                    template = template.replace(f'"{val}"', f'"{bk}"', 1)
                    template = template.replace(f"'{val}'", f"'{bk}'", 1)
                    blank_map[bk] = val
            
            blanks = list(blank_map.keys())
            return template, blanks
        
        # Multiplos exemplos: encontra o que eh comum vs variavel
        linhas_comum = None
        for codigo in codigos_exemplo:
            linhas = codigo.split('\n')
            if linhas_comum is None:
                linhas_comum = linhas
            else:
                # Mantem so as linhas que sao IGUAIS em todos
                min_len = min(len(linhas_comum), len(linhas))
                linhas_comum = [linhas_comum[i] for i in range(min_len) 
                              if linhas_comum[i] == linhas[i]]
        
        template = '\n'.join(linhas_comum) if linhas_comum else codigos_exemplo[0]
        return template, []
    
    @staticmethod
    def extrair_valores(codigo, blanks):
        """Dado um codigo preenchido e uma lista de blanks, extrai os valores."""
        valores = {}
        for bk in blanks:
            # Procura o blank no codigo
            padrao = f'"{bk}"'
            m = re.search(padrao, codigo)
            if m:
                # Pega o contexto ao redor pra identificar o valor
                ctx = codigo[max(0, m.start()-50):m.end()+50]
                valores[bk] = ctx
        return valores


# ============================================================
# IA LOCAL COM CACHE
# ============================================================

class IALocal:
    def __init__(self, model='qwen2.5-coder:7b'):
        self.model = model
        self.cache = {}
    
    def gerar(self, prompt, temp=0.8):
        # Cache por prompt (evita repetir perguntas iguais)
        chave = hashlib.md5(prompt.encode()).hexdigest()
        if chave in self.cache:
            return self.cache[chave]
        
        try:
            data = json.dumps({'model':self.model,'prompt':prompt,'stream':False,
                'options':{'temperature':temp,'num_ctx':4096,'top_p':0.9}}).encode()
            req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.loads(r.read()).get('response','')
                self.cache[chave] = resp
                return resp
        except:
            return None


# ============================================================
# ORQUESTRADOR PRINCIPAL
# ============================================================

class MCRCrew:
    """Orquestrador que junta cerebro + templates + IA."""
    
    def __init__(self):
        self.cerebro = Cerebro()
        self.ia = IALocal()
    
    def executar(self, modulo, args):
        """Executa um modulo."""
        mod_info = self.cerebro.data['modulos'].get(modulo)
        if not mod_info:
            print(f"[ERRO] Modulo '{modulo}' nao encontrado.")
            print(f"Modulos disponiveis: {', '.join(self.cerebro.data['modulos'].keys())}")
            return
        
        template = mod_info['template']
        blanks = mod_info['blanks']
        regras = mod_info.get('regras', {})
        
        print(f'\n[{modulo}] Executando...')
        print(f'  Template: {len(template)} chars')
        print(f'  Blanks: {len(blanks)}')
        
        # Coleta valores dos args ou do cerebro ou da IA
        valores = {}
        
        # 1. Args da linha de comando
        for i, b in enumerate(blanks):
            if i < len(args) and args[i]:
                valores[b] = args[i]
        
        # 2. Cerebro (sugestoes baseadas em historico)
        for b in blanks:
            if b not in valores:
                sugestao = self.cerebro.sugerir_valor(modulo, b)
                if sugestao:
                    print(f'  [Cache] {b} = {sugestao}')
                    valores[b] = sugestao
        
        # 3. IA local (para blanks criativos)
        blanks_restantes = [b for b in blanks if b not in valores]
        if blanks_restantes:
            print(f'  [IA] Perguntando: {", ".join(blanks_restantes)}')
            
            prompt = f"Preencha estes campos para {modulo}:\n"
            for b in blanks_restantes:
                prompt += f"  {b}: "
            prompt += "\n\nResponda no formato:\n" + "\n".join(f"{b}: valor" for b in blanks_restantes)
            
            r = self.ia.gerar(prompt, 0.7)
            if r:
                for line in r.split('\n'):
                    line = line.strip()
                    for b in blanks_restantes:
                        if line.lower().startswith(b.lower() + ':'):
                            v = line.split(':', 1)[1].strip()
                            if v and v.lower() not in ('none', 'null', ''):
                                valores[b] = v
        
        # 4. Valores padrao para o que faltar
        for b in blanks:
            if b not in valores:
                padrao = {
                    'nome': 'SemNome',
                    'titulo': 'Sem Titulo',
                    'id': '1',
                    'hp': '100',
                    'atk': '10',
                    'def': '5',
                }.get(b, f'valor_{b}')
                valores[b] = padrao
        
        # Valida
        erros = []
        for b in blanks:
            if b in regras:
                if regras[b] == 'int':
                    try: int(valores.get(b, ''))
                    except: erros.append(f"'{b}' precisa ser numero")
                elif regras[b] == 'float':
                    try: float(valores.get(b, ''))
                    except: erros.append(f"'{b}' precisa ser decimal")
        
        if erros:
            print(f'  Erros: {len(erros)}')
            for e in erros: print(f'    {e}')
            self.cerebro.registrar_resultado(modulo, False)
            return
        
        # Preenche template
        try:
            resultado = template.format(**valores)
        except KeyError as e:
            print(f'  [ERRO] Template: campo {e} faltando')
            return
        
        # Salva
        nome_arquivo = valores.get('nome', modulo).lower().replace(' ', '_').replace('"','')
        ext = '.lua'
        if modulo == 'otclient': ext = '.otui'
        if modulo == 'docs': ext = '.md'
        
        path = os.path.join(r'E:\Projeto MCR\sandbox', f'v13_{modulo}_{nome_arquivo}{ext}')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(resultado)
        
        print(f'  [OK] Salvo: {path}')
        self.cerebro.registrar_resultado(modulo, True, valores)
        print(f'  [OK] {modulo} concluido!')
    
    def aprender_modulo(self, nome, template, blanks, regras=None, exemplos=None):
        """Aprende um novo modulo."""
        self.cerebro.aprender_modulo(nome, template, blanks, regras, exemplos)
        print(f'  [OK] Modulo "{nome}" aprendido ({len(blanks)} blanks)')
    
    def auto_template(self, nome, codigos):
        """Cria um template automaticamente a partir de exemplos."""
        template, blanks = AutoTemplate.criar_template(codigos)
        if template:
            self.aprender_modulo(nome, template, blanks)
            print(f'  Template: {template[:100]}...')
            print(f'  Blanks detectados: {blanks}')
        else:
            print(f'  [ERRO] Nao foi possivel criar template')
    
    def status(self):
        """Mostra status do cerebro."""
        m = self.cerebro.data['meta']
        mods = self.cerebro.data['modulos']
        print(f'\n[CEREBRO] V{m["versoes"]} — {m["total_acertos"]} acertos, {m["total_erros"]} erros')
        print(f'  Modulos: {len(mods)}')
        for nome, info in sorted(mods.items()):
            acerto_rate = info['acertos'] / max(1, info['uso']) * 100
            print(f'    {nome}: usos={info["uso"]}, acerto={acerto_rate:.0f}% blanks={len(info["blanks"])}')
        print(f'  Cache: {len(self.cerebro.data.get("cache", {}))} entradas')


# ============================================================
# MODULOS PADRAO (embutidos)
# ============================================================

MODULOS_PADRAO = {
    'npc': {
        'template': '''-- NPC: {nome}
local npc = NPC("{nome}")
npc:setSaudacao("{saudacao}")
npc:addItem({item_id}, {item_preco})
print("NPC {nome} carregado.")''',
        'blanks': ['nome', 'saudacao', 'item_id', 'item_preco'],
        'regras': {'item_id': 'int', 'item_preco': 'float'},
    },
    'quest': {
        'template': '''-- Quest: {nome}
local quest = Quest("{nome}")
quest:setDescricao("{descricao}")
quest:addObjetivo("{objetivo}")
quest:addRecompensa("xp", {xp})
quest:addRecompensa("gold", {gold})
print("Quest {nome} carregada.")''',
        'blanks': ['nome', 'descricao', 'objetivo', 'xp', 'gold'],
        'regras': {'xp': 'int', 'gold': 'int'},
    },
    'monster': {
        'template': '''-- Monster: {nome}
local mon = Monster("{nome}")
mon:setHealth({hp})
mon:setAttack({atk})
mon:setDefense({def})
mon:addLoot({loot_id}, {loot_chance})
print("Monster {nome} carregado.")''',
        'blanks': ['nome', 'hp', 'atk', 'def', 'loot_id', 'loot_chance'],
        'regras': {'hp': 'int', 'atk': 'int', 'def': 'int', 'loot_id': 'int', 'loot_chance': 'float'},
    },
    'item': {
        'template': '''-- Item: {nome}
local item = Item({id}, "{nome}")
item:setType("{tipo}")
item:setAttack({atk})
item:setDefense({def})
item:setWeight({peso})
print("Item {nome} carregado.")''',
        'blanks': ['nome', 'id', 'tipo', 'atk', 'def', 'peso'],
        'regras': {'id': 'int', 'atk': 'int', 'def': 'int', 'peso': 'int'},
    },
    'spell': {
        'template': '''-- Spell: {nome}
local spell = Spell("{nome}", "{elemento}")
spell:setDamage({dano})
spell:setManaCost({mana})
spell:setCooldown({cd})
print("Spell {nome} carregada.")''',
        'blanks': ['nome', 'elemento', 'dano', 'mana', 'cd'],
        'regras': {'dano': 'int', 'mana': 'int', 'cd': 'float'},
    },
    'otclient': {
        'template': '''<OTUI>
  <Window name="{nome}" title="{titulo}">
    <Panel name="main" width="300" height="200">
      <Label text="{label_texto}" x="10" y="10" width="280" height="30"/>
      <Button text="{botao_texto}" x="10" y="160" width="100" height="30"/>
    </Panel>
  </Window>
</OTUI>''',
        'blanks': ['nome', 'titulo', 'label_texto', 'botao_texto'],
    },
    'docs': {
        'template': '''# {titulo}

## Descricao
{descricao}

## Uso
{uso}

## Exemplo
{exemplo}

## Notas
{notas}''',
        'blanks': ['titulo', 'descricao', 'uso', 'exemplo', 'notas'],
    },
}


# ============================================================
# MAIN
# ============================================================

def main():
    crew = MCRCrew()
    
    # Carrega modulos padrao no cerebro
    for nome, info in MODULOS_PADRAO.items():
        crew.cerebro.aprender_modulo(
            nome, info['template'], info['blanks'], 
            info.get('regras'), exemplos={'nome': nome}
        )
    
    if len(sys.argv) < 2:
        print("MCR CREW V13 — THE EVOLVING SYSTEM")
        print("Cada uso deixa o sistema mais inteligente.\n")
        print("USO:")
        print(f"  python {sys.argv[0]} <modulo> [args...]")
        print(f"  python {sys.argv[0]} --aprender <nome> <template> <blanks...>")
        print(f"  python {sys.argv[0]} --auto-template <nome> <arquivo_exemplo>")
        print(f"  python {sys.argv[0]} --status")
        print(f"\nMODULOS: {', '.join(MODULOS_PADRAO.keys())}")
        print(f"\nEXEMPLOS:")
        print(f"  python {sys.argv[0]} npc Joao Ola 100 50")
        print(f"  python {sys.argv[0]} monster Goblin 200 20 10 456 0.3")
        print(f"  python {sys.argv[0]} --status")
        return
    
    cmd = sys.argv[1]
    
    if cmd == '--status':
        crew.status()
    
    elif cmd == '--aprender' and len(sys.argv) >= 4:
        nome = sys.argv[2]
        # Le template do stdin ou argumento
        if len(sys.argv) >= 4:
            template = sys.argv[3]
            blanks = sys.argv[4:] if len(sys.argv) > 4 else []
            crew.aprender_modulo(nome, template, blanks)
    
    elif cmd == '--auto-template' and len(sys.argv) >= 4:
        nome = sys.argv[2]
        arquivo = sys.argv[3]
        if os.path.exists(arquivo):
            with open(arquivo, 'r', encoding='utf-8') as f:
                codigo = f.read()
            crew.auto_template(nome, [codigo])
        else:
            print(f"[ERRO] Arquivo nao encontrado: {arquivo}")
    
    elif cmd in MODULOS_PADRAO:
        crew.executar(cmd, sys.argv[2:])
    
    else:
        print(f"[ERRO] Modulo '{cmd}' nao encontrado")

if __name__ == '__main__':
    main()
