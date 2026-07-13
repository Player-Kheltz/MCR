"""mcr.shadow_canary — Ambiente Mock para execucao de scripts Lua sem servidor real.
Simula as APIs do Canary para detectar crashes antes de ir para producao."""
import os
import sys
import time
import re
import json
from pathlib import Path
from typing import Dict, Optional, List

from mcr.paths import DEVIA_KERNEL_DIR, KG_DIR
from mcr.encoding import read_file
from mcr.anti_pattern import classificar_erro, registrar_anti_pattern

# Tenta lupa (LuaJIT Python binding) — mesmo usado pelo LuaSyntaxValidator
_HAS_LUPA = False
_lupa = None
try:
    from lupa import LuaRuntime
    _lupa = LuaRuntime(unpack_returned_tuples=True)
    _HAS_LUPA = True
except ImportError:
    pass


def _gerar_mock_lua() -> str:
    """Gera um ambiente mock completo em Lua com todas as APIs do Canary.
    
    O mock define globals falsas que retornam tabelas vazias ou stubs,
    permitindo que scripts Lua gerados rodem sem um servidor real.
    """
    return '''
-- ============================================================
-- SHADOW CANARY MOCK — APIs simuladas do servidor Canary
-- ============================================================

-- Game API
Game = {}
function Game.createNpcType(name)
    local obj = {_name = name, _registered = false}
    function obj:register(config) self._registered = true; return true end
    return obj
end
function Game.createMonsterType(name)
    local obj = {_name = name}
    function obj:register(config) return true end
    return obj
end
function Game.createMonster(name, pos, ...) return {_name = name, setTarget = function() end} end
function Game.createItem(id, count) return {_id = id, _count = count, remove = function() end} end
function Game.getStorageValue(id) return -1 end
function Game.setStorageValue(id, val) end

-- NpcType
function NpcType() return {} end
npcType = {register = function(self, config) return true end}

-- StdModule (keyword handlers padrao)
StdModule = {}
StdModule.say = function(npc, player, text, config) return true end
StdModule.trade = function(npc, player, text, config) return true end
StdModule.yes = function(npc, player, text, config) return true end
StdModule.no = function(npc, player, text, config) return true end

-- NpcHandler
NpcHandler = {}
function NpcHandler:new()
    return {
        addModule = function(self, ...) return true end,
        setTopic = function(self, t) end,
        setMessage = function(self, m, t) end,
        onThink = function(self, npc, interval) end,
        onAppear = function(self, npc, creature) end,
        onDisappear = function(self, npc, creature) end,
        onMove = function(self, npc, creature, from, to) end,
        onSay = function(self, npc, creature, type, message) end,
        onCloseChannel = function(self, npc, creature) end,
        onBuyItem = function(self, ...) return true end,
        onSellItem = function(self, ...) return true end,
        onCheckItem = function(self, ...) return true end,
    }
end

-- FocusModule
FocusModule = {}
function FocusModule:new()
    return { onGreet = function() end, onDismiss = function() end }
end

-- KeywordHandler
KeywordHandler = {}
function KeywordHandler:new()
    return {addKeyword = function(self, kw, mod, cfg) return true end, 
            addAliasKeyword = function(self, kw) return true end,
            setMessage = function(self, m) end}
end

-- FocusModule
FocusModule = {}
function FocusModule:new() return {addFocus = function() end} end

-- Action
Action = {}
function Action:new()
    return {onUse = function() return true end, uid = function(self, id) self._uid = id end, register = function(self) return true end}
end
function Action:create()
    return {onUse = function() return true end, uid = function(self, id) self._uid = id end, register = function(self) return true end}
end
-- Para chamadas diretas Action() sem .new
setmetatable(Action, {__call = function()
    return {onUse = function() return true end, uid = function(self, id) self._uid = id end, register = function(self) return true end}
end})

-- Player
Player = {}
function Player:getName() return "MockPlayer" end
function Player:getPosition() return {x = 100, y = 100, z = 7} end
function Player:getStorageValue(id) return -1 end
function Player:setStorageValue(id, val) end
function Player:addItem(id, count) return true end
function Player:removeItem(id, count) return true end
function Player:addMoney(money) return true end
function Player:removeMoney(money) return true end
function Player:getMana() return 100 end
function Player:getHealth() return 1000 end
function Player:sendTextMessage(msgType, text) end
function Player:sendCancelMessage(text) end
function Player:say(text, talkType) end
function Player:getLevel() return 100 end
function Player:getVocation() return 1 end
function Player:getGuid() return 1 end

-- Item
Item = {}
function Item:getId() return 100 end
function Item:getType() return {getClientId = function() return 100 end} end
function Item:remove() end
function Item:getPosition() return {x = 100, y = 100, z = 7} end
function Item:getActionId() return 0 end
function Item:setActionId(id) end
function Item:getUniqueId() return 0 end
function Item:setUniqueId(id) end

-- Position
Position = {}
function Position:new(x, y, z) return {x = x, y = y, z = z} end
function Position:add(x, y) return {x = self.x + x, y = self.y + y, z = self.z} end
function Position:__add(x, y) return {x = self.x + x, y = self.y + y, z = self.z} end

-- Container
Container = {}
function Container:new() return {getItems = function() return {} end, getItemHoldingCount = function() return 0 end} end

-- MonsterType (para monsterConfig)
monsterConfig = {name = "", description = "", maxHealth = 0, experience = 0, outfit = {lookType = 0},
                 flags = {attackable = true}, dropList = {}}
monsterType = {register = function(self) return true end}

-- CreatureEvent
CreatureEvent = {}
function CreatureEvent:new(name) return {register = function() end} end

-- GlobalEvent
GlobalEvent = {}
function GlobalEvent:new(name) return {register = function() end} end

-- MoveEvent
MoveEvent = {}
function MoveEvent:new(name) return {register = function() end} end

-- Spell
Spell = {}
function Spell:new(name) return {register = function() end} end

-- TalkAction
TalkAction = {}
function TalkAction:new(name) return {register = function() end} end

-- Message constants
MESSAGE_INFO_DESCR = 1
MESSAGE_EVENT_ADVANCE = 2
MESSAGE_STATUS_WARNING = 3
MESSAGE_DEFAULT = 4
MESSAGE_FAILURE = 5
MESSAGE_TRADE = 6
MESSAGE_STATUS_SMALL = 7
MESSAGE_INFO = 8

-- TalkType constants
TALKTYPE_MONSTER_SAY = 1
TALKTYPE_SAY = 2

-- Effect constants
CONST_ME_FIRE = 6
CONST_ME_ICE = 7
CONST_ME_EARTH = 8
CONST_ME_ENERGY = 9
CONST_ME_MAGIC = 10

-- NpcConfig
npcConfig = {name = "", description = "", outfit = {lookType = 0}, health = 100, maxHealth = 100,
             walkInterval = 2000, walkRadius = 2, shop = {}}

-- HABILIDADES (SPA)
HABILIDADES = {}
HABILIDADES_NPC = {}

-- toLatin1 (protocolo)
function toLatin1(s) return s end

-- print (seguro)
function print(...) end

-- math (padrao)
math = math or {}
string = string or {}
table = table or {}

print("[ShadowCanary] Mock ambiente carregado com sucesso")
'''


