#!/usr/bin/env python3
"""
MCR CREW V12 — Template Engine (Python Estrutura, IA Preenche)
================================================================
O padrao definitivo: Python DA a estrutura COMPLETA.
IA so preenche campos criativos (nomes, textos, numeros).
Zero validacao necessaria — a sintaxe nunca erra.

Cada modulo = um TEMPLATE + lista de BLANKS.
"""

import sys, os, json, re, random, urllib.request, datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE_V12 = r'E:\Projeto MCR\sandbox\.crew_v12'
os.makedirs(BASE_V12, exist_ok=True)

# ============================================================
# TEMPLATE ENGINE
# ============================================================

class TemplateEngine:
    """
    Motor de templates: Python define a estrutura, IA preenche blanks.
    
    Um template eh uma string com {placeholders}.
    Os blanks definem o que a IA deve preencher para cada placeholder.
    """
    
    @staticmethod
    def extrair_blanks(template):
        """Extrai todos os {placeholders} de um template."""
        return re.findall(r'\{(\w+)\}', template)
    
    @staticmethod
    def preencher(template, valores):
        """Preenche o template com os valores fornecidos."""
        return template.format(**valores)
    
    @staticmethod
    def perguntar_ia(ia, modulo, blanks, fp):
        """
        Pergunta a IA por cada blank.
        Retorna dict {blank: valor}.
        """
        contexto = fp.get_contexto()
        
        # Prompt unico pedindo todos os blanks
        prompt = (
            f"Preencha os campos criativos para {modulo}.\n"
            f"{contexto}\n\n"
            f"Campos para preencher:\n"
        )
        for b in blanks:
            prompt += f"  {b}: "
        prompt += (
            "\n\nResponda no formato:\n"
            + "\n".join(f"{b}: valor" for b in blanks)
            + "\n\nApenas os valores, sem explicacoes."
        )
        
        r = ia.gerar(prompt, 0.7)
        
        # Extrai valores do texto
        valores = {}
        if r:
            for line in r.split('\n'):
                line = line.strip()
                for b in blanks:
                    if line.lower().startswith(b.lower() + ':'):
                        valor = line.split(':', 1)[1].strip()
                        if valor and not valor.lower() in ('none', 'null', '', 'n/a'):
                            valores[b] = valor
        
        return valores
    
    @staticmethod
    def validar_valores(valores, blanks, regras=None):
        """Valida valores preenchidos."""
        erros = []
        for b in blanks:
            if b not in valores or not valores[b]:
                erros.append(f"Campo '{b}' vazio")
            else:
                val = valores[b]
                # Se o blank espera numero
                if regras and b in regras:
                    if regras[b] == 'int':
                        try: int(val)
                        except: erros.append(f"'{b}={val}' nao eh numero")
                    elif regras[b] == 'float':
                        try: float(val)
                        except: erros.append(f"'{b}={val}' nao eh decimal")
        return erros


# ============================================================
# FINGERPRINT SIMPLIFICADO
# ============================================================

class Fingerprint:
    def __init__(self, modulo):
        self.path = os.path.join(BASE_V12, f'{modulo}.json')
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'metricas': {'acertos': 0, 'erros': 0}}
    
    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def get_contexto(self):
        ctx = []
        bons = self.data.get('bons', [])
        ruins = self.data.get('ruins', [])
        if bons: ctx.append('Exemplos de qualidade: ' + ', '.join(bons[:3]))
        if ruins: ctx.append('Evitar: ' + ', '.join(ruins[:3]))
        return '\n'.join(ctx)
    
    def registrar(self, item, tipo='acerto'):
        m = self.data.setdefault('metricas', {'acertos':0,'erros':0})
        m[tipo+'s'] += 1
        key = 'bons' if tipo == 'acerto' else 'ruins'
        self.data.setdefault(key, []).append(item)
        self.save()


# ============================================================
# IA LOCAL
# ============================================================

class AILocal:
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


# ============================================================
# MODULOS = TEMPLATE + BLANKS
# ============================================================

MODULOS = {}

def registrar_modulo(nome, template, blanks, regras=None, desc=''):
    """Registra um modulo no framework."""
    MODULOS[nome] = {
        'template': template,
        'blanks': blanks,
        'regras': regras or {},
        'desc': desc,
    }


# --- OTCLIENT ---
registrar_modulo('otclient', '''<OTUI>
  <Window name="{nome}" title="{titulo}">
    <Panel name="main" width="300" height="200">
      <Label text="{label_texto}" x="10" y="10" width="280" height="30"/>
      <Button text="{botao_texto}" x="10" y="160" width="100" height="30"/>
    </Panel>
  </Window>
</OTUI>''',
    blanks=['nome','titulo','label_texto','botao_texto'],
    desc='Cria uma janela OTUI com label e botao')


# --- NPC ---
registrar_modulo('npc', '''-- NPC: {nome}
local npc = NPC("{nome}")
npc:setSaudacao("{saudacao}")
npc:addItem({item_id}, {item_preco})
print("NPC {nome} carregado.")''',
    blanks=['nome','saudacao','item_id','item_preco'],
    regras={'item_id': 'int', 'item_preco': 'float'},
    desc='Cria um NPC com saudacao e item a venda')


