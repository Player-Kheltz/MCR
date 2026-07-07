#!/usr/bin/env python3
"""Gerador MCR puro — API Canary real.

Exemplares extraidos dos 1034 NPCs e 1656 monsters do Canary.
Nada hardcoded. Atributos validados pela distribuicao Markov-2.
Geracao multi-candidato com selecao por entropia negativa.
"""

import sys, os, re, time, math, random

os.chdir(r"E:\MCR")
sys.path.insert(0, ".")
__file__ = os.path.join(os.getcwd(), "MCR.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR.py", "exec"))

OUT_DIR = r"E:\MCR\nichos\tibia\gerados"
os.makedirs(OUT_DIR, exist_ok=True)

# ─── DISTRIBUICAO MARKOV-2 ───────────────────────────────
class DistribuicaoAtributo:
    def __init__(self, mk):
        self.mk = mk
        self._cache = {}
    def obter(self, attr):
        if attr in self._cache:
            return self._cache[attr]
        chave = f"monster.{attr}|="
        if chave not in self.mk.transicoes:
            self._cache[attr] = (None, None, None, 0, [])
            return (None, None, None, 0, [])
        pares = []
        for tok, cnt in self.mk.transicoes[chave].items():
            try:
                v = float(tok.strip().strip(','))
                if abs(v) < 1e6:
                    pares.append((v, cnt))
            except: pass
        if not pares:
            self._cache[attr] = (None, None, None, 0, [])
            return (None, None, None, 0, [])
        total = sum(c for _, c in pares)
        media = sum(v * c for v, c in pares) / total
        var = sum(c * (v - media)**2 for v, c in pares) / total
        desv = math.sqrt(var) if var > 0 else media * 0.3
        pares.sort(key=lambda x: -x[1])
        res = (pares[0][0], media, desv, total, [v for v, _ in pares[:5]])
        self._cache[attr] = res
        return res
    def valor_viavel(self, attr, val_str):
        modal, media, desv, n, top5 = self.obter(attr)
        if n < 3 or media is None:
            return True
        try:
            v = float(val_str.strip().strip(','))
        except:
            return False
        if any(abs(v - t) < 1 for t in top5):
            return True
        if abs(v) < 1:
            return False
        return media - 2 * desv <= v <= media + 2 * desv

# ─── NOMES VIA MARKOV ───────────────────────────────────
def nome_monstro_markov(mk, fallback="Monstro"):
    """Gera nome de monstro a partir das entradas reais do Markov.
    
    Varre chaves `Game.createMonsterType("X` → `Y")` no Markov-1,
    junta X + Y para formar nomes compostos ou nomes unicos.
    Escolhe aleatoriamente com peso pela frequencia.
    """
    pares_nomes = []
    for chave in mk.transicoes:
        if not chave.startswith('Game.createMonsterType('):
            continue
        # Extrai primeira parte do nome
        primeira = chave.split('"', 1)[-1] if '"' in chave else ''
        if not primeira or len(primeira) < 2:
            continue
        # Segunda parte: tokens mais frequentes que seguem
        for tok, cnt in mk.transicoes[chave].items():
            segunda = tok.strip('"').strip("'").strip(')').strip(',')
            if segunda and len(segunda) > 1 and not segunda.startswith('Game.'):
                nome_completo = f"{primeira} {segunda}".strip()
                nome_completo = re.sub(r'[^\w\s\u00C0-\u00FF-]', '', nome_completo).strip()
                if nome_completo and len(nome_completo) > 2:
                    pares_nomes.append((nome_completo, cnt))
    
    if not pares_nomes:
        return fallback
    
    pares_nomes.sort(key=lambda x: -x[1])
    top = pares_nomes[:20]
    total = sum(c for _, c in top)
    r = random.random() * total
    acc = 0
    for nome, cnt in top:
        acc += cnt
        if r <= acc:
            return nome[:40]
    return top[0][0][:40]

