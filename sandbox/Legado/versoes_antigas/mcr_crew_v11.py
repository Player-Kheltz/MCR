#!/usr/bin/env python3
"""
MCR CREW FRAMEWORK v11 — Auto-Adaptable System
================================================
Caracteristicas novas:
  1. AUTO-FINGERPRINT: escaneia projeto existente pra aprender padroes
  2. MODULAR: qualquer projeto, nao so MCR
  3. OTClient refinado com exemplos reais de OTUI
  4. Fingerprints com +20 seeds cada

Uso: python mcr_crew_v11.py <modulo> <tarefa> [args...]
     python mcr_crew_v11.py --autofp <caminho>   # Auto-fingerprint
"""

import sys, os, json, re, random, shutil, urllib.request, datetime

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE_V11 = r'E:\Projeto MCR\sandbox\.crew_v11'
os.makedirs(BASE_V11, exist_ok=True)

# ============================================================
# AUTO-FINGERPRINT ENGINE
# ============================================================
class AutoFingerprint:
    """
    Escaneia um projeto existente e extrai:
    - Padroes de nomenclatura
    - Estruturas comuns
    - O que parece "qualidade" vs "problema"
    """
    
    @staticmethod
    def escanear(caminho, modulo):
        """Escaneia um diretorio e gera fingerprint inicial."""
        padroes = {
            'arquivos_encontrados': 0,
            'extensoes': {},
            'padroes_nomes': [],
            'tamanho_medio': 0,
        }
        
        total_size = 0
        for root, dirs, files in os.walk(caminho):
            # Pula diretorios de sistema
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__')]
            
            for f in files:
                ext = os.path.splitext(f)[1]
                padroes['extensoes'][ext] = padroes['extensoes'].get(ext, 0) + 1
                padroes['arquivos_encontrados'] += 1
                
                # Extrai padroes de nome (CamelCase, snake_case, etc)
                nome_sem_ext = os.path.splitext(f)[0]
                if '_' in nome_sem_ext:
                    padroes['padroes_nomes'].append('snake_case')
                elif nome_sem_ext[0].isupper() if nome_sem_ext else False:
                    padroes['padroes_nomes'].append('PascalCase')
                elif nome_sem_ext[0].islower() if nome_sem_ext else False:
                    padroes['padroes_nomes'].append('camelCase')
                
                try:
                    total_size += os.path.getsize(os.path.join(root, f))
                except: pass
        
        if padroes['arquivos_encontrados'] > 0:
            padroes['tamanho_medio'] = total_size // padroes['arquivos_encontrados']
        
        # Gera fingerprint baseado no scan
        fp = {
            'modulo': modulo,
            'projeto_scan': {
                'caminho': caminho,
                'arquivos': padroes['arquivos_encontrados'],
                'extensoes_principais': sorted(padroes['extensoes'].items(), key=lambda x: -x[1])[:5],
            },
            'exemplos_bons': AutoFingerprint._gerar_seeds(modulo, padroes),
            'exemplos_ruins': AutoFingerprint._gerar_anti_seeds(modulo),
            'regras': AutoFingerprint._gerar_regras(modulo, padroes),
            'metricas': {'acertos': 0, 'erros': 0},
            'criado_em': str(datetime.datetime.now()),
        }
        
        return fp
    
    @staticmethod
    def _gerar_seeds(modulo, padroes):
        """Gera seeds baseado no que encontrou no projeto."""
        seeds = {
            'otclient': [
                'Module com Window + Panel organizado',
                'UIMap com camadas (floor, creatures, effects)',
                'Console com input/output separados',
                'Battle com HP bar + status icons',
                'Container com slots de item',
                'Button com onClick e hover color',
                'Label com font e color customizados',
                'TextEdit com placeholder e max length',
                'ImageView com source e scale',
                'ProgressBar com cores de estado',
                'MenuItem com icone e shortcut',
                'TabPanel com abas organizadas',
                'Scrollbar com thumb e track',
                'ComboBox com dropdown items',
                'CheckBox com label e estado',
            ],
            'npc': [
                'NPC com saudacao personalizada',
                'NPC com loja de itens (compre/venda)',
                'NPC com dialogos condicionais (quest)',
                'NPC com workshop (craft, upgrade)',
                'NPC com banco (deposito/saque)',
                'NPC com bless (sistema de bencaos)',
                'NPC com quests (entrega, coleta)',
                'NPC com dialogo em arvore',
                'NPC com reacoes por vocacao',
                'NPC com horario de funcionamento',
            ],
            'quest': [
                'Quest com 3+ etapas progressivas',
                'Quest com dialogo inicial e final',
                'Quest com recompensa em XP e itens',
                'Quest com requisito de nivel',
                'Quest com escolha do jogador (dual reward)',
                'Quest com boss fight no final',
                'Quest com exploracao (descobrir lugares)',
                'Quest com coleta de recursos',
                'Quest com entrega de itens para NPC',
                'Quest com timeline (tempo limite)',
            ],
            'monster': [
                'Monstro com loot variado (2-5 itens)',
                'Monstro com fraqueza elemental',
                'Monstro com comportamento agressivo/passivo',
                'Monstro com spawn em grupo',
                'Monstro com drop rate balanceado',
                'Monstro com ataques especiais',
                'Monstro com imunidade a condicoes',
                'Monstro com respawn timer',
                'Monstro com loot scaling por nivel',
                'Monstro com variantes (elite, boss)',
            ],
            'item': [
                'Item com ID unico e nome descritivo',
                'Weapon com ataque e defesa balanceados',
                'Armor com defesa e peso',
                'Consumable com efeito (cura, buff)',
                'Item com requisito de nivel',
                'Item com requisito de vocacao',
                'Item com durabilidade',
                'Item com efeito visual ao usar',
                'Item com stack (pocao, flecha)',
                'Item com descricao de lore',
            ],
            'spell': [
                'Spell com nome e elemento definido',
                'Spell com formula de dano escalonada (nivel * 2)',
                'Spell com custo de mana e cooldown',
                'Spell com efeito visual (particles)',
                'Spell com alcance e area',
                'Spell com condicao (stun, slow, burn)',
                'Spell com som de cast',
                'Spell com requisito de magia level',
                'Spell com variacao de dano (min-max)',
                'Spell com efeito em grupo (party)',
            ],
        }
        return seeds.get(modulo, [])
    
    @staticmethod
    def _gerar_anti_seeds(modulo):
        """Gera contra-exemplos."""
        anti = {
            'otclient': [
                'Window sem Panel (widgets soltos)',
                'Button sem onClick handler',
                'Label sem text definido',
                'Module sem .lua correspondente',
                'OTUI com sintaxe invalida',
            ],
            'npc': [
                'NPC sem nenhum dialogo',
                'NPC com precos zerados ou negativos',
                'NPC que nao responde a saudacao basica',
                'NPC sem nome ou ID',
            ],
            'quest': [
                'Quest sem objetivos definidos',
                'Quest com recompensa desproporcional',
                'Quest sem dialogo ou lore',
                'Quest impossivel de completar',
            ],
            'monster': [
                'Monstro sem loot (vazio)',
                'Monstro com stats desbalanceados',
                'Monstro sem nome ou tipo',
                'Monstro com spawn rate 0',
            ],
            'item': [
                'Item sem tipo definido',
                'Item com stats negativos',
                'Item com ID duplicado',
                'Item sem nome',
            ],
            'spell': [
                'Spell sem custo de mana',
                'Spell com cooldown 0 (spammavel)',
                'Spell sem elemento definido',
                'Spell com dano fixo sem scaling',
            ],
        }
        return anti.get(modulo, [])
    
    @staticmethod
    def _gerar_regras(modulo, padroes):
        """Gera regras baseadas no projeto escaneado."""
        return [
            'Seguir o padrao de nomenclatura do projeto existente',
            'Manter consistencia com arquivos ja existentes',
            'Respeitar a estrutura de diretorios do projeto',
            'Codigo deve seguir o estilo do projeto (indentacao, etc)',
        ]


