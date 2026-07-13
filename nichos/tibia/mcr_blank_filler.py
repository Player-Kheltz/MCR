#!/usr/bin/env python3
"""MCR BlankFiller v2 — NPC e Monster completos.

Template fixo (sintaxe Canary 100% valida) + MCR preenche valores
das distribuicoes reais de 1656 monstros e 1034 NPCs.
"""

import sys, os, re, time, math, random

_BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

os.chdir(_BASE)
sys.path.insert(0, ".")
__file__ = os.path.join(os.getcwd(), "MCR.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR.py", "exec"))

OUT_DIR = os.path.join(_BASE, "nichos", "tibia", "gerados")
os.makedirs(OUT_DIR, exist_ok=True)

c = CerebroAGI()
c.carregar(os.path.join(CACHE_DIR, "cerebro.json"))
mk = c.mk_palavra
print(f"Carregado: {mk.total} transicoes, {len(mk.freq)} vocab")

# ─── UTILITARIOS ─────────────────────────────────────────
def valor_mk2(chave):
    if chave not in mk.transicoes or not mk.transicoes[chave]:
        return None
    toks = sorted(mk.transicoes[chave].items(), key=lambda x: -x[1])
    total = sum(c for _, c in toks[:20])
    r = random.random() * total
    acc = 0
    for tok, cnt in toks[:20]:
        acc += cnt
        if r <= acc:
            return tok.strip().strip(',').strip('"').strip("'")
    return toks[0][0].strip().strip(',').strip('"').strip("'")