def validar_sintaxe(codigo: str) -> Dict:
    """Valida sintaxe Lua usando LuaSyntaxValidator (sandbox + loadstring).
    
    Returns:
        dict com 'valido', 'erro'
    """
    if not codigo or len(codigo) < 10:
        return {'valido': False, 'erro': 'Codigo vazio ou muito curto'}

    try:
        import sys as _sys
        _sys.path.insert(0, str(DEVIA_KERNEL_DIR))
        from LuaSyntaxValidator import verificar_sintaxe as _vs
        valido, erro = _vs(codigo)
        return {'valido': valido, 'erro': erro}
    except Exception as e:
        return {'valido': False, 'erro': str(e)}


def executar_shadow_test(caminho_lua: Path) -> Dict:
    """Executa um script Lua contra o ambiente mock do Shadow Canary.
    
    Fluxo:
    1. Le o arquivo .lua
    2. Valida sintaxe
    3. Prepend o mock Lua
    4. Executa via lupa (LuaJIT)
    5. Se crashar, classifica e registra anti-pattern automaticamente
    
    Returns:
        dict com 'status' ('pass', 'crash', 'erro'), 'log', 'erro', 'linha'
    """
    if not caminho_lua.exists():
        return {'status': 'erro', 'erro': 'Arquivo nao encontrado'}

    try:
        codigo = read_file(caminho_lua)
    except Exception as e:
        return {'status': 'erro', 'erro': str(e)}

    # 1. Valida sintaxe
    sintaxe = validar_sintaxe(codigo)
    if not sintaxe['valido']:
        return {'status': 'erro', 'erro': 'Erro de sintaxe: ' + (sintaxe['erro'] or '')}

    if not _HAS_LUPA:
        return {'status': 'pass', 'log': 'lupa nao disponivel — validacao por sintaxe apenas'}

    # 2. Prepend mock
    mock = _gerar_mock_lua()
    codigo_completo = mock + '\n\n-- === SCRIPT GERADO ===\n' + codigo

    # 3. Executa via lupa
    try:
        lr = LuaRuntime(unpack_returned_tuples=True)

        # Tenta executar o codigo completo (mock + script)
        try:
            lr.execute(codigo_completo)
            return {'status': 'pass', 'log': 'Shadow execution OK.'}
        except SyntaxError as e:
            return {'status': 'crash', 'erro': 'Erro de sintaxe: %s' % e, 'linha': 0}
        except Exception as e:
            # Captura o erro de runtime
            erro_msg = str(e)
            linha = 0

            # Tenta extrair a linha do erro
            m_linha = re.search(r'line (\d+)', erro_msg, re.IGNORECASE)
            if m_linha:
                linha = int(m_linha.group(1))

            # Tenta extrair a API problematica
            api_problematica = ''
            m_api = re.search(r"'(\w+)'", erro_msg)
            if m_api:
                api_problematica = m_api.group(1)

            resultado = {
                'status': 'crash',
                'erro': erro_msg[:300],
                'linha': linha,
                'api_problematica': api_problematica,
            }

            # Auto-registra anti-pattern
            if api_problematica:
                erro_anti = classificar_erro(erro_msg, str(caminho_lua))
                registrar_anti_pattern(erro_anti)
                resultado['anti_pattern_registrado'] = True
                resultado['categoria'] = erro_anti['categoria']
                # Auto-aprendizado Markov
                aprender_com_erro(resultado)
            else:
                resultado['anti_pattern_registrado'] = False

            return resultado

    except Exception as e:
        return {'status': 'erro', 'erro': 'Falha no LuaRuntime: %s' % e}