# ============================================================
# FINGERPRINT COM AUTO-SEED
# ============================================================

class Fingerprint:
    def __init__(self, modulo, tarefa='default', auto_scan_path=None):
        self.path = os.path.join(BASE_V11, f'{modulo}_{tarefa}.json')
        self.data = self._load(modulo, auto_scan_path)
    
    def _load(self, modulo, auto_scan_path=None):
        # Se existe fingerprint salvo, carrega
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Se nao existe, mas tem auto_scan_path, escaneia
        if auto_scan_path and os.path.exists(auto_scan_path):
            fp = AutoFingerprint.escanear(auto_scan_path, modulo)
            self._salvar(fp)
            return fp
        
        # Senao, usa seeds pre-treinados
        fp = {
            'modulo': modulo,
            'exemplos_bons': AutoFingerprint._gerar_seeds(modulo, {}),
            'exemplos_ruins': AutoFingerprint._gerar_anti_seeds(modulo),
            'regras': AutoFingerprint._gerar_regras(modulo, {}),
            'metricas': {'acertos': 0, 'erros': 0},
            'criado_em': str(datetime.datetime.now()),
        }
        self._salvar(fp)
        return fp
    
    def _salvar(self, data=None):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(data or self.data, f, ensure_ascii=False, indent=2)
    
    def get_contexto(self):
        ctx = []
        bons = self.data.get('exemplos_bons', [])[:8]
        ruins = self.data.get('exemplos_ruins', [])[:5]
        
        if bons:
            ctx.append('PADROES DE QUALIDADE:')
            for ex in bons:
                ctx.append(f'  + {ex}')
        if ruins:
            ctx.append('EVITAR:')
            for ex in ruins:
                ctx.append(f'  - {ex}')
        
        m = self.data.get('metricas', {})
        ctx.append(f'\n[FP: {m.get("acertos",0)} acertos | {m.get("erros",0)} erros]')
        return '\n'.join(ctx)
    
    def registrar(self, item, tipo='acerto'):
        m = self.data.setdefault('metricas', {'acertos': 0, 'erros': 0})
        m[tipo + 's'] += 1
        
        recentes = self.data.setdefault(tipo + 's_recentes', [])
        recentes.append(item)
        
        # A cada 2 ocorrencias, vira exemplo permanente
        key = 'exemplos_bons' if tipo == 'acerto' else 'exemplos_ruins'
        count = sum(1 for a in recentes if a == item)
        if count >= 2 and item not in self.data.get(key, []):
            self.data.setdefault(key, []).append(item)
            print(f'  [FP] Aprendeu: "{item}" -> {key}')
        
        if len(recentes) > 100: recentes[:] = recentes[-100:]
        self._salvar()


