"""NPC Generator — Geração de NPCs Lua para Canary.

Usa templates baseados em NPCs reais do servidor + LLM para preenchimento.
6 tipos: shop, quest, bank, gate, trainer, dialogue.

Uso:
    from modulos.npc_generator import NPCGenerator
    gen = NPCGenerator()
    resultado = gen.gerar("Ferreiro em Eridanus", "shop")
"""
import os, json, re, textwrap
from typing import Dict, Optional, List
from difflib import SequenceMatcher

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')

# ============================================================
# TEMPLATES LUA
# ============================================================

TEMPLATES = {}

# --- Template BASE (comum a todos) ---
TEMPLATE_BASE = """\
local internalNpcName = "{nome}"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {{}}

npcConfig.name = internalNpcName
npcConfig.description = "{descricao}"

npcConfig.health = 100
npcConfig.maxHealth = npcConfig.health
npcConfig.walkInterval = 2000
npcConfig.walkRadius = 2

npcConfig.outfit = {{
    lookType = {looktype},
    lookHead = 57,
    lookBody = 116,
    lookLegs = 97,
    lookFeet = 114,
    lookAddons = 0,
}}

npcConfig.flags = {{
    floorchange = false,
}}

{shop_config}

-- On buy npc shop message
npcType.onBuyItem = function(npc, player, itemId, subType, amount, ignore, inBackpacks, totalCost)
    npc:sellItem(player, itemId, amount, subType, 0, ignore, inBackpacks)
end
-- On sell npc shop message
npcType.onSellItem = function(npc, player, itemId, subtype, amount, ignore, name, totalCost)
    player:sendTextMessage(MESSAGE_TRADE, string.format("Sold %ix %s for %i gold.", amount, name, totalCost))
end
-- On check npc shop message (look item)
npcType.onCheckItem = function(npc, player, clientId, subType) end

local keywordHandler = KeywordHandler:new()
local npcHandler = NpcHandler:new(keywordHandler)

npcType.onThink = function(npc, interval)
    npcHandler:onThink(npc, interval)
end

npcType.onAppear = function(npc, creature)
    npcHandler:onAppear(npc, creature)
end

npcType.onDisappear = function(npc, creature)
    npcHandler:onDisappear(npc, creature)
end

npcType.onMove = function(npc, creature, fromPosition, toPosition)
    npcHandler:onMove(npc, creature, fromPosition, toPosition)
end

npcType.onSay = function(npc, creature, type, message)
    npcHandler:onSay(npc, creature, type, message)
end

npcType.onCloseChannel = function(npc, creature)
    npcHandler:onCloseChannel(npc, creature)
end

{conteudo_custom}

npcHandler:setMessage(MESSAGE_GREET, "{saudacao}")

{callbacks}

npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)

npcType:register(npcConfig)
"""

# --- Template SHOP ---
TEMPLATES['shop'] = {
    'shop_part': textwrap.dedent("""\
        npcConfig.shop = {{ -- Sellable items
            {{ itemName = "{item1_nome}", clientId = {item1_id}, buy = {item1_preco} }},
            {{ itemName = "{item2_nome}", clientId = {item2_id}, sell = {item2_preco} }},
            {{ itemName = "{item3_nome}", clientId = {item3_id}, buy = {item3_preco} }},
        }}
    """),
    'handler_part': textwrap.dedent("""\
        local function creatureSayCallback(npc, creature, type, message)
            local player = Player(creature)
            local playerId = player:getId()
        
            if not npcHandler:checkInteraction(npc, creature) then
                return false
            end
        
            if MsgContains(message, "trade") then
                npcHandler:say("Just ask me for a {{trade}} to see my offers.", npc, creature)
            end
        
            return true
        end
    """),
    'descricao': "Shop NPC - {nome}",
    'saudacao': "Welcome to {nome}'s shop! Need any {tipo_itens}?",
}