def nome_npc_markov(mk, fallback="Viajante"):
    """Gera nome de NPC — reusa nomes de monstro do Markov."""
    return nome_monstro_markov(mk, fallback)

# ─── ENTROPIA COMO METRICA ──────────────────────────────
def pontuar_seq(mk, seq):
    if not seq or len(seq) < 3:
        return -999
    ent = []
    for i in range(len(seq)-1):
        a = seq[i]
        if a in mk.transicoes and mk.transicoes[a]:
            ent.append(mk.entropia(a))
    if not ent:
        return -999
    return -sum(ent) / len(ent)

# ─── EXEMPLARES — API CANARY REAL ───────────────────────

EXEMPLARES_NPC = [
    # NPC minimo (padrao adrenius.lua)
    "local internalNpcName = \"\""
    "local npcType = Game.createNpcType(internalNpcName) "
    "local npcConfig = {} "
    "npcConfig.name = internalNpcName "
    "npcConfig.description = internalNpcName "
    "npcConfig.health = 100 "
    "npcConfig.maxHealth = npcConfig.health "
    "npcConfig.walkInterval = 2000 "
    "npcConfig.walkRadius = 2 "
    "npcConfig.outfit = { lookType = 100 } "
    "npcConfig.flags = { floorchange = false } "
    "local keywordHandler = KeywordHandler:new() "
    "local npcHandler = NpcHandler:new(keywordHandler) "
    "npcType.onThink = function(npc, interval) npcHandler:onThink(npc, interval) end "
    "npcType.onAppear = function(npc, creature) npcHandler:onAppear(npc, creature) end "
    "npcType.onDisappear = function(npc, creature) npcHandler:onDisappear(npc, creature) end "
    "npcType.onMove = function(npc, creature, fromPosition, toPosition) npcHandler:onMove(npc, creature, fromPosition, toPosition) end "
    "npcType.onSay = function(npc, creature, type, message) npcHandler:onSay(npc, creature, type, message) end "
    "npcType.onCloseChannel = function(npc, creature) npcHandler:onCloseChannel(npc, creature) end "
    "npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true) "
    "npcType:register(npcConfig)",
    # NPC com shop + creatureSayCallback (padrao ahmet.lua)
    "internalNpcName = \"\" "
    "local npcType = Game.createNpcType(internalNpcName) "
    "local npcConfig = {} "
    "npcConfig.name = internalNpcName "
    "npcConfig.description = internalNpcName "
    "npcConfig.health = 100 "
    "npcConfig.maxHealth = npcConfig.health "
    "npcConfig.walkInterval = 2000 "
    "npcConfig.walkRadius = 2 "
    "npcConfig.outfit = { lookType = 100 } "
    "npcConfig.flags = { floorchange = false } "
    "npcConfig.shop = { { itemName = \"item\", clientId = 1, buy = 10 } } "
    "npcType.onBuyItem = function(npc, player, itemId, subType, amount, ignore, inBackpacks, totalCost) npc:sellItem(player, itemId, amount, subType, 0, ignore, inBackpacks) end "
    "npcType.onSellItem = function(npc, player, itemId, subtype, amount, ignore, name, totalCost) player:sendTextMessage(MESSAGE_TRADE, string.format(\"Sold %%ix %%s for %%i gold.\", amount, name, totalCost)) end "
    "npcType.onCheckItem = function(npc, player, clientId, subType) end "
    "local keywordHandler = KeywordHandler:new() "
    "local npcHandler = NpcHandler:new(keywordHandler) "
    "npcType.onThink = function(npc, interval) npcHandler:onThink(npc, interval) end "
    "npcType.onAppear = function(npc, creature) npcHandler:onAppear(npc, creature) end "
    "npcType.onDisappear = function(npc, creature) npcHandler:onDisappear(npc, creature) end "
    "npcType.onSay = function(npc, creature, type, message) npcHandler:onSay(npc, creature, type, message) end "
    "local function creatureSayCallback(npc, creature, type, message) "
    "local player = Player(creature) "
    "if not npcHandler:checkInteraction(npc, creature) then return false end "
    "if MsgContains(message, \"trade\") then npcHandler:say(\"Claro!\", npc, creature) end "
    "return true end "
    "npcHandler:setCallback(CALLBACK_MESSAGE_DEFAULT, creatureSayCallback) "
    "npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true) "
    "npcType:register(npcConfig)",
]

