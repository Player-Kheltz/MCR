#!/usr/bin/env python3
"""gerador_hibrido.py — Gera monstros/NPCs originais.
Estratégia: valores exatos do JSON DB + criatividade Markov para loot/voices/diálogo."""

import json, os, random, re, sys
from collections import defaultdict

# UTF-8 console output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # type: ignore

random.seed()  # True entropy


def sanitize(s: str) -> str:
    """Keep only printable ASCII for names."""
    s = ''.join(c for c in s if 32 <= ord(c) < 127)
    s = s.strip().strip('_').strip('-').strip()
    return s or "Creature"

# ── Markov Chain -----------------------------------------------------------------
class MarkovChain:
    """N-gram character-level Markov chain."""
    def __init__(self, n=4):
        self.n = n
        self.ngrams = defaultdict(list)

    def train(self, texts):
        for txt in texts:
            txt = f"^{txt}$"
            for i in range(len(txt) - self.n + 1):
                gram = txt[i:i+self.n]
                prefix = gram[:-1]
                suffix = gram[-1]
                self.ngrams[prefix].append(suffix)

    def generate(self, min_len=4, max_len=20):
        prefix = random.choice([k for k in self.ngrams if k[0] == '^'])
        result = prefix
        for _ in range(max_len * 2):
            if prefix in self.ngrams:
                ch = random.choice(self.ngrams[prefix])
                if ch == '$':
                    break
                result += ch
                prefix = (prefix + ch)[1:]
            else:
                break
        result = result.strip('^$')
        if len(result) < min_len:
            return self.generate(min_len, max_len)
        return result


class WordMarkov:
    """Word-level bigram Markov chain."""
    def __init__(self):
        self.bigrams = defaultdict(list)

    def train(self, texts):
        for txt in texts:
            words = txt.split()
            if len(words) < 2: continue
            for i in range(len(words)-1):
                self.bigrams[words[i]].append(words[i+1])

    def generate(self, min_words=3, max_words=15):
        start = random.choice(list(self.bigrams.keys()))
        result = [start]
        for _ in range(max_words * 2):
            last = result[-1]
            if last in self.bigrams:
                nxt = random.choice(self.bigrams[last])
                result.append(nxt)
                if len(result) >= max_words:
                    break
            else:
                break
        if len(result) < min_words:
            return self.generate(min_words, max_words)
        return ' '.join(result)


# ── Build Markov Models from DB --------------------------------------------------
def build_models(db_monster, db_npc):
    """Train Markov chains on real names + word patterns."""
    # Character-level Markov for names (monsters)
    mnames = [k for k in db_monster if len(k) >= 3]
    mc_monster_name = MarkovChain(n=4)
    mc_monster_name.train(mnames)

    # Character-level Markov for NPC names
    nnames = [k for k in db_npc if len(k) >= 3]
    mc_npc_name = MarkovChain(n=4)
    mc_npc_name.train(nnames)

    def esc(t):
        t = re.sub(r'\{[^}]*\}', '', t)  # strip {template} tags
        return t.replace('"', "'").replace('\n', ' ').replace('\r', '').strip()[:200]

    # Word-level Markov for voice lines
    all_voices = []
    for v in db_monster.values():
        for voice in v.get("voices", []):
            t = esc(voice.get("text", ""))
            if 3 <= len(t.split()) <= 20:
                all_voices.append(t)
    mc_voice = WordMarkov()
    mc_voice.train(all_voices)

    # Word-level Markov for keyword responses (NPC dialogue)
    all_responses = []
    for v in db_npc.values():
        for kw in v.get("keywords", []):
            r = esc(kw.get("response", ""))
            if 3 <= len(r.split()) <= 25:
                all_responses.append(r)
    mc_response = WordMarkov()
    mc_response.train(all_responses)

    # Word-level Markov for NPC messages
    all_messages = []
    for v in db_npc.values():
        for key in ("greet", "farewell", "walkaway"):
            msg = esc(v.get("messages", {}).get(key, ""))
            if 3 <= len(msg.split()) <= 30:
                all_messages.append(msg)
    mc_message = WordMarkov()
    mc_message.train(all_messages)

    # Shop item name pool
    all_item_names = set()
    for v in db_npc.values():
        for item in v.get("shop", []):
            name = item.get("name", "")
            if name: all_item_names.add(name)
    all_item_names = sorted(all_item_names)
    # Build item name Markov
    mc_item_name = MarkovChain(n=5)
    mc_item_name.train(all_item_names)

    return {
        "monster_name": mc_monster_name,
        "npc_name": mc_npc_name,
        "voice": mc_voice,
        "response": mc_response,
        "message": mc_message,
        "item_name": mc_item_name,
    }


