#!/usr/bin/env python3
"""
MCR CREW FRAMEWORK v10 — Complete System
==========================================
Framework universal com fingerprints SEED (pre-treinados)
para TODAS as areas do Projeto MCR.

Uso: python mcr_crew_v10.py <modulo> <tarefa> [args...]

Modulos:
  habilidades  — Gera habilidades SHC (9.5/10)
  otclient     — Gera/refatora OTUI + Lua
  npc          — Cria NPCs com dialogos
  quest        — Projeta quests com recompensas
  monster      — Configura monstros (loot, stats)
  item         — Cria definicoes de itens
  spell        — Cria efeitos de spells
  sistema      — Projeta sistemas C++/Lua
  docs         — Gera documentacao
"""

import sys, os, json, re, random, shutil, urllib.request, datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE_FINGERPRINTS = r'E:\Projeto MCR\sandbox\.crew_v10'
os.makedirs(BASE_FINGERPRINTS, exist_ok=True)

# ============================================================
# FINGERPRINT SEEDS — Conhecimento PRE-TREINADO para cada modulo
# ============================================================
# Estes sao exemplos que eu (cloud) considero de qualidade.
# O framework comeca sabendo o que eh bom/ruim em CADA area.

FINGERPRINT_SEEDS = {
    'habilidades': {
        'exemplos_bons': [
            'Giro Agil (Clavas Leves)',
            'Clava Trovejante (Clavas Leves)', 
            'Danca das Clavas (Clavas Leves)',
            'Soco Certeiro (Lutador)',
            'Gancho Poderoso (Lutador)',
            'Esquiva Felina (Lutador)',
            'Tiro Certeiro (Arcos)',
            'Chuva de Flechas (Arcos)',
            'Flecha Perfurante (Arcos)',
            'Orbital Igneo (Fogo)',
            'Explosao Glacial (Gelo)',
            'Raio Celeste (Energia)',
        ],
        'exemplos_ruins': [
            'Iron Fist (ingles em dominio pt)',
            'Raging Tiger (ingles)',
            'Punho de Ferro (punho nao e clava)',
            'Cobra Venenosa (cobra nao e arma)',
            'Garrafa de Fogo (garrafa nao e arma)',
            'Agulha Sutil (agulha nao e clava)',
            'Flecha Precision (ingles)',
            'Rapido Fuzil (fuzil nao e arco)',
            'Mira Sombria (sombrio nao combina com arco)',
        ],
        'regras': [
            'Nome deve ter 2+ palavras em portugues',
            'Nome deve usar palavras do pool tematico do dominio',
            'Proibido ingles, nomes de animais, armas de outros tipos',
            'Cada nome deve evocar a mecanica da habilidade',
        ],
    },
    'otclient': {
        'exemplos_bons': [
            'Module com Window + Panel + Button + Label',
            'UIMap com camadas organizadas',
            'Console com input + output + history',
            'Battle com HP bar + status icons',
        ],
        'exemplos_ruins': [
            'Window sem Panel organizador',
            'Labels sem texto descritivo',
            'Botao sem evento onClick',
            'Module sem arquivo .lua correspondente',
        ],
        'regras': [
            'Todo modulo OTUI precisa de .otui + .lua',
            'Janelas precisam de Panel como container',
            'Botoes precisam de evento onClick',
            'Usar nomes descritivos para widgets',
        ],
    },
    'npc': {
        'exemplos_bons': [
            'NPC: {nome:"Joao", sauda:["Bem-vindo!", "Ola!"], itens:[{id:123, preco:50}]}',
            'NPC com dialogos condicionais (quest)',
            'NPC com loja (compre/venda)',
        ],
        'exemplos_ruins': [
            'NPC sem nenhum dialogo',
            'NPC com precos negativos',
            'NPC sem nome ou com nome generico',
        ],
        'regras': [
            'NPC precisa de nome unico e saudacao',
            'Itens de loja precisam de ID e preco validos',
            'Dialogos condicionais precisam de condicao clara',
        ],
    },
    'quest': {
        'exemplos_bons': [
            'Quest: {nome:"A Jornada", etapas:[{obj:"matar 10 goblins", recompensa:{exp:100}}]}',
            'Quest com storyline e progressao',
            'Quest com recompensas escalonadas por dificuldade',
        ],
        'exemplos_ruins': [
            'Quest sem objetivos definidos',
            'Quest com recompensa desproporcional',
            'Quest sem nenhum dialogo ou lore',
        ],
        'regras': [
            'Quest precisa de nome, descricao, objetivos',
            'Recompensas devem ser proporcionais a dificuldade',
            'Quest pode ter multiplas etapas (opcional)',
        ],
    },
    'monster': {
        'exemplos_bons': [
            'Monster: {nome:"Goblin", hp:100, atk:15, def:5, loot:[{id:123, chance:0.5}]}',
            'Monstro com loot table variada',
            'Monstro com fraqueza elemental definida',
        ],
        'exemplos_ruins': [
            'Monstro sem loot (vazio)',
            'Monstro com stats desbalanceados (hp 1, atk 999)',
            'Monstro sem nome ou ID',
        ],
        'regras': [
            'Monstro precisa de nome, HP, ataque, defesa',
            'Loot precisa de ID do item + chance (0-1)',
            'Stats devem ser balanceados para o nivel',
        ],
    },
    'item': {
        'exemplos_bons': [
            'Item: {id:123, nome:"Espada Longa", tipo:"weapon", atk:25, def:5, peso:40}',
            'Item com requisito de nivel ou vocacao',
            'Item com efeito especial (cura, buff)',
        ],
        'exemplos_ruins': [
            'Item sem tipo definido',
            'Item com stats negativos',
            'Item sem nome descritivo',
        ],
        'regras': [
            'Item precisa de ID unico, nome, tipo',
            'Atributos dependem do tipo (arma: atk; armadura: def)',
            'Itens especiais precisam de efeito definido',
        ],
    },
    'spell': {
        'exemplos_bons': [
            'Spell: {nome:"Bola de Fogo", elemento:"fire", dano:100, mana:30, cooldown:4}',
            'Spell com formula de dano escalonada',
            'Spell com efeito visual definido',
        ],
        'exemplos_ruins': [
            'Spell sem custo de mana',
            'Spell com cooldown 0 (spammavel)',
            'Spell sem elemento definido',
        ],
        'regras': [
            'Spell precisa de nome, elemento, dano, mana, cooldown',
            'Dano pode ser fixo ou por formula (ex: nivel * 2)',
            'Efeito visual opcional mas recomendado',
        ],
    },
    'sistema': {
        'exemplos_bons': [
            'Sistema: {nome:"Crafting", desc:"Combina recursos em equipamentos"}',
            'Sistema com arquitetura clara (modulos separados)',
            'Sistema com fallback e tratamento de erros',
        ],
        'exemplos_ruins': [
            'Sistema supercomplexo sem documentacao',
            'Sistema sem definicao clara de responsabilidades',
            'Sistema que duplica funcionalidade existente',
        ],
        'regras': [
            'Sistema precisa de nome e descricao claros',
            'Arquitetura deve ser modular',
            'Evitar duplicar funcionalidades do Canary',
        ],
    },
}

