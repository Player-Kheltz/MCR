#!/usr/bin/env python3
"""Gera NPC e Monster Lua — exemplares + geracao inteligente + pos-processamento."""

import sys, os, re, time

_BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

os.chdir(_BASE)
sys.path.insert(0, ".")
__file__ = os.path.join(os.getcwd(), "MCR.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR.py", "exec"))

# ─── VALIDACAO COMPARTILHADA ──────────────────────────────

BRACKETS = {'{':'}', '[':']', '(':')'}
BRACKETS_REV = {v:k for k,v in BRACKETS.items()}

def brackets_ok(texto):
    pilha = []
    for ch in texto:
        if ch in BRACKETS:
            pilha.append(ch)
        elif ch in BRACKETS_REV:
            if not pilha or pilha[-1] != BRACKETS_REV[ch]:
                return False
            pilha.pop()
    return not pilha

def limpar_tokens(seq):
    """Remove byte lixo e tokens de controle."""
    return [t for t in seq if not t.startswith('B:') and t != '<UNK>'
            and not t.startswith('--') and len(t) < 80]

# ─── EXEMPLARES ────────────────────────────────────────────

EXEMPLARES_NPC = [
    # NPC completo com keywordHandler + shop + storage
    """local keywordHandler = KeywordHandler()
local npcHandler = Npc()
local talkState = {}

function onCreatureAppear(creature) npcHandler:onCreatureAppear(creature) end
function onCreatureDisappear(creature) npcHandler:onCreatureDisappear(creature) end
function onCreatureSay(creature, msgType, message) npcHandler:onCreatureSay(creature, msgType, message) end
function onThink() npcHandler:onThink() end

npcHandler:setMessage(MESSAGE_GREET, "Ola |PLAYERNAME|!")
npcHandler:setMessage(MESSAGE_FAREWELL, "Ate logo!")
npcHandler:setMessage(MESSAGE_SENDTRADE, "O que deseja?")

npcHandler:addModule(FocusModule())
npcHandler:register()""",
    # NPC ferreiro com config e shop
    """local npc = Npc()
npcConfig = {
    name = "Ferreiro",
    greet = "Precisa de algo?",
    bye = "Volte sempre!"
}

function onSay(player, words, param)
    if words == "hi" then
        npc:sai("Ola, aventureiro!")
    elseif words == "trade" then
        npc:sai("Claro!")
        doPlayerOpenShop(player)
    end
    return true
end

npcHandler:setMessage(MESSAGE_GREET, "Ola!")
npcHandler:setMessage(MESSAGE_FAREWELL, "Tchau!")
npcHandler:register()""",
    # NPC com storage (missoes)
    """local npcHandler = Npc()

function creatureSayCallback(npc, creature, msgType, message)
    local player = creature:getPlayer()
    if not player then return true end

    if MsgContains(message, "missao") then
        local storage = player:getStorageValue(1000)
        if storage < 1 then
            npcHandler:say("Faca esta missao!", npc, creature)
            player:setStorageValue(1000, 1)
        else
            npcHandler:say("Ja completou!", npc, creature)
        end
    end
    return true
end

npcHandler:addModule(FocusModule())
npcHandler:register()""",
    # NPC shop
    """function onBuy(player)
    player:sendTextMessage(MESSAGE_INFO, "Obrigado pela compra!")
    return true
end

npcType.onSellItem = 23544

npcHandler:setMessage(MESSAGE_SENDTRADE, "O que deseja?")
npcHandler:register()""",
]