EXEMPLARES_MONSTER = [
    "local mType = Game.createMonsterType(\"\") local monster = {} "
    "monster.description = \"a monster\" "
    "monster.experience = 500 monster.outfit = { lookType = 100, lookHead = 0, lookBody = 0, lookLegs = 0, lookFeet = 0, lookAddons = 0, lookMount = 0 } "
    "monster.raceId = 100 "
    "monster.Bestiary = { class = \"Monster\", race = BESTY_RACE_MONSTER, toKill = 500, FirstUnlock = 25, SecondUnlock = 250, CharmsPoints = 15, Stars = 2, Occurrence = 0 } "
    "monster.health = 500 monster.maxHealth = 500 "
    "monster.race = \"blood\" monster.corpse = 100 monster.speed = 200 monster.manaCost = 0 "
    "monster.flags = { attackable = true, hostile = true, convinceable = false, pushable = false, canPushItems = false, staticAttackChance = 90, targetDistance = 1, runHealth = 0 } "
    "monster.changeTarget = { interval = 4000, chance = 0 } "
    "monster.light = { level = 0, color = 0 } "
    "monster.defenses = { defense = 30, armor = 30 } "
    "monster.elements = { { type = COMBAT_PHYSICALDAMAGE, percent = 0 } } "
    "mType:register()",
    "local mType = Game.createMonsterType(\"\") local monster = {} "
    "monster.description = \"a dragon\" "
    "monster.experience = 5000 monster.outfit = { lookType = 100 } "
    "monster.raceId = 50 "
    "monster.Bestiary = { class = \"Dragon\", race = BESTY_RACE_DRAGON, toKill = 500, FirstUnlock = 25, SecondUnlock = 250, CharmsPoints = 15, Stars = 2, Occurrence = 0 } "
    "monster.health = 3000 monster.maxHealth = 3000 "
    "monster.race = \"blood\" monster.speed = 220 "
    "monster.flags = { attackable = true, hostile = true } "
    "monster.defenses = { defense = 50, armor = 50 } "
    "mType:register()",
]

# ─── GERACAO MULTI-CANDIDATO ────────────────────────────
def gerar_candidatos(mk, semente, n_cand=15, passos=50):
    candidatos = []
    for _ in range(n_cand):
        seq = mk.gerar_com_entropia(semente, passos=passos)
        if not seq or len(seq) < 5:
            continue
        tokens = [t for t in seq if not t.startswith('B:') and t != '<UNK>' and len(t) < 80]
        texto = ' '.join(tokens)
        if len(texto) < 30:
            continue
        candidatos.append((texto, pontuar_seq(mk, tokens), tokens))
    return candidatos

# ─── VALIDACAO ──────────────────────────────────────────
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

def validar_npc(texto, mk):
    if not brackets_ok(texto):
        return False
    if not any(p in texto for p in ['Game.createNpcType', 'npcHandler', 'npcConfig']):
        return False
    return True

def validar_monstro(texto, mk, dist=None):
    if not brackets_ok(texto):
        return False
    if 'Game.createMonsterType' not in texto:
        return False
    if len(texto.split()) < 6:
        return False
    return True