def valor_num_mk2(chave, min_v=1, max_v=999999, fallback=100):
    for _ in range(8):
        v = valor_mk2(chave)
        try:
            n = int(float(v))
            if min_v <= n < max_v:
                return n
        except Exception: pass
    return random.randint(min_v, max(max_v//4, 1))

def variedade(chave, n=5):
    res = []
    if chave in mk.transicoes:
        toks = sorted(mk.transicoes[chave].items(), key=lambda x: -x[1])
        for tok, _ in toks[:n*3]:
            v = tok.strip().strip(',').strip('"').strip("'")
            if v and v not in res:
                res.append(v)
                if len(res) >= n:
                    break
    return res

# ─── NOMES ───────────────────────────────────────────────
def nome_monstro_fn(fallback="Criatura"):
    pares = []
    for chave in mk.transicoes:
        if not chave.startswith('Game.createMonsterType('):
            continue
        partes = chave.split('"', 2)
        if len(partes) < 2:
            continue
        primeira = partes[1].strip()
        if not primeira or len(primeira) < 2:
            continue
        for tok, cnt in mk.transicoes[chave].items():
            segunda = tok.strip('"').strip("'").strip(')').strip(',').strip()
            if not segunda or len(segunda) <= 1:
                continue
            if 'Game.' in segunda or 'BESTY' in segunda or 'COMBAT' in segunda:
                continue
            nome = (primeira + ' ' + segunda).strip()
            nome = re.sub(r'[^\w\s\u00C0-\u00FF-]', '', nome).strip()
            if 3 < len(nome) <= 40:
                pares.append((nome, cnt))
    if not pares:
        return fallback
    pares.sort(key=lambda x: -x[1])
    top = pares[:30]
    total = sum(c for _, c in top)
    r = random.random() * total
    acc = 0
    for nome, cnt in top:
        acc += cnt
        if r <= acc:
            return nome
    return top[0][0]

def nome_npc_fn(fallback="Viajante"):
    return nome_monstro_fn(fallback)

# ─── ITENS LOOT ──────────────────────────────────────────
def itens_loot(n_min=1, n_max=5):
    ids = []
    if 'id|=' in mk.transicoes:
        for tok, cnt in mk.transicoes['id|='].items():
            try:
                ids.append((int(tok.strip().strip(',')), cnt))
            except Exception: pass
    ids.sort(key=lambda x: -x[1])
    if not ids:
        return []
    n = random.randint(n_min, min(n_max, len(ids)))
    itens = []
    for iid, cnt in ids[:n]:
        chance = min(100000, max(100, int(random.gauss(cnt*50, cnt*20))))
        maxc = random.choices([1,5,10,20,50,100], weights=[30,25,20,15,5,5])[0]
        itens.append(f"    {{id = {iid}, chance = {chance}, maxCount = {maxc}}}")
    return itens

# ─── ATAQUES ─────────────────────────────────────────────
def ataques(n_min=1, n_max=3):
    nomes = variedade('name|=', 8) or ['melee', 'combat', 'speed']
    n = random.randint(n_min, n_max)
    atqs, usados = [], []
    for _ in range(n):
        nome = random.choice([x for x in nomes if x not in usados] or nomes)
        usados.append(nome)
        dano = random.randint(5, 300)
        atqs.append(f'    {{name = "{nome}", interval = 2000, chance = 100, minDamage = 0, maxDamage = -{dano}}}')
    return atqs

# ─── VOZES ───────────────────────────────────────────────
def vozes(n_min=1, n_max=3):
    textos = variedade('text|=', 8)
    n = random.randint(n_min, n_max)
    vzs = []
    for _ in range(n):
        txt = random.choice(textos) if textos else "Ola!"
        vzs.append(f'    {{text = "{txt}", yell = {random.choice(["true","false"])}}}')
    return vzs

# ─── ELEMENTOS ──────────────────────────────────────────
def elementos():
    tipos = [
        'COMBAT_PHYSICALDAMAGE', 'COMBAT_ENERGYDAMAGE', 'COMBAT_EARTHDAMAGE',
        'COMBAT_FIREDAMAGE', 'COMBAT_ICEDAMAGE', 'COMBAT_DEATHDAMAGE', 'COMBAT_HOLYDAMAGE'
    ]
    elems = []
    var = random.choice(tipos)
    for t in tipos:
        p = 0
        if t == var:
            p = random.choice([-25, -10, 10, 25])
        elems.append(f'    {{type = {t}, percent = {p}}}')
    return elems

# ─── MONSTER TEMPLATE ────────────────────────────────────
MONSTER_TPL = """local mType = Game.createMonsterType("{NOME}")
local monster = {{}}

monster.description = "{DESC}"
monster.experience = {XP}
monster.outfit = {{
    lookType = {LOOK},
}}
monster.raceId = {RACEID}
monster.Bestiary = {{
    class = "{BCLASS}",
    race = BESTY_RACE_{BRACE},
    toKill = {TOKILL},
    FirstUnlock = {FUNLOCK},
    SecondUnlock = {SUNLOCK},
    CharmsPoints = {CPOINTS},
    Stars = {STARS},
    Occurrence = 0,
}}
monster.health = {HP}
monster.maxHealth = {HP}
monster.race = "{RACE}"
monster.corpse = {CORPSE}
monster.speed = {SPEED}
monster.manaCost = {MANA}

monster.changeTarget = {{
    interval = 4000,
    chance = 0,
}}
monster.strategiesTarget = {{
    nearest = 100,
}}
monster.flags = {{
    summonable = false,
    attackable = {ATKABLE},
    hostile = {HOSTILE},
    convinceable = false,
    pushable = {PUSHABLE},
    rewardBoss = false,
    illusionable = false,
    canPushItems = true,
    canPushCreatures = false,
    staticAttackChance = {SAC},
    targetDistance = {TDIST},
    runHealth = {RUNHP},
    healthHidden = false,
    isBlockable = false,
    canWalkOnEnergy = false,
    canWalkOnFire = false,
    canWalkOnPoison = false,
}}
monster.light = {{
    level = 0,
    color = 0,
}}

monster.voices = {{
    interval = 5000,
    chance = 10,
{VOCES}
}}

monster.loot = {{
{LOOT}
}}

monster.attacks = {{
{ATAQUES}
}}

monster.elements = {{
{ELEMS}
}}

monster.defenses = {{
    defense = {DEF},
    armor = {ARM},
}}

mType:register()"""

def gerar_monstro():
    nome = nome_monstro_fn()
    xp = valor_num_mk2('monster.experience|=', min_v=5, max_v=200000, fallback=100)
    hp = valor_num_mk2('monster.health|=', min_v=20, fallback=500)
    speed = valor_num_mk2('monster.speed|=', min_v=20, max_v=2000, fallback=150)
    look = valor_num_mk2('lookType|=', min_v=1, max_v=2000, fallback=100)
    mana = valor_num_mk2('manaCost|=', min_v=0, max_v=5000, fallback=0)
    raceid = random.randint(1, 1000)
    
    loot = ",\n".join(itens_loot(1, 4))
    atqs = ",\n".join(ataques(1, 2))
    vzs = ",\n".join(vozes(0, 2))
    elems = ",\n".join(elementos())
    
    return MONSTER_TPL.format(
        NOME=nome, DESC=f"um {nome.lower()}",
        XP=xp, HP=hp, SPEED=speed, LOOK=look, MANA=mana,
        RACEID=raceid,
        BCLASS=random.choice(["Amphibic","Dragon","Demon","Elemental","Humanoid","Mammal","Magical","Undead"]),
        BRACE=random.choice(["AMPHIBIC","DRAGON","DEMON","ELEMENTAL","HUMANOID","MAMMAL","MAGICAL","UNDEAD"]),
        TOKILL=random.choice([250,500,1000,2500]),
        FUNLOCK=random.choice([10,25,50,100]),
        SUNLOCK=random.choice([100,250,500,1000]),
        CPOINTS=random.choice([5,10,15,20,25]),
        STARS=random.choice([1,2,3,4]),
        RACE=random.choice(["blood","undead","fire","energy","venom"]),
        CORPSE=random.choice([100,200,300,400,500,600,6079]),
        ATKABLE=random.choices(['true','false'],[90,10])[0],
        HOSTILE=random.choices(['true','false'],[80,20])[0],
        PUSHABLE=random.choices(['true','false'],[30,70])[0],
        SAC=random.choice([90,95]),
        TDIST=random.choice([1,2,3,4]),
        RUNHP=valor_num_mk2('runHealth|=', min_v=0, max_v=1000, fallback=10),
        VOCES=vzs if vzs else "-- sem vozes",
        LOOT=loot if loot else "-- sem loot",
        ATAQUES=atqs if atqs else "-- sem ataques",
        ELEMS=elems,
        DEF=random.randint(1, 100),
        ARM=random.randint(1, 100),
    )

# ─── NPC TEMPLATE ────────────────────────────────────────
NPC_TPL = """local internalNpcName = "{NOME}"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {{}}

npcConfig.name = internalNpcName
npcConfig.description = internalNpcName
npcConfig.health = 100
npcConfig.maxHealth = npcConfig.health
npcConfig.walkInterval = {WALKINT}
npcConfig.walkRadius = {WALKR}
npcConfig.outfit = {{
    lookType = {LOOK},
}}
npcConfig.flags = {{
    floorchange = false,
}}

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

npcHandler:setMessage(MESSAGE_GREET, "{GREET}")
npcHandler:setMessage(MESSAGE_FAREWELL, "{FAREWELL}")
npcHandler:setMessage(MESSAGE_SENDTRADE, "{TRADE}")

npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)

npcType:register(npcConfig)"""

def gerar_npc():
    nome = nome_npc_fn()
    look = valor_num_mk2('lookType|=', min_v=1, max_v=2000, fallback=100)
    dialogo_variants = [
        ("Ola, aventureiro!", "Ate logo!", "O que deseja?"),
        ("Bem-vindo, |PLAYERNAME|!", "Volte sempre!", "Veja meus itens!"),
        ("Precisa de algo?", "Tchau!", "Interessado em algo?"),
        ("Ola, viajante!", "Ate mais!", "O que procura?"),
    ]
    greet, farewell, trade = random.choice(dialogo_variants)
    
    return NPC_TPL.format(
        NOME=nome,
        LOOK=look,
        WALKINT=random.choice([1500, 2000, 2500]),
        WALKR=random.choice([1, 2, 3]),
        GREET=greet,
        FAREWELL=farewell,
        TRADE=trade,
    )

# ─── MAIN ────────────────────────────────────────────────
print("=" * 60)
print("  MCR BLANK FILLER v2")
print("=" * 60)

for i in range(3):
    texto = gerar_npc()
    fp = os.path.join(OUT_DIR, f"npc_bf_{i+1}.lua")
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(f"-- MCR BLANK FILLER v2 — {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(texto + "\n")
    print(f"\n  NPC {i+1} -> {os.path.basename(fp)}")
    for linha in texto.split('\n')[:15]:
        print(f"  {linha}")

print(f"\n{'─'*60}")

for i in range(5):
    texto = gerar_monstro()
    fp = os.path.join(OUT_DIR, f"monster_bf_{i+1}.lua")
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(f"-- MCR BLANK FILLER v2 — {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(texto + "\n")
    print(f"\n  MONSTER {i+1} -> {os.path.basename(fp)}")
    for linha in texto.split('\n')[:15]:
        print(f"  {linha}")

print(f"\n{'='*60}")
print(f"  3 NPCs + 5 monstros em {OUT_DIR}")
print(f"{'='*60}")