# --- Template QUEST ---
TEMPLATES['quest'] = {
    'shop_part': '',
    'handler_part': textwrap.dedent("""\
        local function creatureSayCallback(npc, creature, type, message)
            local player = Player(creature)
            local playerId = player:getId()
        
            if not npcHandler:checkInteraction(npc, creature) then
                return false
            end
        
            if MsgContains(message, "mission") or MsgContains(message, "quest") then
                if player:getStorageValue(Storage.{quest_storage}) < 1 then
                    npcHandler:say("{quest_start_text}", npc, creature)
                    npcHandler:setTopic(playerId, 1)
                else
                    npcHandler:say("{quest_progress_text}", npc, creature)
                    npcHandler:setTopic(playerId, 2)
                end
            elseif MsgContains(message, "yes") then
                if npcHandler:getTopic(playerId) == 1 then
                    player:setStorageValue(Storage.{quest_storage}, 1)
                    npcHandler:say("{quest_accept_text}", npc, creature)
                    npcHandler:setTopic(playerId, 0)
                elseif npcHandler:getTopic(playerId) == 2 then
                    if player:getItemCount({reward_item_id}) >= 1 then
                        player:removeItem({reward_item_id}, 1)
                        player:addItem({reward_item_id}, 1) -- TODO: ajustar reward
                        player:setStorageValue(Storage.{quest_storage}, 2)
                        npcHandler:say("{quest_complete_text}", npc, creature)
                    else
                        npcHandler:say("{quest_missing_item_text}", npc, creature)
                    end
                    npcHandler:setTopic(playerId, 0)
                end
            end
        
            return true
        end
        
        npcHandler:setCallback(CALLBACK_MESSAGE_DEFAULT, creatureSayCallback)
    """),
    'descricao': "Quest NPC - {nome}",
    'saudacao': "Greetings, adventurer! Are you looking for a {quest_term}?",
}

# --- Template BANK ---
TEMPLATES['bank'] = {
    'shop_part': '',
    'handler_part': textwrap.dedent("""\
        local function creatureSayCallback(npc, creature, type, message)
            local player = Player(creature)
            local playerId = player:getId()
        
            if not npcHandler:checkInteraction(npc, creature) then
                return false
            end
        
            if MsgContains(message, "balance") or MsgContains(message, "saldo") then
                local balance = player:getBankBalance()
                npcHandler:say(string.format("Your account balance is %d gold.", balance), npc, creature)
            elseif MsgContains(message, "deposit") then
                npcHandler:say("How much would you like to deposit?", npc, creature)
                npcHandler:setTopic(playerId, 1)
            elseif MsgContains(message, "withdraw") then
                npcHandler:say("How much would you like to withdraw?", npc, creature)
                npcHandler:setTopic(playerId, 2)
            elseif MsgContains(message, "yes") then
                if npcHandler:getTopic(playerId) == 1 then
                    npcHandler:say("Sorry, I need a specific amount.", npc, creature)
                    npcHandler:setTopic(playerId, 0)
                elseif npcHandler:getTopic(playerId) == 2 then
                    npcHandler:say("Sorry, I need a specific amount.", npc, creature)
                    npcHandler:setTopic(playerId, 0)
                end
            end
        
            return true
        end
        
        npcHandler:setCallback(CALLBACK_MESSAGE_DEFAULT, creatureSayCallback)
    """),
    'descricao': "Bank NPC - {nome}",
    'saudacao': "Welcome to the {bank_name}! How can I help you?",
}

# --- Template GATE ---
TEMPLATES['gate'] = {
    'shop_part': '',
    'handler_part': textwrap.dedent("""\
        local function creatureSayCallback(npc, creature, type, message)
            local player = Player(creature)
            local playerId = player:getId()
        
            if not npcHandler:checkInteraction(npc, creature) then
                return false
            end
        
            if MsgContains(message, "pass") or MsgContains(message, "entrance") or MsgContains(message, "let me in") then
                if player:getLevel() >= {gate_level} then
                    npcHandler:say("{gate_open_text}", npc, creature)
                    player:getPosition():sendMagicEffect(CONST_ME_TELEPORT)
                else
                    npcHandler:say(string.format("{gate_blocked_text}", {gate_level}), npc, creature)
                end
            end
        
            return true
        end
        
        npcHandler:setCallback(CALLBACK_MESSAGE_DEFAULT, creatureSayCallback)
    """),
    'descricao': "Gate NPC - {nome}",
    'saudacao': "Halt! State your business.",
}