# ── Monster Generator ------------------------------------------------------------
def sample_loot(db_monster, max_items=8):
    """Generate loot by sampling real item patterns from DB."""
    all_loot_entries = []
    for v in db_monster.values():
        all_loot_entries.extend(v.get("loot", []))
    if not all_loot_entries:
        return []

    # Generate varied loot
    n = random.randint(1, max_items)
    loot = []
    used_ids = set()
    # Weight by frequency in real data
    weighted = all_loot_entries[:]
    for _ in range(n):
        if not weighted: break
        entry = random.choice(weighted)
        eid = entry.get("id", entry.get("itemId", 0))
        if eid and eid not in used_ids:
            loot.append({
                "id": eid,
                "chance": entry.get("chance", random.randint(500, 50000)),
                "maxCount": entry.get("maxCount", 1),
            })
            used_ids.add(eid)
    return loot


def sample_voices(db_monster, mc_voice, max_voices=5):
    """Generate voice lines — mix of real and Markov-generated."""
    voices = []
    # Some real sampled voices
    all_real = []
    for v in db_monster.values():
        for vi in v.get("voices", []):
            t = vi.get("text", "")
            if t: all_real.append(t)

    n_real = random.randint(1, min(3, len(all_real)))
    for _ in range(n_real):
        if all_real:
            voices.append(random.choice(all_real))

    # Some Markov-generated
    n_gen = random.randint(1, max_voices - len(voices))
    for _ in range(n_gen):
        try:
            txt = mc_voice.generate(min_words=4, max_words=12)
            voices.append(txt)
        except: pass

    random.shuffle(voices)
    return voices[:max_voices]


def pick_nice_template(db_monster):
    """Pick a template that has reasonable data (not all zeros, has loot, has voices)."""
    keys = list(db_monster.keys())
    random.shuffle(keys)
    for k in keys:
        v = db_monster[k]
        if v.get("experience", 0) > 0 and v.get("health", 0) > 0:
            return k, v
    return keys[0], db_monster[keys[0]]


def sample_attacks(db_monster):
    """Sample attack patterns from real monsters."""
    all_atk = []
    for v in db_monster.values():
        all_atk.extend(v.get("attacks", []))
    if not all_atk:
        return []

    n = random.randint(1, 4)
    attacks = []
    used_names = set()
    for _ in range(n * 3):
        atk = random.choice(all_atk)
        aname = atk.get("name", "")
        if aname and aname not in used_names:
            attacks.append({
                "name": aname,
                "interval": atk.get("interval", 2000),
                "chance": atk.get("chance", 10),
                "min": atk.get("min", 0),
                "max": atk.get("max", 0),
            })
            used_names.add(aname)
        if len(attacks) >= n:
            break
    return attacks