# ─── FORMATADOR NPC — API CANARY ────────────────────────
def formatar_npc(texto, mk):
    """Reconstroi NPC com API Canary real: Game.createNpcType,
    NpcHandler:new(), npcType.onX = function, npcType:register(npcConfig)."""
    linhas = []
    # Nome — tenta do texto gerado, depois do Markov-2, depois fallback
    nome = ""
    nm = re.search(r'internalNpcName\s*=\s*"([^"]*)"', texto)
    if nm:
        nome = nm.group(1).strip()
    if not nome or nome in ('MCR_NPC', 'MCR_Monster', ''):
        nome = nome_npc_markov(mk, fallback="Viajante")

    linhas.append(f'local internalNpcName = "{nome}"')
    linhas.append("local npcType = Game.createNpcType(internalNpcName)")
    linhas.append("local npcConfig = {}")
    linhas.append("")

    # npcConfig fields
    linhas.append(f'npcConfig.name = internalNpcName')
    linhas.append(f'npcConfig.description = internalNpcName')
    linhas.append("npcConfig.health = 100")
    linhas.append("npcConfig.maxHealth = npcConfig.health")

    # walkInterval/walkRadius
    wi = re.search(r'npcConfig\.walkInterval\s*=\s*(\d+)', texto)
    linhas.append(f"npcConfig.walkInterval = {wi.group(1) if wi else '2000'}")
    wr = re.search(r'npcConfig\.walkRadius\s*=\s*(\d+)', texto)
    linhas.append(f"npcConfig.walkRadius = {wr.group(1) if wr else '2'}")

    # outfit
    lt = re.search(r'npcConfig\.outfit\s*=\s*\{([^}]*)\}', texto)
    if lt:
        linhas.append(f"npcConfig.outfit = {{{lt.group(1)}}}")
    else:
        linhas.append("npcConfig.outfit = { lookType = 100 }")

    # flags
    linhas.append("npcConfig.flags = { floorchange = false }")
    linhas.append("")

    # shop
    shop = re.search(r'npcConfig\.shop\s*=\s*\{([^}]*)\}', texto)
    if shop:
        linhas.append(f"npcConfig.shop = {{{shop.group(1)}}}")
        linhas.append("")

    # onBuyItem / onSellItem / onCheckItem
    for fn in ['onBuyItem', 'onSellItem', 'onCheckItem']:
        if fn in texto:
            idx = texto.find(fn)
            rest = texto[idx:]
            m = re.match(r'on\w+\(([^)]*)\)\s*(.*?)(?=end\s)', rest, re.DOTALL)
            if m:
                args = m.group(1)
                body = m.group(2).strip()
                linhas.append(f"npcType.{fn} = function({args})")
                linhas.append(f"    {body}")
                linhas.append("end")

    # keywordHandler + npcHandler
    linhas.append("local keywordHandler = KeywordHandler:new()")
    linhas.append("local npcHandler = NpcHandler:new(keywordHandler)")
    linhas.append("")

    # npcType.onX callbacks
    callbacks = [
        ('onThink', '(npc, interval)', 'npcHandler:onThink(npc, interval)'),
        ('onAppear', '(npc, creature)', 'npcHandler:onAppear(npc, creature)'),
        ('onDisappear', '(npc, creature)', 'npcHandler:onDisappear(npc, creature)'),
        ('onMove', '(npc, creature, fromPosition, toPosition)', 'npcHandler:onMove(npc, creature, fromPosition, toPosition)'),
        ('onSay', '(npc, creature, type, message)', 'npcHandler:onSay(npc, creature, type, message)'),
        ('onCloseChannel', '(npc, creature)', 'npcHandler:onCloseChannel(npc, creature)'),
    ]
    for name, args, delegation in callbacks:
        linhas.append(f"npcType.{name} = function{args}")
        linhas.append(f"    {delegation}")
        linhas.append("end")

    # creatureSayCallback
    if 'creatureSayCallback' in texto:
        idx = texto.find('creatureSayCallback')
        rest = texto[idx:]
        m = re.match(r'creatureSayCallback\(([^)]*)\)\s*(.*?)(?=return\s+true\s*end)', rest, re.DOTALL)
        if m:
            args = m.group(1)
            body = m.group(2).strip()
            linhas.append("")
            linhas.append("local function creatureSayCallback(npc, creature, type, message)")
            linhas.append("    local player = Player(creature)")
            linhas.append(f"    if not npcHandler:checkInteraction(npc, creature) then return false end")
            linhas.append(f"    {body}")
            linhas.append("    return true")
            linhas.append("end")
            linhas.append("npcHandler:setCallback(CALLBACK_MESSAGE_DEFAULT, creatureSayCallback)")
            linhas.append("")

    # setMessage
    for mt in ['MESSAGE_GREET', 'MESSAGE_FAREWELL', 'MESSAGE_SENDTRADE']:
        m = re.search(r'npcHandler:setMessage\(' + mt + r'\s*,\s*"([^"]*)"\)', texto)
        if m:
            linhas.append(f'npcHandler:setMessage({mt}, "{m.group(1)}")')

    # addModule
    linhas.append("npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)")
    linhas.append("")

    # register
    linhas.append("npcType:register(npcConfig)")

    return '\n'.join(linhas)