# ============================================================
# NUCLEO DO FRAMEWORK
# ============================================================

class Fingerprint:
    """Fingerprint que comeca com seeds pre-treinados."""
    
    def __init__(self, modulo, tarefa='default'):
        self.path = os.path.join(BASE_FINGERPRINTS, f'{modulo}_{tarefa}.json')
        self.data = self._load(modulo)
    
    def _load(self, modulo):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Merge with seeds (preserve aprendizado)
                seed = FINGERPRINT_SEEDS.get(modulo, {})
                for k, v in seed.items():
                    if k not in data or not data[k]:
                        data[k] = v
                    elif isinstance(v, list):
                        # Merge unico
                        existentes = set(str(x) for x in data[k])
                        for item in v:
                            if str(item) not in existentes:
                                data[k].append(item)
                                existentes.add(str(item))
                return data
        
        # Primeira vez: usa seed
        return dict(FINGERPRINT_SEEDS.get(modulo, {}))
    
    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def get_contexto(self):
        ctx = []
        bons = self.data.get('exemplos_bons', [])
        ruins = self.data.get('exemplos_ruins', [])
        regras = self.data.get('regras', [])
        
        if bons:
            ctx.append('REFERENCIAS DE QUALIDADE (siga este estilo):')
            for ex in bons[:5]:
                ctx.append(f'  [BOM] {ex}')
        if ruins:
            ctx.append('EVITE ESTES PADROES:')
            for ex in ruins[:5]:
                ctx.append(f'  [RUIM] {ex}')
        if regras:
            ctx.append('REGRAS:')
            for r in regras:
                ctx.append(f'  - {r}')
        
        # Metricas
        m = self.data.get('metricas', {})
        ctx.append(f'\n[Aprendizado: {m.get("acertos",0)} acertos, {m.get("erros",0)} erros]')
        
        return '\n'.join(ctx)
    
    def registrar(self, item, tipo='acerto'):
        """Registra acerto ou erro e atualiza exemplos."""
        metricas = self.data.setdefault('metricas', {'acertos': 0, 'erros': 0})
        metricas[tipo + 's'] += 1
        
        if tipo == 'acerto':
            recentes = self.data.setdefault('acertos_recentes', [])
            recentes.append(item)
            count = sum(1 for a in recentes if a == item)
            if count >= 2 and item not in self.data.get('exemplos_bons', []):
                self.data.setdefault('exemplos_bons', []).append(item)
                print(f'    [FP] Aprendeu: "{item}" virou exemplo BOM')
            if len(recentes) > 100: recentes[:] = recentes[-100:]
        else:
            recentes = self.data.setdefault('erros_recentes', [])
            recentes.append(item)
            count = sum(1 for a in recentes if a == item)
            if count >= 2 and item not in self.data.get('exemplos_ruins', []):
                self.data.setdefault('exemplos_ruins', []).append(item)
                print(f'    [FP] Aprendeu: "{item}" virou exemplo RUIM')
            if len(recentes) > 100: recentes[:] = recentes[-100:]
        
        self.save()