EXEMPLARES_MONSTER = [
    # Monster completo
    """local mType = Game.createMonsterType("Exemplo")
local monster = {}

monster.description = "um monstro exemplo"
monster.experience = 100
monster.outfit = {
    lookType = 100,
    lookHead = 0,
    lookBody = 0,
    lookLegs = 0,
    lookFeet = 0,
    lookAddons = 0,
    lookMount = 0,
}
monster.health = 500
monster.maxHealth = 500
monster.defense = 30
monster.armor = 30
monster.raceId = 100
monster.Bestiary = {
    class = "Example",
    race = BESTY_RACE_EXAMPLE,
    toKill = 500,
    FirstUnlock = 25,
    SecondUnlock = 250,
    CharmsPoints = 15,
    Stars = 2,
    Occurrence = 0,
}
monster.speed = 200
monster.addHealth = 0
monster.runHealth = 10
mType:register()""",
    # Monster completo 2
    """local mType = Game.createMonsterType("Dragon")
local monster = {}
monster.description = "a large dragon"
monster.experience = 5000
monster.outfit = { lookType = 100 }
monster.health = 3000
monster.maxHealth = 3000
monster.defense = 50
monster.armor = 50
monster.raceId = 50
monster.race = "dragon"
monster.speed = 200
monster.addHealth = 0
monster.runHealth = 10
monster.elementEarth = 100
monster.elementFire = 0
monster.elementIce = 200
mType:register()""",
    # Monster com elements e loot
    """local mType = Game.createMonsterType("Fire Elemental")
local monster = {}
monster.description = "a being of pure fire"
monster.experience = 800
monster.outfit = { lookType = 200 }
monster.health = 1500
monster.maxHealth = 1500
monster.defense = 20
monster.armor = 20
monster.elementEarth = 100
monster.elementFire = 0
monster.elementEnergy = 100
monster.elementIce = 200
monster.raceId = 200
mType:register()""",
]

# ─── GERADOR INTELIGENTE ──────────────────────────────────

def gerar_entity(c, sementes, exemplares, tipo, max_tentativas=30):
    """Gera NPC ou Monster alimentando exemplares + tentativas multiplas."""
    # Alimenta exemplares
    for i, ex in enumerate(exemplares):
        c.alimentar(ex, f"exemplar_{tipo}_{i}")

    resultados = []
    for semente in sementes:
        if semente not in c.mk_palavra.freq:
            continue
        for tentativa in range(max_tentativas):
            seq = c.mk_palavra.gerar_com_entropia(semente, passos=40)
            if not seq: continue
            tokens = limpar_tokens(seq)
            texto = " ".join(tokens)
            if len(texto) < 40: continue
            if not brackets_ok(texto): continue

            melhor = texto

            # Validacao especifica
            valido = False
            if tipo == 'monster' and ('monster.' in melhor or 'Game.createMonsterType' in melhor):
                valido = True
            elif tipo == 'npc' and any(p in melhor for p in ['npcHandler', 'npcConfig', 'onSay', 'creatureSayCallback', 'keywordHandler', 'FocusModule']):
                valido = True

            if valido:
                resultados.append((melhor, semente, tentativa+1))
                break

    return resultados

# ─── POS-PROCESSAMENTO ────────────────────────────────────