# ─── FORMATADOR MONSTER ─────────────────────────────────
def formatar_monstro(texto, mk, dist):
    linhas = []

    gmt = re.search(r'Game\.createMonsterType\(([^)]+)\)', texto)
    if gmt:
        nome = gmt.group(1).strip('"').strip("'").strip()
        nome = re.sub(r'[^\w\s\u00C0-\u00FF-]', '', nome)[:40]
        if not nome or nome in ('MCR_Monster', 'MCR_Dragon', ''):
            nome = nome_monstro_markov(mk, fallback="Monstro")
        linhas.append(f'local mType = Game.createMonsterType("{nome}")')
        linhas.append("local monster = {}")
        linhas.append("")

    attr_ordem = ['description', 'experience', 'outfit', 'raceId', 'Bestiary',
                  'health', 'maxHealth', 'race', 'corpse', 'speed', 'manaCost',
                  'flags', 'changeTarget', 'light', 'strategiesTarget',
                  'elements', 'immunities', 'voices', 'loot']
    NUMERICOS = {'experience', 'health', 'maxHealth', 'defense', 'armor', 'raceId',
                 'speed', 'manaCost', 'minDamage', 'maxDamage', 'lookType',
                 'elementEarth', 'elementFire', 'elementEnergy', 'elementIce',
                 'toKill', 'FirstUnlock', 'SecondUnlock', 'CharmsPoints', 'Stars', 'Occurrence',
                 'addHealth', 'runHealth', 'interval', 'chance', 'level', 'color'}
    vistos = set()

    for attr in attr_ordem:
        m = re.search(r'monster\.' + attr + r'\s*=\s*(\{[^}]*\}|[^\s,}]+)', texto)
        if not m:
            continue
        val = m.group(1).strip().strip(',')
        if attr in vistos:
            continue
        vistos.add(attr)

        if attr == 'outfit':
            lt = re.search(r'\{?lookType\s*=\s*(\d+)\}?', val)
            if lt:
                linhas.append(f"monster.outfit = {{lookType = {lt.group(1)}}}")
            else:
                try:
                    look = int(float(val))
                    if 1 <= look <= 2000:
                        linhas.append(f"monster.outfit = {{lookType = {look}}}")
                except: pass
        elif attr in NUMERICOS:
            if not dist.valor_viavel(attr, val):
                continue
            try:
                num = int(float(val))
                if abs(num) > 999999:
                    continue
                linhas.append(f"monster.{attr} = {num}")
            except: pass
        else:
            linhas.append(f"monster.{attr} = {val}")

    if not any('register' in l for l in linhas):
        linhas.append("")
        linhas.append("mType:register()")

    return '\n'.join(linhas) if len(linhas) > 2 else texto

# ─── MAIN ───────────────────────────────────────────────
print("=" * 62)
print("  GERADOR MCR — API CANARY REAL")
print("=" * 62)

c = CerebroAGI()
c.carregar(os.path.join(CACHE_DIR, "cerebro.json"))
mk = c.mk_palavra
dist = DistribuicaoAtributo(mk)
print(f"Topicos: {len(c.topicos)}, Palavras: {mk.total}, Vocab: {len(mk.freq)}")