# --- Template TRAINER ---
TEMPLATES['trainer'] = {
    'shop_part': '',
    'handler_part': textwrap.dedent("""\
        local function creatureSayCallback(npc, creature, type, message)
            local player = Player(creature)
            local playerId = player:getId()
        
            if not npcHandler:checkInteraction(npc, creature) then
                return false
            end
        
            if MsgContains(message, "train") or MsgContains(message, "learn") or MsgContains(message, "teach") then
                npcHandler:say("{train_offer_text}", npc, creature)
                npcHandler:setTopic(playerId, 1)
            elseif MsgContains(message, "spell") or MsgContains(message, "skill") then
                npcHandler:say("{train_spell_text}", npc, creature)
                npcHandler:setTopic(playerId, 2)
            elseif MsgContains(message, "yes") then
                if npcHandler:getTopic(playerId) == 1 then
                    npcHandler:say("{train_accept_text}", npc, creature)
                    npcHandler:setTopic(playerId, 0)
                elseif npcHandler:getTopic(playerId) == 2 then
                    npcHandler:say("{train_spell_accept_text}", npc, creature)
                    npcHandler:setTopic(playerId, 0)
                end
            end
        
            return true
        end
        
        npcHandler:setCallback(CALLBACK_MESSAGE_DEFAULT, creatureSayCallback)
    """),
    'descricao': "Trainer NPC - {nome}",
    'saudacao': "Welcome, pupil! Ready to improve your skills?",
}

# --- Template DIALOGUE ---
TEMPLATES['dialogue'] = {
    'shop_part': '',
    'handler_part': textwrap.dedent("""\
        keywordHandler:addKeyword({{"job"}}, StdModule.say, {{npcHandler = npcHandler, text = "{job_text}"}})
        keywordHandler:addAliasKeyword({{"work"}})
        keywordHandler:addKeyword({{"name"}}, StdModule.say, {{npcHandler = npcHandler, text = "{name_text}"}})
        keywordHandler:addKeyword({{"hint"}}, StdModule.say, {{npcHandler = npcHandler, text = "{hint_text}"}})
        keywordHandler:addAliasKeyword({{"help"}})
        keywordHandler:addAliasKeyword({{"info"}})
        
        local function creatureSayCallback(npc, creature, type, message)
            local player = Player(creature)
            local playerId = player:getId()
        
            if not npcHandler:checkInteraction(npc, creature) then
                return false
            end
        
            if MsgContains(message, "bye") then
                npcHandler:say("{farewell_text}", npc, creature)
            end
        
            return true
        end
        
        npcHandler:setCallback(CALLBACK_MESSAGE_DEFAULT, creatureSayCallback)
    """),
    'descricao': "Dialogue NPC - {nome}",
    'saudacao': "Hello there, traveler!",
}

# ============================================================
# GERADOR DE NPC
# ============================================================