def generate_monster(db_monster, mc_models):
    """Generate one original monster .lua file content."""
    # Pick a random real monster as structural template
    template_name, tmpl = pick_nice_template(db_monster)

    # Generate new name
    mc_name = mc_models["monster_name"]
    new_name = None
    for _ in range(20):
        try:
            candidate = sanitize(mc_name.generate(min_len=4, max_len=18))
            if candidate and candidate not in db_monster:
                new_name = candidate
                break
        except:
            pass
    if not new_name:
        new_name = sanitize(f"{template_name}_{random.randint(100,999)}")
    if not new_name:
        new_name = f"Creature{random.randint(1000,9999)}"

    # Critical values from template — vary ±15%
    def vary(val, pct=0.15):
        delta = max(1, int(val * pct))
        return max(1, val + random.randint(-delta, delta))

    ex = tmpl.get("experience", random.randint(100, 5000))
    hp = tmpl.get("health", random.randint(100, 10000))
    mhp = tmpl.get("maxHealth", hp)
    spd = tmpl.get("speed", random.randint(50, 500))
    exp_out = vary(ex)
    health_out = vary(hp)
    speed_out = vary(spd)

    outfit = tmpl.get("outfit", {"lookType": 1})
    race = tmpl.get("race_type", "blood")
    raceId = tmpl.get("raceId", random.randint(1, 100))
    corpse = tmpl.get("corpse", 0)
    if corpse == 0:
        corpse = random.choice([0, random.randint(1800, 6000)])
    defense = tmpl.get("defense", random.randint(1, 80))
    if defense == 0: defense = random.randint(1, 30)
    armor = tmpl.get("armor", random.randint(1, 80))
    if armor == 0: armor = random.randint(1, 30)

    # Creative parts
    loot = sample_loot(db_monster)
    voices = sample_voices(db_monster, mc_models["voice"])
    attacks = sample_attacks(db_monster)

    # Build the template
    voice_interval = random.choice([5000, 8000, 10000, 15000, 20000, 30000])
    voice_chance = random.choice([10, 20, 30, 40, 50])

    parts = []
    parts.append(f'''local monster = Game.createMonsterType("{new_name}")
monster:register()''')

    parts.append(f'''
monster.name = "{new_name}"
monster.description = "a {new_name}"
monster.experience = {exp_out}
monster.outfit = {{''')
    for k, v in outfit.items():
        parts.append(f"\t{k} = {v},")
    parts.append(f'''}}
monster.health = {health_out}
monster.maxHealth = {mhp}
monster.race = "{race}"
monster.raceId = {raceId}
monster.corpse = {corpse}
monster.speed = {speed_out}
monster.manaCost = 0

monster.changeTarget = {random.choice(["true", "false"])}
monster.strategies = {{"{random.choice(['attack', 'retreat', 'defend', 'idle', 'patrol'])}"}}
monster.flags = {{
	{random.choice(["ignoreSpawnBlock = false,", "ignoreSpawnBlock = true,"])}
	{random.choice(["pushCreatures = true,", "pushCreatures = false,"])}
	{random.choice(["clientAnimations = true,", "clientAnimations = false,"])}
	{random.choice(["attackPlayers = true,", "attackPlayers = false,"])}
}}

monster.defenses = {{
	defense = {defense},
	armor = {armor},
	{random.choice(["", "-- mitigation = 1.0"])}
}}''')

    # Loot
    if loot:
        parts.append(f'''
monster.loot = {{''')
        for item in loot:
            parts.append(f"\t{{id = {item['id']}, chance = {item['chance']}, maxCount = {item.get('maxCount', 1)}}},")
        parts.append(f'}}')
    else:
        # Give at least one default gold coin
        parts.append(f'''
monster.loot = {{
	{{id = 2148, chance = 100000, maxCount = {random.randint(1, 50)}}},
}}''')

    # Attacks
    if attacks:
        parts.append(f'''
monster.attacks = {{''')
        for atk in attacks:
            aname = atk['name'].strip('"').strip("'")
            if atk['min'] or atk['max']:
                parts.append(f"\t{{name = \"{aname}\", interval = {atk.get('interval', 2000)}, chance = {atk.get('chance', 10)}, min = {atk['min']}, max = {atk['max']}}},")
            else:
                parts.append(f"\t{{name = \"{aname}\", interval = {atk.get('interval', 2000)}, chance = {atk.get('chance', 10)}}},")
        parts.append(f'}}')

    # Voices
    if voices:
        parts.append(f'''
monster.voices = {{
	interval = {voice_interval},
	chance = {voice_chance},''')
        for v in voices:
            parts.append(f'\t{{text = "{v}", yell = {random.choice(["true", "false"])}}},')
        parts.append(f'}}')

    parts.append(f'''
monster.immunities = {{
	{{type = "{random.choice(['fire', 'energy', 'earth', 'ice', 'holy', 'death', 'drown', 'physical', 'lifedrain', 'paralyze', 'drunk', 'manadrain'])}", condition = true}},
}}

monster:register()''')

    return '\n'.join(parts), new_name