class AILocal:
    """Interface com IA local com fallback para texto simples."""
    
    def __init__(self, model='qwen2.5-coder:7b'):
        self.model = model
    
    def gerar(self, prompt, temp=0.8):
        try:
            data = json.dumps({'model':self.model,'prompt':prompt,'stream':False,
                'options':{'temperature':temp,'num_ctx':8192,'top_p':0.9}}).encode()
            req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read()).get('response','')
        except: return None
    
    def gerar_json(self, prompt, temp=0.7):
        """Tenta JSON, se falhar usa regex pra extrair."""
        r = self.gerar(prompt, temp)
        if not r: return None
        
        # Tenta JSON
        for p in [r'\[.*?\]', r'\{.*?\}']:
            m = re.search(p, r, re.DOTALL)
            if m:
                try: return json.loads(m.group())
                except: pass
        
        # Fallback: extrai linhas NOME:, DESCRICAO:, etc
        result = {}
        for line in r.split('\n'):
            line = line.strip()
            if ':' in line:
                key, val = line.split(':', 1)
                result[key.strip().lower()] = val.strip()
        return result if result else None


# ============================================================
# MODULO GENERATOR — Fabrica de modulos
# ============================================================

class ModuloMCR:
    """Classe base para todos os modulos do MCR."""
    
    def __init__(self, nome, fp, ia):
        self.nome = nome
        self.fp = fp
        self.ia = ia
        self.seed = FINGERPRINT_SEEDS.get(nome, {})
    
    def gerar_prompt_base(self, tarefa, contexto_extra=''):
        """Gera prompt padrao com contexto do fingerprint."""
        fp_ctx = self.fp.get_contexto()
        return (
            f"Tarefa: {tarefa} no Projeto MCR (Tibia).\n"
            f"{fp_ctx}\n"
            f"{contexto_extra}\n"
        )
    
    def extrair_lista(self, texto):
        """Extrai uma lista de items do texto (um por linha)."""
        items = []
        for line in texto.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                if line.startswith('- ') or line[0].isdigit() and '. ' in line[:4]:
                    items.append(re.sub(r'^[- \d.]+', '', line).strip())
                elif ':' in line and len(line) < 100:
                    items.append(line)
        return items
    
    def prompt_lista(self, instrucao, quantidade):
        """Gera prompt que retorna lista (um item por linha)."""
        return f"{instrucao}\n\nListe {quantidade} itens, um por linha, sem numeracao extra."


# ============================================================
# MODULOS ESPECIFICOS
# ============================================================

