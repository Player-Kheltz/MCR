"""mcr.golden_templates — Templates Lua parametrizados para geracao instantanea.
Substitui variaveis como {{NPC_NAME}} por valores fornecidos.
Zero LLM, zero segundos. Todos os templates sao Canary-canonicos."""
import re
from typing import Dict, List
from mcr.paths import CANARY_NPC_DIR, CANARY_MONSTER_DIR
from mcr.encoding import write_file

# ─── Papeis que podem ser gerados via template (Tier 1) ──────
ROLE_TEMPLATE_MAP = {
    "vendedor", "guarda", "ferreiro", "padeiro", "taverneiro",
    "tecelao", "cavaleiro", "campones", "mendigo", "mercador",
    "comerciante", "vendedora", "guarda costas", "soldado",
    "artesao", "carpinteiro", "cocheiro", "mensageiro",
}


def is_template_role(role: str) -> bool:
    """True se o papel pode ser gerado via template (Tier 1)."""
    if not role:
        return False
    role_lower = role.lower().strip()
    if role_lower in ROLE_TEMPLATE_MAP:
        return True
    for r in ROLE_TEMPLATE_MAP:
        if r in role_lower:
            return True
    return False


# ─── Template de NPC (Canary canonico) ────────────────────────
_TEMPLATE_NPC_CANARY = """local internalNpcName = "{{NPC_NAME}}"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {}

npcConfig.name = internalNpcName
npcConfig.description = internalNpcName

npcConfig.health = {{HEALTH}}
npcConfig.maxHealth = {{HEALTH}}
npcConfig.walkInterval = 2000
npcConfig.walkRadius = 2

npcConfig.outfit = {
    lookType = {{LOOKTYPE}},
    lookHead = 0,
    lookBody = 0,
    lookLegs = 0,
    lookFeet = 0,
    lookAddons = 0,
}

npcConfig.flags = {
    floorchange = false,
}
{{SHOP_SECTION}}
local keywordHandler = KeywordHandler:new()
keywordHandler:addKeyword({"oi"}, StdModule.say, {npc = npcType, text = "{{GREETING}}"})
keywordHandler:addKeyword({"job"}, StdModule.say, {npc = npcType, text = "{{JOB_DESC}}"})

npcType:register(npcConfig)
"""


def gerar_npc_canary(params: Dict) -> str:
    """Gera script Lua de NPC canônico Canary a partir de parametros.
    
    Args:
        params: dict com keys:
            name (obrigatorio), health (default 100), looktype (default 128),
            greeting (default "Ola!"), job_desc (default "..."),
            shop_items (opcional, lista de dicts com name, clientId, buy, sell)
    
    Returns:
        string com o codigo Lua completo.
    """
    nome = params.get('name', 'NPC')
    health = params.get('health', 100)
    looktype = params.get('looktype', 128)
    greeting = params.get('greeting', 'Ola, como posso ajudar?')
    job_desc = params.get('job_desc', 'Trabalho por aqui.')

    # Shop: condicional — so aparece se houver itens
    shop_items = params.get('shop_items', [])
    if shop_items:
        linhas = []
        for item in shop_items:
            nome_item = item.get('name', 'item')
            client_id = item.get('clientId', 100)
            buy = item.get('buy', 0)
            sell = item.get('sell', 0)
            partes = ['    { itemName = "%s", clientId = %d' % (nome_item, client_id)]
            if buy:
                partes.append('buy = %d' % buy)
            if sell:
                partes.append('sell = %d' % sell)
            linhas.append(', '.join(partes) + ' },')
        shop_block = '\nnpcConfig.shop = {\n' + '\n'.join(linhas) + '\n}\n'
    else:
        shop_block = ''

    codigo = _TEMPLATE_NPC_CANARY
    codigo = codigo.replace('{{NPC_NAME}}', nome)
    codigo = codigo.replace('{{HEALTH}}', str(health))
    codigo = codigo.replace('{{LOOKTYPE}}', str(looktype))
    codigo = codigo.replace('{{GREETING}}', greeting)
    codigo = codigo.replace('{{JOB_DESC}}', job_desc)
    codigo = codigo.replace('{{SHOP_SECTION}}', shop_block)

    return codigo