def formatar_npc(texto):
    """Estrutura NPC a partir de tokens Markov (espacados, sem \n)."""
    # Remove contaminacao de monster
    for p in ['Game.createMonsterType', 'BESTY_RACE', 'monster.', 'createMonster', 'mType']:
        texto = texto.replace(p, '')

    linhas = []

    # Headers
    if 'npcHandler' in texto or 'npcConfig' in texto or 'keywordHandler' in texto:
        if 'keywordHandler' in texto:
            linhas.append("local keywordHandler = KeywordHandler()")
        if 'talkState' in texto:
            linhas.append("local talkState = {}")
        linhas.append("local npcHandler = Npc()")
        linhas.append("")

    # Callbacks onCreature*
    for fn in ['onCreatureAppear', 'onCreatureDisappear', 'onCreatureSay', 'onThink']:
        if fn in texto:
            idx = texto.find(fn)
            # Pega argumentos ate o proximo )
            rest = texto[idx:]
            args_match = re.match(r'on\w+\(([^)]*)\)', rest)
            args = args_match.group(1) if args_match else 'creature'
            linhas.append(f"function {fn}({args}) npcHandler:onCreatureAppear({args.split(',')[0].strip()}) end")

    # npcConfig
    cfg_match = re.search(r'npcConfig\s*=\s*\{([^}]*)\}', texto)
    if cfg_match:
        linhas.append(f"npcConfig = {{{cfg_match.group(1)}}}")
        linhas.append("")

    # Callbacks principais
    for cb in ['creatureSayCallback', 'onSay', 'onGreet', 'onBuy']:
        if cb in texto:
            idx = texto.find(cb)
            rest = texto[idx:]
            args_match = re.match(r'creatureSayCallback\(([^)]*)\)', rest) or re.match(r'on\w+\(([^)]*)\)', rest)
            args = args_match.group(1) if args_match else 'npc, creature, msgType, message'
            # Corpo: tudo ate o proximo function/register/fim, removendo ends extras
            corpo_match = re.search(r'\)\s*(.*?)(?=function\s+|npcHandler:|$)', rest)
            corpo_raw = corpo_match.group(1).strip() if corpo_match else 'return true'
            # Remove ends extras do Markov
            corpo = re.sub(r'\bend\b', '', corpo_raw).strip()
            if corpo:
                linhas.append(f"function {cb}({args})")
                linhas.append(f"    {corpo}")
                linhas.append("end")
                linhas.append("")

    # setMessage
    for msg_type in ['MESSAGE_GREET', 'MESSAGE_FAREWELL', 'MESSAGE_SENDTRADE']:
        m = re.search(r'npcHandler:setMessage\(' + msg_type + r'\s*,\s*"([^"]*)"\)', texto)
        if m:
            linhas.append(f'npcHandler:setMessage({msg_type}, "{m.group(1)}")')

    # Finalizacao
    if 'FocusModule' in texto:
        linhas.append("npcHandler:addModule(FocusModule())")
    if not any('register' in l for l in linhas):
        linhas.append("npcHandler:register()")

    return "\n".join(linhas) if linhas else texto

ATTR_NUMERICOS = {'experience', 'health', 'maxHealth', 'defense', 'armor', 'raceId',
                   'speed', 'addHealth', 'runHealth', 'lookType',
                   'elementEarth', 'elementFire', 'elementEnergy', 'elementIce',
                   'toKill', 'FirstUnlock', 'SecondUnlock', 'CharmsPoints', 'Stars', 'Occurrence'}

def valor_numerico(val):
    """Extrai numero de uma string tipo '= 123' ou '= "texto"'."""
    val = val.strip()
    if val.startswith('='):
        val = val[1:].strip()
    val = val.strip(',')
    # Se for string, retorna None
    if val.startswith('"') or val.startswith("'"):
        return None
    # Se for chamada de funcao, retorna None
    if val.startswith('Game.') or val.startswith('function'):
        return None
    try:
        return int(float(val))
    except Exception:
        return None

def formatar_monstro(texto):
    """Estrutura monstro a partir de tokens Markov."""
    linhas = []

    # Procura Game.createMonsterType
    gmt = re.search(r'Game\.createMonsterType\(([^)]+)\)', texto)
    if gmt:
        nome_raw = gmt.group(1).strip('"').strip("'").strip()
        # Limpa nome — Markov pode concatenar
        nome = re.sub(r'[^\w\s\u00C0-\u00FF-]', '', nome_raw).strip()[:40]
        if not nome:
            nome = "MonstroGerado"
        linhas.append(f'local mType = Game.createMonsterType("{nome}")')
        linhas.append("local monster = {}")
        linhas.append("")

    # Procura atributos na ordem
    attr_ordem = ['description', 'experience', 'outfit', 'health', 'maxHealth',
                  'defense', 'armor', 'raceId', 'speed', 'race', 'addHealth', 'runHealth',
                  'elementEarth', 'elementFire', 'elementEnergy', 'elementIce',
                  'lookType']
    vistos = set()
    for attr in attr_ordem:
        # M = Markov pode concatenar: monster.experience=500 ou monster.experience=500,
        pattern = r'monster\.' + attr + r'\s*=\s*([^\s,}]+)'
        m = re.search(pattern, texto)
        if m:
            val = m.group(1).strip().strip(',')
            if attr in ATTR_NUMERICOS:
                num = valor_numerico(val)
                if num is not None and attr not in vistos:
                    vistos.add(attr)
                    linhas.append(f"monster.{attr} = {num}")
            else:
                if attr not in vistos:
                    vistos.add(attr)
                    linhas.append(f'monster.{attr} = {val}')

    if not any('register' in l for l in linhas):
        linhas.append("")
        linhas.append("mType:register()")

    return "\n".join(linhas) if linhas else texto