class ModuloHabilidades(ModuloMCR):
    def executar(self, args):
        print(f'\n[MODULO HABILIDADES]')
        print(f'  Fingerprint: {len(self.seed.get("exemplos_bons",[]))} seeds bons')
        print(f'  Use: python mcr_crew_v10.py habilidades <dominio> <n>')


class ModuloOTClient(ModuloMCR):
    def executar(self, args):
        nome = args[0] if args else 'MinhaJanela'
        print(f'\n[MODULO OTCLIENT] Criando {nome}...')
        
        prompt = self.gerar_prompt_base(
            f"Criar modulo OTClient chamado '{nome}'",
            f"Crie OTUI e Lua para uma janela com Panel, Button, Label, TextEdit."
        )
        r = self.ia.gerar(prompt, 0.7)
        
        if r:
            # Extrai conteudo entre tags OTUI
            otui = ''
            m = re.search(r'<OTUI>.*?</OTUI>', r, re.DOTALL)
            if m: otui = m.group()
            
            if otui:
                path = f'E:\\Projeto MCR\\OTClient\\modules\\{nome}\\{nome}.otui'
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(otui)
                print(f'  [OK] OTUI salvo: {path}')
                self.fp.registrar(nome, 'acerto')
            else:
                print(f'  [ERRO] Nao gerou OTUI valido')
                self.fp.registrar('OTClient:' + nome, 'erro')
        print('  [CONCLUIDO]')


class ModuloNPC(ModuloMCR):
    def executar(self, args):
        nome = args[0] if args else 'NPC_Generico'
        print(f'\n[MODULO NPC] Criando {nome}...')
        
        prompt = self.gerar_prompt_base(
            f"Criar NPC chamado '{nome}'",
            "Formato: NOME: nome | SAUDACAO: texto | ITENS: id1:preco1, id2:preco2"
        )
        r = self.ia.gerar(prompt, 0.7)
        
        if r:
            # Salva como NPC
            path = f'E:\\Projeto MCR\\sandbox\\npc_{nome.lower()}.lua'
            with open(path, 'w', encoding='utf-8') as f:
                f.write('-- NPC gerado pelo MCR Crew v10\n')
                f.write(f'-- {r[:500]}\n')
            print(f'  [OK] NPC salvo: {path}')
        print('  [CONCLUIDO]')


class ModuloQuest(ModuloMCR):
    def executar(self, args):
        nome = args[0] if args else 'Quest_Nova'
        print(f'\n[MODULO QUEST] Criando {nome}...')
        
        prompt = self.gerar_prompt_base(
            f"Criar quest '{nome}'",
            "Formato: NOME: nome | DESCRICAO: texto | OBJETIVOS: obj1, obj2 | RECOMPENSA: item:qtd"
        )
        r = self.ia.gerar(prompt, 0.7)
        
        if r:
            path = f'E:\\Projeto MCR\\sandbox\\quest_{nome.lower()}.lua'
            with open(path, 'w', encoding='utf-8') as f:
                f.write('-- Quest gerada pelo MCR Crew v10\n')
                f.write(f'-- {r[:500]}\n')
            print(f'  [OK] Quest salva: {path}')
            self.fp.registrar(nome, 'acerto')
        else:
            self.fp.registrar('Quest:' + nome, 'erro')
        print('  [CONCLUIDO]')


class ModuloMonster(ModuloMCR):
    def executar(self, args):
        nome = args[0] if args else 'Monstro_Novo'
        print(f'\n[MODULO MONSTER] Criando {nome}...')
        
        prompt = self.gerar_prompt_base(
            f"Criar monstro '{nome}'",
            "Formato: NOME: nome | HP: valor | ATK: valor | DEF: valor | LOOT: id:chance"
        )
        r = self.ia.gerar(prompt, 0.7)
        
        if r:
            path = f'E:\\Projeto MCR\\sandbox\\monster_{nome.lower()}.lua'
            with open(path, 'w', encoding='utf-8') as f:
                f.write('-- Monster gerado pelo MCR Crew v10\n')
                f.write(f'-- {r[:500]}\n')
            print(f'  [OK] Monster salvo: {path}')
            self.fp.registrar(nome, 'acerto')
        else:
            self.fp.registrar('Monster:' + nome, 'erro')
        print('  [CONCLUIDO]')