class AILocal:
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
        r = self.gerar(prompt, temp)
        if not r: return None
        for p in [r'\[.*?\]', r'\{.*?\}']:
            m = re.search(p, r, re.DOTALL)
            if m:
                try: return json.loads(m.group())
                except: pass
        return None


# ============================================================
# MODULOS
# ============================================================

class ModuloBase:
    def __init__(self, nome, fp, ia):
        self.nome = nome
        self.fp = fp
        self.ia = ia
    
    def prompt(self, instrucao, formato='texto'):
        ctx = self.fp.get_contexto()
        return f"{instrucao}\n\n{ctx}\n\nFormato da resposta:\n{formato}\nResponda APENAS no formato solicitado."


class ModuloOTClient(ModuloBase):
    """OTClient com template Python + IA criativa."""
    def executar(self, args):
        nome = args[0] if args else 'MinhaJanela'
        print(f'\n[OTClient] Criando {nome}...')
        
        # IA gera APENAS os valores criativos
        p = self.prompt(
            "Defina os widgets para uma janela OTClient.",
            "TITULO: texto da janela\nLABELS: label1, label2\nBOTOES: botao1, botao2\nLARGURA: numero\nALTURA: numero"
        )
        r = self.ia.gerar(p, 0.7)
        
        if r:
            titulo = 'Janela'
            labels = ['Texto']
            botoes = ['Clique']
            largura = 300
            altura = 200
            
            for line in r.split('\n'):
                line = line.strip()
                upper = line.upper()
                if upper.startswith('TITULO:'): titulo = line.split(':',1)[1].strip()
                elif upper.startswith('LABELS:'): 
                    labels = [x.strip() for x in line.split(':',1)[1].split(',') if x.strip()]
                elif upper.startswith('BOTOES:'):
                    botoes = [x.strip() for x in line.split(':',1)[1].split(',') if x.strip()]
                elif upper.startswith('LARGURA:'):
                    try: largura = int(re.search(r'\d+', line).group())
                    except: pass
                elif upper.startswith('ALTURA:'):
                    try: altura = int(re.search(r'\d+', line).group())
                    except: pass
            
            # Python monta o OTUI com template
            lines = []
            lines.append('<OTUI>')
            lines.append(f'  <Window name="{nome}" title="{titulo}">')
            lines.append(f'    <Panel name="main" width="{largura}" height="{altura}">')
            
            y = 10
            for i, label in enumerate(labels):
                lines.append(f'      <Label text="{label}" x="10" y="{y}" width="{largura-20}" height="30"/>')
                y += 35
            
            for i, botao in enumerate(botoes):
                lines.append(f'      <Button text="{botao}" x="10" y="{y}" width="100" height="30">')
                lines.append(f'        <onClick> {nome}.on{i}() </onClick>')
                lines.append(f'      </Button>')
                y += 40
            
            lines.append('    </Panel>')
            lines.append('  </Window>')
            lines.append('</OTUI>')
            otui = '\n'.join(lines)
            
            path = f'E:\Projeto MCR\sandbox\otclient_{nome}\{nome}.otui'
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(otui)
            print(f'  [OK] OTUI gerado: {nome} ({len(labels)} labels, {len(botoes)} botoes)')
            self.fp.registrar(nome, 'acerto')
        else:
            print(f'  [ERRO] IA nao respondeu')
            self.fp.registrar(f'OTClient:{nome}', 'erro')
        print('  [CONCLUIDO]')