# ─── MAIN ──────────────────────────────────────────────────

print("=" * 60)
print("  GERADOR COMPLETO: NPC + MONSTER LUA")
print("  Base: 629 scripts + 1034 NPCs + 1656 monsters Canary")
print("=" * 60)

c = CerebroAGI()
c.carregar(os.path.join(CACHE_DIR, "cerebro.json"))
print(f"Topicos: {len(c.topicos)}, Palavras: {c.mk_palavra.total}\n")

# ─── NPC ──────────────────────────────────────────────────
print("─" * 60)
print("  GERANDO NPC...")
print("─" * 60)
sementes_npc = ['npcHandler', 'npcConfig', 'local', 'function', 'keywordHandler']
npcs = gerar_entity(c, sementes_npc, EXEMPLARES_NPC, 'npc', max_tentativas=25)

for i, (texto, semente, t) in enumerate(npcs):
    print(f"\n  NPC {i+1} (semente='{semente}', tentativa #{t})")
    print(f"  {'─'*40}")
    saida = formatar_npc(texto)
    for linha in saida.split('\n')[:20]:
        print(f"  {linha}")

# ─── MONSTER ──────────────────────────────────────────────
print(f"\n{'─'*60}")
print(f"  GERANDO MONSTER...")
print(f"{'─'*60}")
sementes_monster = ['local', 'monster', 'monster.description', 'monster.experience', 'monster.outfit']
monsters = gerar_entity(c, sementes_monster, EXEMPLARES_MONSTER, 'monster', max_tentativas=25)

for i, (texto, semente, t) in enumerate(monsters):
    print(f"\n  MONSTER {i+1} (semente='{semente}', tentativa #{t})")
    print(f"  {'─'*40}")
    saida = formatar_monstro(texto)
    for linha in saida.split('\n')[:20]:
        print(f"  {linha}")

# ─── SALVAR RESULTADOS ───────────────────────────────────
OUT_DIR = os.path.join(_BASE, "nichos", "tibia", "gerados")
os.makedirs(OUT_DIR, exist_ok=True)

for i, (texto, semente, t) in enumerate(npcs):
    saida = formatar_npc(texto)
    fp = os.path.join(OUT_DIR, f"npc_gerado_{i+1}.lua")
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(f"-- GERADO POR MCR (semente='{semente}', tentativa #{t})\n")
        f.write(f"-- {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(saida + "\n")
    print(f"  Salvo: {fp}")

for i, (texto, semente, t) in enumerate(monsters):
    saida = formatar_monstro(texto)
    fp = os.path.join(OUT_DIR, f"monster_gerado_{i+1}.lua")
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(f"-- GERADO POR MCR (semente='{semente}', tentativa #{t})\n")
        f.write(f"-- {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(saida + "\n")
    print(f"  Salvo: {fp}")

# ─── RESUMO ──────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  RESUMO")
print(f"{'='*60}")
print(f"  NPCs validos gerados: {len(npcs)} (salvos em {OUT_DIR})")
print(f"  Monsters validos: {len(monsters)} (salvos em {OUT_DIR})")
print(f"  Vocabulario total: {len(c.mk_palavra.freq)}")
print(f"{'='*60}")
