#!/usr/bin/env python3
"""extract_npc.py v2 — Extracts structured data from NPC files."""
import os, re, json

_BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

RAIZ_NPC = r"E:\Projeto MCR\Canary\data-otservbr-global\npc"
OUT_JSON = os.path.join(_BASE, "nichos", "tibia", "npc_db.json")

def extract(fp):
    with open(fp, "r", encoding="utf-8", errors="replace") as f:
        texto = f.read()

    dados = {"_src": os.path.relpath(fp, RAIZ_NPC)}

    # name from internalNpcName or createNpcType
    m = re.search(r'local internalNpcName\s*=\s*"(.+?)"', texto)
    if m: dados["name"] = m.group(1)
    if not dados.get("name"):
        m = re.search(r'Game\.createNpcType\("(.+?)"\)', texto)
        if m: dados["name"] = m.group(1)
    if m := re.search(r'npcConfig\.description\s*=\s*"(.+?)"', texto):
        dados["description"] = m.group(1)
    if m := re.search(r'npcConfig\.health\s*=\s*(\d+)', texto):
        dados["health"] = int(m.group(1))
    if m := re.search(r'npcConfig\.maxHealth\s*=\s*(\d+)', texto):
        dados["maxHealth"] = int(m.group(1))
    if m := re.search(r'npcConfig\.walkInterval\s*=\s*(\d+)', texto):
        dados["walkInterval"] = int(m.group(1))
    if m := re.search(r'npcConfig\.walkRadius\s*=\s*(\d+)', texto):
        dados["walkRadius"] = int(m.group(1))

    # outfit
    m = re.search(r'npcConfig\.outfit\s*=\s*\{([^}]+)\}', texto, re.DOTALL)
    if m:
        outfit = {}
        for kv in re.finditer(r'(\w+)\s*=\s*(\d+)', m.group(1)):
            outfit[kv.group(1)] = int(kv.group(2))
        if outfit: dados["outfit"] = outfit

    # voices
    m = re.search(r'npcConfig\.voices\s*=\s*\{', texto)
    if m:
        start = m.end()
        depth, end = 1, start
        while depth > 0 and end < len(texto):
            if texto[end] == '{': depth += 1
            elif texto[end] == '}': depth -= 1
            end += 1
        block = texto[start:end-1]
        iv = re.search(r'interval\s*=\s*(\d+)', block)
        ch = re.search(r'chance\s*=\s*(\d+)', block)
        if iv: dados["voice_interval"] = int(iv.group(1))
        if ch: dados["voice_chance"] = int(ch.group(1))
        voices = []
        for v in re.finditer(r'\{\s*text\s*=\s*"(.+?)"\s*\}', block):
            voices.append(v.group(1))
        if voices: dados["voices"] = voices

    # shop
    # Find npcConfig.shop = { ... } block
    m = re.search(r'npcConfig\.shop\s*=\s*\{', texto)
    if m:
        start = m.end()
        depth, end = 1, start
        while depth > 0 and end < len(texto):
            if texto[end] == '{': depth += 1
            elif texto[end] == '}': depth -= 1
            end += 1
        block = texto[start:end-1]
        # Each shop item: { itemName = "...", clientId = N, buy = N, sell = N }
        shop_items = []
        for si_m in re.finditer(r'\{(.+?)\}', block):
            item = {"id": None, "buy": 0, "sell": 0}
            for kv in re.finditer(r'(\w+)\s*=\s*(.+?)(?:,|\n|$)', si_m.group(1)):
                k, v = kv.group(1).strip(), kv.group(2).strip().strip(',')
                if v.startswith('"'): v = v.strip('"')
                elif v.isdigit(): v = int(v)
                if k == "itemName": item["name"] = v
                elif k == "clientId": item["id"] = v
                elif k == "buy": item["buy"] = v
                elif k == "sell": item["sell"] = v
            if item.get("name"): shop_items.append(item)
        if shop_items: dados["shop"] = shop_items

    # messages
    for m_msg in re.finditer(r'npcHandler:setMessage\((\w+),\s*"(.+?)"\)', texto):
        key = m_msg.group(1)
        if key.startswith("MESSAGE_"):
            key = key.replace("MESSAGE_", "").lower()
        dados.setdefault("messages", {})[key] = m_msg.group(2)

    # keyword -> response mapping
    keywords = []
    # Simple form: keywordHandler:addKeyword({ "word" }, StdModule.say, { ... text = "..." })
    for kw_m in re.finditer(
        r'keywordHandler:addKeyword\(\{([^}]+)\},\s*StdModule\.say,\s*\{[^}]*?\btext\s*=\s*"(.+?)"',
        texto
    ):
        words = [w.strip().strip("'\"") for w in kw_m.group(1).split(",")]
        keywords.append({"words": words, "response": kw_m.group(2)})
    if keywords: dados["keywords"] = keywords

    # Callback (quest) storage references
    storages = set()
    for s in re.finditer(r'Storage\.([\w.]+)', texto):
        storages.add(s.group(1))
    if storages: dados["storages"] = sorted(storages)

    # Flags
    m = re.search(r'npcConfig\.flags\s*=\s*\{([^}]*)\}', texto, re.DOTALL)
    if m:
        flags = {}
        for kv in re.finditer(r'(\w+)\s*=\s*(true|false)', m.group(1)):
            flags[kv.group(1)] = kv.group(2) == 'true'
        if flags: dados["flags"] = flags

    return dados.get("name", ""), dados


db = {}
total = 0
for raiz, dirs, files in os.walk(RAIZ_NPC):
    for f in sorted(files):
        if not f.endswith('.lua'): continue
        fp = os.path.join(raiz, f)
        try:
            nome, dados = extract(fp)
            if nome:
                db[nome] = dados
                total += 1
        except Exception as e:
            print(f"  ERRO {f}: e")

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=1)

print(f"NPCs extraidos: {total}")
print(f"Salvo em: {OUT_JSON} ({os.path.getsize(OUT_JSON)/1024:.0f} KB)")