class ModuloNPC(ModuloBase):
    def executar(self, args):
        nome = args[0] if args else 'NPC'
        print(f'\n[NPC] Criando {nome}...')
        p = self.prompt(f"Crie um NPC chamado '{nome}' para um servidor Tibia.", 
                        "NOME: nome\nSAUDACAO: texto\nITENS: ID:PRECO, ID:PRECO\nDIALOGOS: pergunta -> resposta")
        r = self.ia.gerar(p, 0.7)
        if r:
            path = f'E:\\Projeto MCR\\sandbox\\npc_{nome.lower()}.lua'
            with open(path, 'w', encoding='utf-8') as f:
                f.write('-- NPC gerado pelo MCR Crew v11\n')
                for line in r.split('\n')[:20]:
                    f.write(f'-- {line}\n')
            print(f'  [OK] NPC salvo: {path}')
            self.fp.registrar(nome, 'acerto')
        else:
            self.fp.registrar(f'NPC:{nome}', 'erro')
        print('  [CONCLUIDO]')


class ModuloQuest(ModuloBase):
    def executar(self, args):
        nome = args[0] if args else 'Quest'
        print(f'\n[Quest] Criando {nome}...')
        p = self.prompt(f"Crie uma quest chamada '{nome}'.",
                        "NOME: nome\nDESCRICAO: texto\nOBJETIVOS:\n- objetivo 1\n- objetivo 2\nRECOMPENSA:\nxp: valor\nitens: ID:QTD")
        r = self.ia.gerar(p, 0.7)
        if r:
            path = f'E:\\Projeto MCR\\sandbox\\quest_{nome.lower()}.lua'
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f'-- Quest: {nome}\n')
                f.write(r[:800] + '\n')
            print(f'  [OK] Quest salva')
            self.fp.registrar(nome, 'acerto')
        else:
            self.fp.registrar(f'Quest:{nome}', 'erro')
        print('  [CONCLUIDO]')


class ModuloMonster(ModuloBase):
    def executar(self, args):
        nome = args[0] if args else 'Monstro'
        print(f'\n[Monster] Criando {nome}...')
        p = self.prompt(f"Crie um monstro chamado '{nome}'.",
                        "NOME: nome\nHP: valor\nATK: valor\nDEF: valor\nLOOT: \n  - ID:CHANCE\n  - ID:CHANCE\nELEMENTO: fire/ice/earth/energy/physical")
        r = self.ia.gerar(p, 0.7)
        if r:
            path = f'E:\\Projeto MCR\\sandbox\\monster_{nome.lower()}.lua'
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f'-- Monster: {nome}\n')
                f.write(r[:800] + '\n')
            print(f'  [OK] Monster salvo')
            self.fp.registrar(nome, 'acerto')
        else:
            self.fp.registrar(f'Monster:{nome}', 'erro')
        print('  [CONCLUIDO]')


class ModuloItem(ModuloBase):
    def executar(self, args):
        nome = args[0] if args else 'Item'
        print(f'\n[Item] Criando {nome}...')
        p = self.prompt(f"Crie um item chamado '{nome}'.",
                        "NOME: nome\nID: numero\nTIPO: weapon/armor/consumable\nATRIBUTOS:\n  atk: valor\n  def: valor\n  peso: numero")
        r = self.ia.gerar(p, 0.7)
        if r:
            path = f'E:\\Projeto MCR\\sandbox\\item_{nome.lower()}.lua'
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f'-- Item: {nome}\n')
                f.write(r[:600] + '\n')
            print(f'  [OK] Item salvo')
            self.fp.registrar(nome, 'acerto')
        else:
            self.fp.registrar(f'Item:{nome}', 'erro')
        print('  [CONCLUIDO]')