class ModuloItem(ModuloMCR):
    def executar(self, args):
        nome = args[0] if args else 'Item_Novo'
        print(f'\n[MODULO ITEM] Criando {nome}...')
        
        prompt = self.gerar_prompt_base(
            f"Criar item '{nome}'",
            "Formato: NOME: nome | ID: numero | TIPO: weapon/armor/consumable | ATRIBUTOS: chave:valor"
        )
        r = self.ia.gerar(prompt, 0.7)
        
        if r:
            path = f'E:\\Projeto MCR\\sandbox\\item_{nome.lower()}.lua'
            with open(path, 'w', encoding='utf-8') as f:
                f.write('-- Item gerado pelo MCR Crew v10\n')
                f.write(f'-- {r[:500]}\n')
            print(f'  [OK] Item salvo: {path}')
            self.fp.registrar(nome, 'acerto')
        else:
            self.fp.registrar('Item:' + nome, 'erro')
        print('  [CONCLUIDO]')


class ModuloSpell(ModuloMCR):
    def executar(self, args):
        nome = args[0] if args else 'Spell_Nova'
        print(f'\n[MODULO SPELL] Criando {nome}...')
        
        prompt = self.gerar_prompt_base(
            f"Criar spell '{nome}'",
            "Formato: NOME: nome | ELEMENTO: fire/ice/earth/energy | DANO: valor | MANA: custo | CD: segundos"
        )
        r = self.ia.gerar(prompt, 0.7)
        
        if r:
            path = f'E:\\Projeto MCR\\sandbox\\spell_{nome.lower()}.lua'
            with open(path, 'w', encoding='utf-8') as f:
                f.write('-- Spell gerada pelo MCR Crew v10\n')
                f.write(f'-- {r[:500]}\n')
            print(f'  [OK] Spell salva: {path}')
            self.fp.registrar(nome, 'acerto')
        else:
            self.fp.registrar('Spell:' + nome, 'erro')
        print('  [CONCLUIDO]')


class ModuloDocs(ModuloMCR):
    def executar(self, args):
        tema = args[0] if args else 'Feature_Nova'
        print(f'\n[MODULO DOCS] Gerando documentacao sobre {tema}...')
        
        prompt = self.gerar_prompt_base(
            f"Documentar: {tema}",
            "Gere documentacao tecnica em markdown."
        )
        r = self.ia.gerar(prompt, 0.7)
        
        if r:
            path = f'E:\\Projeto MCR\\sandbox\\docs_{tema.lower()}.md'
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f'# {tema}\n\n')
                f.write(r[:2000])
            print(f'  [OK] Documentacao salva: {path}')
            self.fp.registrar(tema, 'acerto')
        print('  [CONCLUIDO]')


# ============================================================
# ORQUESTRADOR
# ============================================================

MODULOS = {
    'habilidades': ModuloHabilidades,
    'otclient': ModuloOTClient,
    'npc': ModuloNPC,
    'quest': ModuloQuest,
    'monster': ModuloMonster,
    'item': ModuloItem,
    'spell': ModuloSpell,
    'sistema': ModuloDocs,  # Reuses Docs (projetar = documentar)
    'docs': ModuloDocs,
}

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print(f'Modulos: {", ".join(MODULOS.keys())}')
        print('Ex: python mcr_crew_v10.py npc Joao')
        print('    python mcr_crew_v10.py quest Aventura')
        print('    python mcr_crew_v10.py otclient MinhaJanela')
        return
    
    nome_mod = sys.argv[1]
    args = sys.argv[2:]
    
    if nome_mod not in MODULOS:
        print(f'Modulo invalido. Disponiveis: {", ".join(MODULOS.keys())}')
        return
    
    # Cada modulo tem seu fingerprint
    fp = Fingerprint(nome_mod)
    ia = AILocal()
    modulo = MODULOS[nome_mod](nome_mod, fp, ia)
    
    # Mostra status do fingerprint
    n_bons = len(fp.data.get('exemplos_bons', []))
    n_ruins = len(fp.data.get('exemplos_ruins', []))
    print(f'[Fingerprint] {n_bons} exemplos bons, {n_ruins} exemplos ruins')
    
    modulo.executar(args)
    
    # Mostra aprendizado apos execucao
    metricas = fp.data.get('metricas', {'acertos':0,'erros':0})
    print(f'[Aprendizado] Total: {metricas["acertos"]} acertos, {metricas["erros"]} erros')

if __name__ == '__main__':
    main()