def executar_shadow_codigo(codigo: str) -> Dict:
    """Executa uma string de codigo Lua diretamente no Shadow Canary."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.lua', mode='w', encoding='utf-8', delete=False) as f:
        f.write(codigo)
        tmp = f.name
    try:
        return executar_shadow_test(Path(tmp))
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass


def aprender_com_erro(resultado: Dict) -> Optional[str]:
    """Aprende com um erro de execucao do Shadow Canary.
    
    Se o erro for 'attempt to index a nil value (field/global X)',
    registra X como uma transicao Markov de penalidade no KG
    para que o sistema evite usar X no futuro neste contexto.
    
    Args:
        resultado: dict retornado por executar_shadow_test()
    
    Returns:
        nome da API penalizada, ou None se nao houve aprendizado
    """
    if resultado.get('status') != 'crash':
        return None

    erro_msg = resultado.get('erro', '')
    api_problematica = resultado.get('api_problematica', '')

    # Extrai a API do erro se nao foi capturada
    if not api_problematica:
        m_api = re.search(r"(?:field|global)\s+'(\w+)'", erro_msg)
        if m_api:
            api_problematica = m_api.group(1)

    if not api_problematica:
        return None

    # Registra como anti-pattern no KG
    erro_classificado = classificar_erro(erro_msg, str(resultado.get('arquivo', '')))
    erro_classificado['api_problematica'] = api_problematica
    erro_classificado['categoria'] = 'runtime_shadow'

    try:
        registrar_anti_pattern(erro_classificado)
    except Exception:
        pass

    # Registra como transicao Markov de penalidade
    # Isso permite que o MCR Decisor aprenda "nao use X neste contexto"
    _registrar_penalidade_markov(api_problematica, erro_msg)

    print('[ShadowCanary] Aprendizado por erro: "%s" penalizado no KG' % api_problematica)
    return api_problematica


def _registrar_penalidade_markov(api: str, erro: str):
    """Registra uma penalidade Markov no KG para uma API que falhou.
    
    Cria/atualiza um arquivo de penalidades que o MCRDecisor pode consultar.
    """
    penalidades_path = KG_DIR / 'shadow_penalidades.json'
    penalidades = {}
    if penalidades_path.exists():
        try:
            with open(penalidades_path, 'r', encoding='utf-8') as f:
                penalidades = json.load(f)
        except Exception:
            pass

    if api not in penalidades:
        penalidades[api] = {
            'ocorrencias': 0,
            'ultimo_erro': '',
            'timestamp': '',
        }

    penalidades[api]['ocorrencias'] += 1
    penalidades[api]['ultimo_erro'] = erro[:200]
    penalidades[api]['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')

    try:
        KG_DIR.mkdir(parents=True, exist_ok=True)
        with open(penalidades_path, 'w', encoding='utf-8') as f:
            json.dump(penalidades, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def consultar_penalidades(api: str = '') -> Dict:
    """Retorna penalidades registradas para uma API ou todas.
    
    Usado pelo MCRDecisor para verificar se uma API e confiavel.
    
    Args:
        api: nome da API (vazio = retorna todas)
    
    Returns:
        dict com penalidades
    """
    penalidades_path = KG_DIR / 'shadow_penalidades.json'
    if not penalidades_path.exists():
        return {}
    try:
        with open(penalidades_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        if api:
            return dados.get(api, {})
        return dados
    except Exception:
        return {}