# --- QUEST ---
registrar_modulo('quest', '''-- Quest: {nome}
local quest = Quest("{nome}")
quest:setDescricao("{descricao}")
quest:addObjetivo("{objetivo}")
quest:addRecompensa("xp", {xp})
quest:addRecompensa("gold", {gold})
print("Quest {nome} carregada.")''',
    blanks=['nome','descricao','objetivo','xp','gold'],
    regras={'xp': 'int', 'gold': 'int'},
    desc='Cria uma quest com objetivo e recompensa')


# --- MONSTER ---
registrar_modulo('monster', '''-- Monster: {nome}
local mon = Monster("{nome}")
mon:setHealth({hp})
mon:setAttack({atk})
mon:setDefense({def})
mon:addLoot({loot_id}, {loot_chance})
print("Monster {nome} carregado.")''',
    blanks=['nome','hp','atk','def','loot_id','loot_chance'],
    regras={'hp': 'int', 'atk': 'int', 'def': 'int', 'loot_id': 'int', 'loot_chance': 'float'},
    desc='Cria um monstro com stats e loot')


# --- ITEM ---
registrar_modulo('item', '''-- Item: {nome}
local item = Item({id}, "{nome}")
item:setType("{tipo}")
item:setAttack({atk})
item:setDefense({def})
item:setWeight({peso})
print("Item {nome} carregado.")''',
    blanks=['nome','id','tipo','atk','def','peso'],
    regras={'id': 'int', 'atk': 'int', 'def': 'int', 'peso': 'int'},
    desc='Cria um item com atributos')


# --- SPELL ---
registrar_modulo('spell', '''-- Spell: {nome}
local spell = Spell("{nome}", "{elemento}")
spell:setDamage({dano})
spell:setManaCost({mana})
spell:setCooldown({cd})
print("Spell {nome} carregada.")''',
    blanks=['nome','elemento','dano','mana','cd'],
    regras={'dano': 'int', 'mana': 'int', 'cd': 'float'},
    desc='Cria uma spell com elemento e custos')


# --- DOCS (template markdown) ---
registrar_modulo('docs', '''# {titulo}

## Descricao
{descricao}

## Uso
{uso}

## Exemplo
{exemplo}

## Notas
{notas}''',
    blanks=['titulo','descricao','uso','exemplo','notas'],
    desc='Gera documentacao markdown')


# ============================================================
# ORQUESTRADOR
# ============================================================

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in MODULOS:
        print("MCR CREW V12 — Template Engine")
        print("Python da estrutura, IA preenche blanks.")
        print()
        print(f"Modulos: {', '.join(MODULOS.keys())}")
        print()
        for nome, mod in MODULOS.items():
            print(f"  {nome}: {mod['desc']}")
            print(f"    Blanks: {', '.join(mod['blanks'])}")
        print()
        print("Uso: python mcr_crew_v12.py <modulo> [args...]")
        return
    
    nome_mod = sys.argv[1]
    args = sys.argv[2:]
    mod = MODULOS[nome_mod]
    
    print(f'\n[V12] {nome_mod}: {mod["desc"]}')
    
    # Prepara blanks com valores default ou args
    valores_iniciais = {}
    for i, b in enumerate(mod['blanks']):
        if i < len(args) and args[i]:
            valores_iniciais[b] = args[i]
    
    # Pergunta a IA pelos blanks faltantes
    ia = AILocal()
    fp = Fingerprint(nome_mod)
    
    blanks_faltantes = [b for b in mod['blanks'] if b not in valores_iniciais]
    
    erros = []
    if blanks_faltantes:
        print(f'  Perguntando IA por: {", ".join(blanks_faltantes)}')
        valores_ia = TemplateEngine.perguntar_ia(ia, nome_mod, blanks_faltantes, fp)
        valores_iniciais.update(valores_ia)
        
        # Valida
        erros = TemplateEngine.validar_valores(valores_iniciais, mod['blanks'], mod.get('regras'))
        if erros:
            print(f'  Validacao: {len(erros)} erros')
            for e in erros:
                print(f'    [ERRO] {e}')
        else:
            print(f'  Todos os campos validos!')
    
    # Preenche template
    try:
        resultado = TemplateEngine.preencher(mod['template'], valores_iniciais)
    except KeyError as e:
        print(f'  [ERRO] Template: campo {e} faltando')
        return
    
    # Salva
    nome_arquivo = valores_iniciais.get('nome', nome_mod).lower().replace(' ', '_')
    ext = '.lua' if nome_mod != 'docs' else '.md'
    ext = '.otui' if nome_mod == 'otclient' else ext
    
    path = f'E:\\Projeto MCR\\sandbox\\v12_{nome_mod}_{nome_arquivo}{ext}'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(resultado)
    
    print(f'  [OK] Salvo: {path}')
    print(f'  [OK] {nome_mod} concluido!')
    
    # Registra aprendizado
    if not erros:
        fp.registrar(nome_mod, 'acerto')
        # Salva os valores como exemplo
        fp.data.setdefault('bons', []).append(str(valores_iniciais))
        fp.save()

if __name__ == '__main__':
    main()