# ─── Template de Monstro (Canary canonico) ────────────────────
_TEMPLATE_MONSTER_CANARY = """local mType = Game.createMonsterType("{{MONSTER_NAME}}")
local monster = {}

monster.name = "{{MONSTER_NAME}}"
monster.description = "{{DESCRIPTION}}"
monster.experience = {{EXPERIENCE}}
monster.health = {{HEALTH}}
monster.maxHealth = {{HEALTH}}
monster.speed = {{SPEED}}
monster.race = "{{RACE}}"

monster.outfit = {
    lookType = {{LOOKTYPE}},
}

monster.flags = {
    attackable = true,
    hostile = true,
    convinceable = false,
    pushable = false,
    rewardBoss = false,
    staticAttackChance = 90,
    targetDistance = 1,
}

monster.loot = {
{{DROP_ITEMS}}
}

monster.attacks = {
    {name = "melee", interval = 2000, chance = 100},
}

mType:register(monster)
"""


def gerar_monstro_parametrizado(params: Dict) -> str:
    """Gera script Lua de monstro Canary a partir de parametros."""
    nome = params.get('name', 'Monster')
    health = params.get('health', 500)
    exp = params.get('experience', 1000)
    speed = params.get('speed', 200)
    looktype = params.get('looktype', 100)
    desc = params.get('description', 'Um monstro perigoso.')
    race = params.get('race', 'blood')

    drop_items = params.get('drop_items', [])
    if drop_items:
        linhas = []
        for item in drop_items:
            item_id = item.get('id', 2160)
            chance = item.get('chance', 100000)
            max_count = item.get('maxCount', 1)
            linhas.append('    { id = %d, chance = %d, maxCount = %d },' % (item_id, chance, max_count))
        drop_str = '\n'.join(linhas)
    else:
        drop_str = '    -- { id = 2160, chance = 100000, maxCount = 1 }'

    codigo = _TEMPLATE_MONSTER_CANARY
    codigo = codigo.replace('{{MONSTER_NAME}}', nome)
    codigo = codigo.replace('{{DESCRIPTION}}', desc)
    codigo = codigo.replace('{{HEALTH}}', str(health))
    codigo = codigo.replace('{{EXPERIENCE}}', str(exp))
    codigo = codigo.replace('{{SPEED}}', str(speed))
    codigo = codigo.replace('{{LOOKTYPE}}', str(looktype))
    codigo = codigo.replace('{{RACE}}', race)
    codigo = codigo.replace('{{DROP_ITEMS}}', drop_str)

    return codigo


# ─── Funcoes de salvamento (compatibilidade) ─────────────────

def salvar_npc_parametrizado(params: Dict) -> str:
    """Gera e salva um NPC no disco usando template Canary. Retorna caminho."""
    codigo = gerar_npc_canary(params)
    nome = params.get('name', 'npc').lower().replace(' ', '_')
    nome_arquivo = re.sub(r'[^a-z0-9_]', '', nome) + '.lua'
    destino = CANARY_NPC_DIR / nome_arquivo
    write_file(destino, codigo, language='lua')
    return '[Template] NPC %s salvo em: %s' % (nome_arquivo, destino)


def salvar_monstro_parametrizado(params: Dict) -> str:
    """Gera e salva um Monstro no disco. Retorna caminho."""
    codigo = gerar_monstro_parametrizado(params)
    nome = params.get('name', 'monster').lower().replace(' ', '_')
    nome_arquivo = re.sub(r'[^a-z0-9_]', '', nome) + '.lua'
    destino = CANARY_MONSTER_DIR / nome_arquivo
    write_file(destino, codigo, language='lua')
    return '[Template] Monstro %s salvo em: %s' % (nome_arquivo, destino)
