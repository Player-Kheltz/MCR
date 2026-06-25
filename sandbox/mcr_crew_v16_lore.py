#!/usr/bin/env python3
"""
MCR CREW V16 — LORE ENGINE + Deep Creative Layer
====================================================
Camada de criatividade profunda para o MCR Crew.

Funciona como um sub-crew especializado:
  - Recebe um "blank" (ex: nome de NPC)
  - Pesquisa no banco de lore mundial
  - Gera historia, personalidade, dialogo
  - Retorna o texto enriquecido

O banco de lore CRESCE com cada uso.
"""

import sys, os, json, re, hashlib, urllib.request, datetime, random

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE_LORE = r'E:\Projeto MCR\sandbox\.lore_engine'
os.makedirs(BASE_LORE, exist_ok=True)

# ============================================================
# WORLD LORE DATABASE — Conhecimento do mundo
# ============================================================

class WorldLore:
    """
    Banco de conhecimento do mundo de Eridanus.
    Cada entrada alimenta a IA na hora de criar conteudo profundo.
    """
    
    def __init__(self):
        self.path = os.path.join(BASE_LORE, 'world.json')
        self.data = self._carregar()
    
    def _carregar(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f: return json.load(f)
        
        # Lore INICIAL do mundo (pode crescer)
        return {
            'mundo': {
                'nome': 'Eridanus',
                'era': 'Terceira Era',
                'descricao': 'Uma cidade-estado fundada ha tres seculos por tres herois.',
            },
            'cidades': {
                'eridanus': {
                    'nome': 'Eridanus',
                    'fundacao': 'Ha 300 anos',
                    'fundadores': ['Aeliana, a Mago', 'Thorn, o Guerreiro', 'Lyra, a Protetora'],
                    'descricao': 'Construida sobre um antigo vilarejo, Eridanus prospera as margens do Lago Azure.',
                    'locais': ['Mina Abandonada', 'Ruinas do Templo', 'Biblioteca Antiga', 'Lago Azure', 'Praca Central'],
                }
            },
            'racas': {
                'humanos': 'A maioria dos habitantes de Eridanus. Conhecidos por sua resiliencia.',
                'elfos': 'Raros na cidade, mas respeitados por sua sabedoria antiga.',
                'anoes': 'Habitam as profundezas da Mina Abandonada. Conhecem os segredos da pedra.',
            },
            'personagens': {},
            'itens_lendarios': {},
            'eventos': {},
            'metricas': {'lore_criado': 0, 'lore_usado': 0},
        }
    
    def salvar(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def registrar_personagem(self, nome, info):
        """Aprende sobre um novo personagem."""
        self.data['personagens'][nome.lower()] = info
        self.data['metricas']['lore_criado'] += 1
        self.salvar()
    
    def registrar_item(self, nome, info):
        """Aprende sobre um novo item lendario."""
        self.data['itens_lendarios'][nome.lower()] = info
        self.salvar()
    
    def get_contexto_mundo(self):
        """Retorna contexto do mundo para alimentar a IA."""
        ctx = []
        mundo = self.data.get('mundo', {})
        ctx.append(f"MUNDO: {mundo.get('nome','')} - {mundo.get('descricao','')}")
        
        for cidade, info in self.data.get('cidades', {}).items():
            ctx.append(f"CIDADE {cidade.upper()}: {info.get('descricao','')}")
            ctx.append(f"  Fundadores: {', '.join(info.get('fundadores',[]))}")
            ctx.append(f"  Locais: {', '.join(info.get('locais',[]))}")
        
        if self.data.get('personagens'):
            ctx.append("PERSONAGENS CONHECIDOS:")
            for nome, info in list(self.data['personagens'].items())[:5]:
                ctx.append(f"  {nome}: {info.get('historia','')[:80]}...")
        
        return '\n'.join(ctx)


# ============================================================
# IA LORE LOCAL
# ============================================================

class IALore:
    def __init__(self, model='qwen2.5-coder:7b'):
        self.model = model
        self.cache = {}
    
    def gerar(self, prompt, temp=0.85):
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
# LORE GENERATOR — Cria historia profunda
# ============================================================

class LoreGenerator:
    """
    Gera lore profundo para QUALQUER entidade:
    - NPCs (historia, personalidade, dialogo)
    - Quests (narrativa, objetivos com proposito)
    - Items (historia, origem, poder)
    - Locais (descricao, atmosfera, segredos)
    """
    
    def __init__(self, world, ia):
        self.world = world
        self.ia = ia
    
    def gerar_lore_npc(self, nome, cargo='', cidade='eridanus'):
        """Gera historia completa para um NPC."""
        ctx_mundo = self.world.get_contexto_mundo()
        
        prompt = f"""Crie um NPC com HISTORIA PROFUNDA para o jogo Tibia.

MUNDO:
{ctx_mundo}

NPC: {nome}
CARGO: {cargo or 'morador'}
CIDADE: {cidade}

Crie:
1. HISTORIA COMPLETA (2-3 paragrafos): passado, motivacoes, segredos
2. PERSONALIDADE (3-5 tracos)
3. DIALOGO DE SAUDACAO (1-2 frases que revelam a personalidade)
4. SEGREDO: algo que o NPC esconde
5. CONEXOES: com quem mais ele se relaciona na cidade

Formato da resposta (siga exatamente):
HISTORIA: texto
PERSONALIDADE: traco1, traco2, traco3
SAUDACAO: "texto do dialogo"
SEGREDO: texto
CONEXOES: nome1, nome2"""
        
        r = self.ia.gerar(prompt, 0.85)
        
        lore = self._parse_resposta(r, ['HISTORIA', 'PERSONALIDADE', 'SAUDACAO', 'SEGREDO', 'CONEXOES'])
        
        # Registra no banco mundial
        if lore.get('HISTORIA'):
            self.world.registrar_personagem(nome.lower(), {
                'nome': nome,
                'cargo': cargo,
                'historia': lore.get('HISTORIA', ''),
                'personalidade': lore.get('PERSONALIDADE', ''),
				'segredo': lore.get('SEGREDO', ''),
                'criado_em': str(datetime.datetime.now()),
            })
        
        return lore
    
    def gerar_lore_quest(self, nome, nivel=1):
        """Gera narrativa profunda para uma quest."""
        ctx_mundo = self.world.get_contexto_mundo()
        
        prompt = f"""Crie uma QUEST com NARRATIVA PROFUNDA.

MUNDO:
{ctx_mundo}

QUEST: {nome}
NIVEL MINIMO: {nivel}

Crie:
1. INTRODUCAO (2-3 paragrafos): o que esta acontecendo e porque o jogador deve se importar
2. OBJETIVOS COM PROPOSITO (nao apenas "mate X", mas explique POR QUE)
3. REVELACAO: o que o jogador descobre no final
4. CONEXAO COM O MUNDO: como isso afeta Eridanus

Formato:
INTRODUCAO: texto
OBJETIVOS: 
  - objetivo 1: proposito
  - objetivo 2: proposito
REVELACAO: texto
CONEXAO: texto"""
        
        r = self.ia.gerar(prompt, 0.85)
        return self._parse_resposta(r, ['INTRODUCAO', 'OBJETIVOS', 'REVELACAO', 'CONEXAO'])
    
    def gerar_lore_item(self, nome, tipo='item'):
        """Gera historia para um item."""
        ctx_mundo = self.world.get_contexto_mundo()
        
        prompt = f"""Crie um ITEM com HISTORIA para o jogo Tibia.

MUNDO:
{ctx_mundo}

ITEM: {nome}
TIPO: {tipo}

Crie:
1. DESCRICAO FISICA (2-3 frases): como o item parece
2. ORIGEM: de onde veio, quem o criou
3. PODER/EFEITO: o que ele faz alem do obvio
4. LENDA: o que os habitantes dizem sobre ele

Formato:
DESCRICAO: texto
ORIGEM: texto
PODER: texto
LENDA: texto"""
        
        r = self.ia.gerar(prompt, 0.85)
        lore = self._parse_resposta(r, ['DESCRICAO', 'ORIGEM', 'PODER', 'LENDA'])
        
        if lore.get('ORIGEM'):
            self.world.registrar_item(nome.lower(), lore)
        
        return lore
    
    def gerar_lore_local(self, nome, cidade='eridanus'):
        """Gera descricao para um local."""
        ctx_mundo = self.world.get_contexto_mundo()
        
        prompt = f"""Crie um LOCAL com ATMOSFERA para o jogo Tibia.

MUNDO:
{ctx_mundo}

LOCAL: {nome}
CIDADE: {cidade}

Crie:
1. APARENCIA (2-3 frases): como o local parece, cheiros, sons
2. HISTORIA: o que aconteceu aqui
3. PERIGO: o que espreita nas sombras
4. SEGREDO: algo que poucos sabem

Formato:
APARENCIA: texto
HISTORIA: texto
PERIGO: texto
SEGREDO: texto"""
        
        r = self.ia.gerar(prompt, 0.85)
        return self._parse_resposta(r, ['APARENCIA', 'HISTORIA', 'PERIGO', 'SEGREDO'])
    
    def _parse_resposta(self, texto, campos):
        """Extrai campos - parser flexivel."""
        resultado = {}
        if not texto: return resultado
        
        for campo in campos:
            # Tenta varios padroes
            for padrao in [
                rf'{campo}:\s*(.+?)(?=\n[A-Z][A-Z ]+:|\Z)',
                rf'{campo}:\s*(.+?)(?=\n\d|\Z)',
                rf'\*\*{campo}\*\*:?\s*(.+?)(?=\n\*\*|\Z)',
            ]:
                try:
                    m = re.search(padrao, texto, re.DOTALL | re.IGNORECASE)
                    if m:
                        val = m.group(1).strip().strip('*\n\r ')
                        if len(val) > 15:
                            resultado[campo] = val[:500]
                            break
                except: pass
        
        return resultado


# ============================================================
# INTEGRACAO COM MCR CREW TEMPLATES
# ============================================================

class LoreTemplateIntegrator:
    """
    Integra o lore engine com os templates do MCR Crew.
    O template pode chamar {lore_npc}, {lore_quest} etc.
    e o lore engine preenche com historia profunda.
    """
    
    # Mapa: blank do template -> funcao de lore
    MAPA = {
        'lore_npc': ('gerar_lore_npc', ['HISTORIA', 'SAUDACAO', 'PERSONALIDADE']),
        'lore_quest': ('gerar_lore_quest', ['INTRODUCAO', 'OBJETIVOS']),
        'lore_item': ('gerar_lore_item', ['DESCRICAO', 'ORIGEM', 'PODER']),
        'lore_local': ('gerar_lore_local', ['APARENCIA', 'HISTORIA']),
    }
    
    @staticmethod
    def enriquecer_template(template, gerador_lore, **kwargs):
        """
        Substitui {lore_*} blanks no template por lore gerado.
        Ex: template = "NPC: {nome}\nHistoria: {lore_npc}"
        """
        import re
        
        def enriquecer(match):
            blank = match.group(1)
            if blank in LoreTemplateIntegrator.MAPA:
                func_name, campos = LoreTemplateIntegrator.MAPA[blank]
                func = getattr(gerador_lore, func_name, None)
                if func:
                    # Passa kwargs como parametros
                    lore = func(**kwargs)
                    if lore:
                        # Retorna o primeiro campo como preenchimento
                        for campo in campos:
                            if campo in lore:
                                return lore[campo][:200]
                        return str(lore)
            return match.group(0)
        
        return re.sub(r'\{lore_(\w+)\}', enriquecer, template)


# ============================================================
# DEMO
# ============================================================

def demo():
    print('='*60)
    print('  MCR CREW V16 — LORE ENGINE')
    print('  Criatividade profunda para o MCR Crew')
    print('='*60)
    
    world = WorldLore()
    ia = IALore()
    gerador = LoreGenerator(world, ia)
    
    print(f'\nBanco de lore inicial: {len(world.data["personagens"])} personagens')
    print(f'Contexto do mundo carregado: {world.data["mundo"]["nome"]}')
    
    # Testa geracao de lore para NPC
    print('\n--- TESTE: LORE PARA NPC ---')
    lore_npc = gerador.gerar_lore_npc('Velho Sabio', 'Guardiao do Conhecimento')
    for campo, valor in lore_npc.items():
        print(f'  {campo}: {str(valor)[:100]}...')
    
    # Testa geracao de lore para Quest
    print('\n--- TESTE: LORE PARA QUEST ---')
    lore_quest = gerador.gerar_lore_quest('O Legado Perdido de Eridanus', 10)
    for campo, valor in lore_quest.items():
        print(f'  {campo}: {str(valor)[:100]}...')
    
    # Testa geracao de lore para Item
    print('\n--- TESTE: LORE PARA ITEM ---')
    lore_item = gerador.gerar_lore_item('Olho de Eridanus', 'artefato')
    for campo, valor in lore_item.items():
        print(f'  {campo}: {str(valor)[:100]}...')
    
    # Estatisticas
    print(f'\n--- ESTATISTICAS ---')
    print(f'Personagens no banco: {len(world.data["personagens"])}')
    print(f'Itens lendarios: {len(world.data["itens_lendarios"])}')
    print(f'Lore criado: {world.data["metricas"]["lore_criado"]}')

if __name__ == '__main__':
    demo()