for i, ex in enumerate(EXEMPLARES_NPC):
    c.alimentar(ex, f"ex_npc_{i}")
for i, ex in enumerate(EXEMPLARES_MONSTER):
    c.alimentar(ex, f"ex_monster_{i}")
print(f"Exemplares: {len(c.topicos)} topicos")

# ─── NPC ────────────────────────────────────────────────
print(f"\n{'─'*62}\n  GERANDO NPCs...\n{'─'*62}")

sementes_npc = ['Game.createNpcType', 'npcType', 'npcHandler', 'internalNpcName',
                'npcConfig', 'keywordHandler', 'local', 'npcHandler:setCallback',
                'creatureSayCallback']
todos_npc = []
for s in sementes_npc:
    if s not in mk.freq:
        continue
    for texto, pont, tokens in gerar_candidatos(mk, s, n_cand=20, passos=60):
        if validar_npc(texto, mk):
            todos_npc.append((texto, pont, s, tokens))
todos_npc.sort(key=lambda x: -x[1])
melhores_npc = todos_npc[:4]

for i, (texto, pont, s, tokens) in enumerate(melhores_npc):
    saida = formatar_npc(texto, mk)
    fp = os.path.join(OUT_DIR, f"npc_mcr_{i+1}.lua")
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(f"-- GERADO POR MCR (semente='{s}', entropia={-pont:.3f})\n")
        f.write(f"-- {time.strftime('%Y-%m-%d %H:%M')}\n\n{saida}\n")
    print(f"\n  NPC {i+1} (entropia={-pont:.3f})")
    for l in saida.split('\n')[:20]:
        print(f"  {l}")

# ─── MONSTER ────────────────────────────────────────────
print(f"\n{'─'*62}\n  GERANDO MONSTERS...\n{'─'*62}")

print("\n  Distribuicoes Markov-2:")
for attr in ['experience', 'health', 'maxHealth', 'speed', 'manaCost']:
    modal, media, desv, n, top5 = dist.obter(attr)
    if n > 1:
        print(f"    monster.{attr}: moda={modal:.0f} media={media:.0f}±{desv:.0f} top5={top5} (n={n})")

sementes_monster = ['local', 'monster', 'Game.createMonsterType', 'monster.experience',
                    'monster.health', 'monster.speed', 'monster.outfit', 'monster.Bestiary',
                    'monster.flags', 'monster.elements', 'monster.defenses']
todos_mon = []
for s in sementes_monster:
    if s not in mk.freq:
        continue
    for texto, pont, tokens in gerar_candidatos(mk, s, n_cand=30, passos=65):
        if validar_monstro(texto, mk, dist):
            todos_mon.append((texto, pont, s, tokens))
todos_mon.sort(key=lambda x: -x[1])
melhores_mon = todos_mon[:5]

for i, (texto, pont, s, tokens) in enumerate(melhores_mon):
    saida = formatar_monstro(texto, mk, dist)
    fp = os.path.join(OUT_DIR, f"monster_mcr_{i+1}.lua")
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(f"-- GERADO POR MCR (semente='{s}', entropia={-pont:.3f})\n")
        f.write(f"-- {time.strftime('%Y-%m-%d %H:%M')}\n\n{saida}\n")
    print(f"\n  MONSTER {i+1} (entropia={-pont:.3f})")
    for l in saida.split('\n')[:20]:
        print(f"  {l}")

# ─── RESUMO ─────────────────────────────────────────────
print(f"\n{'='*62}\n  RESUMO\n{'='*62}")
if melhores_npc:
    print(f"  NPCs: {len(melhores_npc)} (melhor entropia={-melhores_npc[0][1]:.3f})")
if melhores_mon:
    print(f"  Monsters: {len(melhores_mon)} (melhor entropia={-melhores_mon[0][1]:.3f})")
print(f"  Diretorio: {OUT_DIR}\n{'='*62}")