class NPCGenerator:
    """Gera scripts Lua de NPCs para Canary usando templates + LLM."""
    
    def __init__(self, modelo_llm: Optional[str] = None):
        self.modelo = modelo_llm or "qwen2.5-coder:7b"
        self._ultimo_npc = None
    
    def gerar(self, descricao: str, tipo: str = 'shop', nome: Optional[str] = None,
              exemplos: Optional[List[Dict]] = None) -> Dict:
        """Gera um NPC completo.
        
        Args:
            descricao: Descrição do NPC (ex: "Ferreiro em Eridanus que vende armas")
            tipo: Tipo do NPC (shop/quest/bank/gate/trainer/dialogue)
            nome: Nome do NPC (opcional - gerado se não fornecido)
            exemplos: NPCs reais do CanaryIndexer para usar como inspiração
        
        Returns:
            Dict com { 'codigo': str, 'arquivo': str, 'nome': str, 'tipo': str, 'erro': str }
        """
        if tipo not in TEMPLATES:
            return {'erro': 'Tipo invalido: %s' % tipo, 'codigo': '', 'arquivo': '', 'nome': ''}
        
        # Gerar placeholders (usa exemplos reais se disponiveis, senao LLM)
        placeholders = self._gerar_placeholders(descricao, tipo, nome, exemplos=exemplos)
        if 'erro' in placeholders:
            return placeholders
        
        # Montar código
        codigo = self._montar_codigo(tipo, placeholders)
        
        # Salvar
        nome_arquivo = placeholders.get('nome', 'npc_desconhecido').lower().replace(' ', '_').replace("'", '')
        caminho = os.path.join(SANDBOX, '%s.lua' % nome_arquivo)
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(codigo)
        
        resultado = {
            'codigo': codigo,
            'arquivo': caminho,
            'nome': placeholders.get('nome', 'unknown'),
            'tipo': tipo,
            'erro': '',
        }
        self._ultimo_npc = resultado
        return resultado
    
    def _gerar_placeholders(self, descricao: str, tipo: str, nome: Optional[str] = None,
                            exemplos: Optional[List[Dict]] = None) -> Dict:
        """Gera placeholders usando LLM ou exemplos reais."""
        template = TEMPLATES[tipo]
        placeholders_base = {
            'nome': nome or self._gerar_nome(descricao, tipo),
            'descricao': template['descricao'],
            'saudacao': template['saudacao'],
        }
        
        # Placeholders específicos por tipo
        extras = self._placeholders_por_tipo(tipo, descricao, placeholders_base, exemplos=exemplos)
        if 'erro' in extras:
            return extras
        
        placeholders_base.update(extras)
        
        # Resolver placeholders aninhados (ex: {nome} dentro de saudacao)
        for _ in range(3):  # max 3 iteracoes para resolver aninhamento
            alterado = False
            for k, v in list(placeholders_base.items()):
                if isinstance(v, str) and '{' in v:
                    try:
                        novo = v.format(**placeholders_base)
                        if novo != v:
                            placeholders_base[k] = novo
                            alterado = True
                    except (KeyError, ValueError):
                        pass
            if not alterado:
                break
        
        return placeholders_base
    
    def _gerar_nome(self, descricao: str, tipo: str = 'shop') -> str:
        """Gera um nome de NPC baseado na descricao."""
        # Tenta extrair nome da descrição
        m = re.search(r'(?:chamado|nome|se chama)\s+(\w+)', descricao, re.IGNORECASE)
        if m:
            return m.group(1)
        
        # Fallback: nomes fantasy comuns em Tibia
        nomes_fallback = [
            'Ferraduro', 'Ferronius', 'Açorius', 'Gorthan', 
            'Mithrilus', 'Durin', 'Balthor', 'Kardan'
        ]
        tipo_map = {
            'shop': ['Mercador', 'Vendedor', 'Comerciante'],
            'quest': ['Sábio', 'Velho', 'Mestre'],
            'bank': ['Banqueiro', 'Tesoureiro', 'Guarda-Livros'],
            'gate': ['Guarda', 'Sentinela', 'Vigia'],
            'trainer': ['Mestre', 'Instrutor', 'Professor'],
            'dialogue': ['Andarilho', 'Mensageiro', 'Bob'],
        }
        sufixos = tipo_map.get(tipo, ['NPC'])
        import random
# MCRzificado: usa MCR quando disponivel, fallback para LLM
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', '..', '..'))
try:
    from MCR import MCRMotor, MCRGenerator, MCRValidator, MCRBuilder, MCRPreencher, MCRReconstructor
    _mcr = MCRMotor()
    _TEM_MCR = True