# ── NPC Generator -----------------------------------------------------------------
def generate_npc(db_npc, mc_models):
    """Generate one original NPC .lua file content."""
    # Pick a random template
    template_name = random.choice(list(db_npc.keys()))
    tmpl = db_npc[template_name]

    mc_nm = mc_models["npc_name"]
    new_name = None
    for _ in range(20):
        try:
            candidate = sanitize(mc_nm.generate(min_len=5, max_len=20))
            if candidate and candidate not in db_npc:
                new_name = candidate.title()
                break
        except:
            pass
    if not new_name:
        new_name = sanitize(f"{template_name}_{random.randint(100,999)}")
    if not new_name:
        new_name = f"Npc{random.randint(1000,9999)}"

    outfit = tmpl.get("outfit", {"lookType": 130, "lookHead": 0, "lookBody": 0, "lookLegs": 0, "lookFeet": 0})
    walkInterval = tmpl.get("walkInterval", 2000)
    walkRadius = tmpl.get("walkRadius", 2)

    # Shop — mix real items, possibly with Markov names
    shop_items = []
    all_shop = []
    for v in db_npc.values():
        all_shop.extend(v.get("shop", []))
    n_shop = random.randint(0, 12)
    used_names = set()
    for _ in range(n_shop * 3):
        item = random.choice(all_shop) if all_shop else {}
        iname = item.get("name", "")
        if iname and iname not in used_names:
            buy_val = item.get("buy", 0)
            if not buy_val or buy_val == 0:
                buy_val = random.randint(10, 500)
            sell_val = item.get("sell", 0)
            if not sell_val or sell_val == 0:
                sell_val = None
            shop_items.append({
                "name": iname,
                "id": item.get("id", random.randint(2000, 10000)),
                "buy": buy_val,
                "sell": sell_val,
            })
            used_names.add(iname)
            if len(shop_items) >= n_shop:
                break

    # Keywords / responses
    all_keywords = []
    for v in db_npc.values():
        all_keywords.extend(v.get("keywords", []))
    n_kw = random.randint(2, 6)
    keywords = []
    used_kw = set()
    for _ in range(n_kw * 3):
        kw = random.choice(all_keywords) if all_keywords else {}
        words = kw.get("words", [])
        word_label = words[0] if words else ""
        if word_label and word_label not in used_kw:
            # Try Markov for response
            try:
                resp = mc_models["response"].generate(min_words=3, max_words=12)
            except:
                resp = kw.get("response", f"Hello, I am {new_name}.")
            keywords.append({"words": words[:2], "response": resp})
            used_kw.add(word_label)
            if len(keywords) >= n_kw:
                break

    # Messages
    mc_msg = mc_models["message"]
    try: greet = mc_msg.generate(min_words=4, max_words=10)
    except: greet = f"Greetings, |PLAYERNAME|. Welcome to my shop."
    try: farewell = mc_msg.generate(min_words=3, max_words=8)
    except: farewell = "Good bye. Come back anytime."
    try: walkaway = mc_msg.generate(min_words=2, max_words=5)
    except: walkaway = "Farewell."

    voices = []
    try:
        for _ in range(random.randint(1, 4)):
            v = mc_models["voice"].generate(min_words=4, max_words=12)
            voices.append(v)
    except: pass

    # Build file
    has_shop = len(shop_items) > 0
    has_voices = len(voices) > 0
    has_keywords = len(keywords) > 0

    parts = []
    parts.append(f'''local internalNpcName = "{new_name}"
local npcType = Game.createNpcType(internalNpcName)
local npcConfig = {{}}

npcConfig.name = internalNpcName
npcConfig.description = internalNpcName

npcConfig.health = 100
npcConfig.maxHealth = npcConfig.health
npcConfig.walkInterval = {walkInterval}
npcConfig.walkRadius = {walkRadius}

npcConfig.outfit = {{''')
    for k, v in outfit.items():
        parts.append(f"\t{k} = {v},")
    parts.append('''
}

npcConfig.flags = {
\tfloorchange = false,
}''')

    if has_voices:
        parts.append(f'''
npcConfig.voices = {{
\tinterval = {random.choice([8000, 10000, 15000, 20000])},
\tchance = {random.choice([30, 40, 50, 60])},''')
        for v in voices:
            parts.append(f'\t{{text = "{v}"}},')
        parts.append('}')

    if has_shop:
        parts.append(f'''
npcConfig.shop = {{''')
        for item in shop_items:
            sell_str = ""
            if item.get("sell"):
                sell_str = f", sell = {item['sell']}"
            parts.append(f"\t{{itemName = \"{item['name']}\", clientId = {item['id']}, buy = {item['buy']}{sell_str}}},")
        parts.append(f'''
}}

npcType.onBuyItem = function(npc, player, itemId, subType, amount, ignore, inBackpacks, totalCost)
\tnpc:sellItem(player, itemId, amount, subType, 0, ignore, inBackpacks)
end
npcType.onSellItem = function(npc, player, itemId, subtype, amount, ignore, name, totalCost)
\tplayer:sendTextMessage(MESSAGE_TRADE, string.format("Sold %%ix %%s for %%i gold.", amount, name, totalCost))
end
npcType.onCheckItem = function(npc, player, clientId, subType) end''')

    parts.append(f'''
local keywordHandler = KeywordHandler:new()
local npcHandler = NpcHandler:new(keywordHandler)''')

    if has_keywords:
        for kw in keywords:
            word_str = ", ".join(f'"{w}"' for w in kw['words'])
            parts.append(f'''
keywordHandler:addKeyword({{{word_str}}}, StdModule.say, {{npcHandler = npcHandler, text = "{kw['response']}"}})''')

    parts.append(f'''
npcType.onThink = function(npc, interval)
\tnpcHandler:onThink(npc, interval)
end

npcType.onAppear = function(npc, creature)
\tnpcHandler:onAppear(npc, creature)
end

npcType.onDisappear = function(npc, creature)
\tnpcHandler:onDisappear(npc, creature)
end

npcType.onSay = function(npc, creature, type, message)
\tnpcHandler:onSay(npc, creature, type, message)
end

npcType.onCloseChannel = function(npc, creature)
\tnpcHandler:onCloseChannel(npc, creature)
end

npcHandler:setMessage(MESSAGE_GREET, "{greet}")
npcHandler:setMessage(MESSAGE_FAREWELL, "{farewell}")
npcHandler:setMessage(MESSAGE_WALKAWAY, "{walkaway}")

npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)

npcType:register(npcConfig)''')

    return '\n'.join(parts), new_name