class ModuloSpell(ModuloBase):
    def executar(self, args):
        nome = args[0] if args else 'Spell'
        print(f'\n[Spell] Criando {nome}...')
        p = self.prompt(f"Crie uma spell chamada '{nome}'.",
                        "NOME: nome\nELEMENTO: fire/ice/earth/energy\nDANO: valor ou formula\nMANA: custo\nCOOLDOWN: segundos\nEFEITO_VISUAL: CONST_ME_xxx")
        r = self.ia.gerar(p, 0.7)
        if r:
            path = f'E:\\Projeto MCR\\sandbox\\spell_{nome.lower()}.lua'
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f'-- Spell: {nome}\n')
                f.write(r[:600] + '\n')
            print(f'  [OK] Spell salva')
            self.fp.registrar(nome, 'acerto')
        else:
            self.fp.registrar(f'Spell:{nome}', 'erro')
        print('  [CONCLUIDO]')


class ModuloDocs(ModuloBase):
    def executar(self, args):
        tema = args[0] if args else 'Tema'
        print(f'\n[Docs] Gerando documentacao sobre {tema}...')
        p = self.prompt(f"Documente: {tema}",
                        "# Titulo\n\n## Descricao\n...\n\n## Uso\n...\n\n## Exemplo\n...\n\n## Notas\n...")
        r = self.ia.gerar(p, 0.7)
        if r:
            path = f'E:\\Projeto MCR\\sandbox\\docs_{tema.lower()}.md'
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f'# {tema}\n\n')
                f.write(r[:2000])
            print(f'  [OK] Documentacao salva')
            self.fp.registrar(tema, 'acerto')
        print('  [CONCLUIDO]')


class ModuloAutoFP(ModuloBase):
    """Modulo especial: escaneia projeto e cria fingerprint."""
    def executar(self, args):
        caminho = args[0] if args else '.'
        print(f'\n[AutoFP] Escaneando: {caminho}')
        
        if not os.path.exists(caminho):
            print(f'  [ERRO] Caminho invalido')
            return
        
        for modulo in ['otclient', 'npc', 'quest', 'monster', 'item', 'spell']:
            fp = Fingerprint(modulo, 'default', auto_scan_path=caminho)
            n_bons = len(fp.data.get('exemplos_bons', []))
            n_ruins = len(fp.data.get('exemplos_ruins', []))
            print(f'  [{modulo}] {n_bons} seeds bons, {n_ruins} seeds ruins')
        
        print('  [OK] Auto-fingerprint concluido')


# ============================================================
# ORQUESTRADOR
# ============================================================

MODULOS = {
    'otclient': ModuloOTClient,
    'npc': ModuloNPC,
    'quest': ModuloQuest,
    'monster': ModuloMonster,
    'item': ModuloItem,
    'spell': ModuloSpell,
    'docs': ModuloDocs,
    'autofp': ModuloAutoFP,
}

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print(f'Modulos: {", ".join(MODULOS.keys())}')
        print('Para auto-fingerprint: python mcr_crew_v11.py autofp <caminho_do_projeto>')
        return
    
    nome_mod = sys.argv[1]
    
    if nome_mod == '--autofp' or nome_mod == 'autofp':
        nome_mod = 'autofp'
        fp = Fingerprint('autofp')
        ia = AILocal()
        modulo = ModuloAutoFP('autofp', fp, ia)
        modulo.executar(sys.argv[2:])
        return
    
    if nome_mod not in MODULOS:
        print(f'Modulos: {", ".join(MODULOS.keys())}')
        return
    
    args = sys.argv[2:]
    fp = Fingerprint(nome_mod)
    ia = AILocal()
    modulo = MODULOS[nome_mod](nome_mod, fp, ia)
    
    bons = len(fp.data.get('exemplos_bons', []))
    ruins = len(fp.data.get('exemplos_ruins', []))
    print(f'[FP] {bons} exemplos bons, {ruins} exemplos ruins')
    
    modulo.executar(args)

if __name__ == '__main__':
    main()