except ImportError:
    _TEM_MCR = False
        return random.choice(sufixos) + ' ' + random.choice(nomes_fallback)
    
    def _placeholders_por_tipo(self, tipo: str, descricao: str, base: Dict,
                                exemplos: Optional[List[Dict]] = None) -> Dict:
        """Gera placeholders específicos para cada tipo de NPC.
        
        Se exemplos reais do CanaryIndexer forem fornecidos, usa itens reais
        em vez de placeholders genéricos.
        """
        placeholders = {}
        
        if tipo == 'shop':
            # Tentar usar exemplos REAIS do CanaryIndexer primeiro
            if exemplos:
                for ex in exemplos:
                    shop_items = ex.get('itens_shop', []) or ex.get('itens', [])
                    if shop_items:
                        for i, item in enumerate(shop_items):
                            placeholders[f'item{i+1}_nome'] = item.get('nome', 'item')
                            placeholders[f'item{i+1}_id'] = item.get('client_id', 3003)
                            preco = item.get('sell') or item.get('buy') or item.get('preco', 50)
                            placeholders[f'item{i+1}_preco'] = preco
                        placeholders['tipo_itens'] = ex.get('tipo_itens', 'equipment')
                        break  # usa o primeiro NPC que tiver itens
            
            # Se NAO encontrou nos exemplos, usa placeholders genericos
            if 'item1_nome' not in placeholders:
                placeholders.update({
                    'tipo_itens': 'equipment',
                    'item1_nome': 'example item',
                    'item1_id': 3003,
                    'item1_preco': 50,
                    'item2_nome': 'another item',
                    'item2_id': 3457,
                    'item2_preco': 10,
                    'item3_nome': 'third item',
                    'item3_id': 2920,
                    'item3_preco': 2,
                })
        
        elif tipo == 'quest':
            placeholders.update({
                'quest_storage': 'Quest.Custom.' + base.get('nome', 'Quest').upper().replace(' ', ''),
                'quest_term': 'mission',
                'quest_start_text': 'I need your help!',
                'quest_progress_text': 'Have you completed the task yet?',
                'quest_accept_text': 'Thank you! Now go and complete the task.',
                'quest_complete_text': 'Well done! Here is your reward.',
                'quest_missing_item_text': 'You still need to bring me the required item.',
                'reward_item_id': 3031,
            })
        
        elif tipo == 'bank':
            placeholders.update({
                'bank_name': base.get('nome', 'Bank of Tibia'),
            })
        
        elif tipo == 'gate':
            placeholders.update({
                'gate_level': 20,
                'gate_open_text': 'You may pass.',
                'gate_blocked_text': 'You need level %d to pass.',
            })
        
        elif tipo == 'trainer':
            placeholders.update({
                'train_offer_text': 'I can teach you a few things. What would you like to learn?',
                'train_spell_text': 'Here are the spells I can teach you.',
                'train_accept_text': 'Excellent! Let us begin the training.',
                'train_spell_accept_text': 'A wise choice. Let me teach you.',
            })
        
        elif tipo == 'dialogue':
            placeholders.update({
                'job_text': 'I am just a humble traveler.',
                'name_text': 'My name is ' + base.get('nome', 'NPC') + '.',
                'hint_text': 'Explore the world and you shall find what you seek.',
                'farewell_text': 'Safe travels!',
            })
        
        return placeholders
    
    def _montar_codigo(self, tipo: str, placeholders: Dict) -> str:
        """Monta o código Lua completo a partir dos placeholders."""
        template = TEMPLATES[tipo]
        
        # Formatar shop_config
        shop_config = template['shop_part']
        if shop_config:
            shop_config = shop_config.format(**placeholders)
        
        # Formatar conteudo_custom
        handler_part = template['handler_part']
        conteudo_custom = ''
        if handler_part:
            try:
                conteudo_custom = handler_part.format(**placeholders)
            except KeyError as e:
                conteudo_custom = '-- [[ Erro ao gerar handler: %s ]]\n' % str(e)
        
        # Formatar callback (handler)        
        callbacks = ''
        if conteudo_custom:
            callbacks = 'npcHandler:setCallback(CALLBACK_MESSAGE_DEFAULT, creatureSayCallback)'
        
        # Montar código final
        codigo = TEMPLATE_BASE.format(
            nome=placeholders.get('nome', 'NPC'),
            descricao=placeholders.get('descricao', ''),
            looktype=placeholders.get('looktype', 130),
            saudacao=placeholders.get('saudacao', 'Hello!'),
            shop_config=shop_config,
            conteudo_custom=conteudo_custom,
            callbacks=callbacks,
        )
        
        return codigo


# ============================================================
# PONTO DE ENTRADA
# ============================================================

if __name__ == '__main__':
    gen = NPCGenerator()
    
    for tipo in ['shop', 'quest', 'dialogue']:
        print('=== Gerando %s ===' % tipo)
        resultado = gen.gerar('NPC %s em Eridanus' % tipo, tipo)
        if resultado.get('erro'):
            print('ERRO:', resultado['erro'])
        else:
            print('Nome:', resultado['nome'])
            print('Arquivo:', resultado['arquivo'])
            print('Codigo (%d linhas):' % len(resultado['codigo'].split('\n')))
            print(resultado['codigo'] + '...')
        print()