# ── Main --------------------------------------------------------------------------
def main():
    print("Carregando bases de dados...")
    db_monster = json.load(open(r"E:\MCR\nichos\tibia\monster_db.json", "r", encoding="utf-8"))
    db_npc = json.load(open(r"E:\MCR\nichos\tibia\npc_db.json", "r", encoding="utf-8"))
    print(f"  Monstros: {len(db_monster)}")
    print(f"  NPCs: {len(db_npc)}")

    print("Treinando modelos Markov...")
    mc_models = build_models(db_monster, db_npc)

    out_monster_dir = r"E:\MCR\nichos\tibia\gerado\monster"
    out_npc_dir = r"E:\MCR\nichos\tibia\gerado\npc"
    os.makedirs(out_monster_dir, exist_ok=True)
    os.makedirs(out_npc_dir, exist_ok=True)

    # Generate monsters
    n_monsters = 10
    print(f"\nGerando {n_monsters} monstros...")
    for i in range(n_monsters):
        content, name = generate_monster(db_monster, mc_models)
        fname = name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
        fp = os.path.join(out_monster_dir, f"{fname}.lua")
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [{i+1}/{n_monsters}] {name} -> {fp}")

    # Generate NPCs
    n_npcs = 10
    print(f"\nGerando {n_npcs} NPCs...")
    for i in range(n_npcs):
        content, name = generate_npc(db_npc, mc_models)
        fname = name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
        fp = os.path.join(out_npc_dir, f"{fname}.lua")
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [{i+1}/{n_npcs}] {name} -> {fp}")

    print("\nConcluído!")


if __name__ == "__main__":
    main()
