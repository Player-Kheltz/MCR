#!/usr/bin/env python3
"""extract_monster.py — Extrai campos de monstros para JSON estruturado."""
import os, re, json

RAIZ_MON = r"E:\Projeto MCR\Canary\data-otservbr-global\monster"
OUT_JSON = r"E:\MCR\nichos\tibia\monster_db.json"

def extract(fp):
    with open(fp, "r", encoding="utf-8", errors="replace") as f:
        texto = f.read()
    
    m = re.search(r'Game\.createMonsterType\("(.+?)"\)', texto)
    nome = m.group(1) if m else ""
    
    dados = {"_src": os.path.relpath(fp, RAIZ_MON)}
    dados["name"] = nome
    
    if m := re.search(r'monster\.description\s*=\s*"(.+?)"', texto):
        dados["description"] = m.group(1)
    if m := re.search(r'monster\.experience\s*=\s*(\d+)', texto):
        dados["experience"] = int(m.group(1))
    if m := re.search(r'monster\.raceId\s*=\s*(\d+)', texto):
        dados["raceId"] = int(m.group(1))
    if m := re.search(r'monster\.health\s*=\s*(\d+)', texto):
        dados["health"] = int(m.group(1))
    if m := re.search(r'monster\.maxHealth\s*=\s*(\d+)', texto):
        dados["maxHealth"] = int(m.group(1))
    if m := re.search(r'monster\.corpse\s*=\s*(\d+)', texto):
        dados["corpse"] = int(m.group(1))
    if m := re.search(r'monster\.speed\s*=\s*(\d+)', texto):
        dados["speed"] = int(m.group(1))
    if m := re.search(r'monster\.manaCost\s*=\s*(\d+)', texto):
        dados["manaCost"] = int(m.group(1))
    if m := re.search(r'monster\.race\s*=\s*"(.+?)"', texto):
        dados["race_type"] = m.group(1)
    
    if m := re.search(r'monster\.outfit\s*=\s*\{([^}]+)\}', texto, re.DOTALL):
        outfit = {}
        for kv in re.finditer(r'(\w+)\s*=\s*(\d+)', m.group(1)):
            outfit[kv.group(1)] = int(kv.group(2))
        dados["outfit"] = outfit
    
    if m := re.search(r'monster\.defenses\s*=\s*\{', texto):
        start = m.end()
        depth, end = 1, start
        while depth > 0 and end < len(texto):
            if texto[end] == '{': depth += 1
            elif texto[end] == '}': depth -= 1
            end += 1
        block = texto[start:end-1]
        if m2 := re.search(r'defense\s*=\s*(\d+)', block):
            dados["defense"] = int(m2.group(1))
        if m2 := re.search(r'armor\s*=\s*(\d+)', block):
            dados["armor"] = int(m2.group(1))
        if m2 := re.search(r'mitigation\s*=\s*([\d.]+)', block):
            dados["mitigation"] = float(m2.group(1))
    
    if m := re.search(r'monster\.Bestiary\s*=\s*\{', texto):
        start = m.end()
        depth, end = 1, start
        while depth > 0 and end < len(texto):
            if texto[end] == '{': depth += 1
            elif texto[end] == '}': depth -= 1
            end += 1
        block = texto[start:end-1]
        bestiary = {}
        for kv in re.finditer(r'(\w+)\s*=\s*(.+?)(?:,|\n|$)', block):
            val = kv.group(2).strip().strip(',')
            if val.startswith('"'): val = val.strip('"')
            elif val.isdigit(): val = int(val)
            elif val.replace('.','',1).isdigit(): val = float(val)
            bestiary[kv.group(1)] = val
        dados["bestiary"] = bestiary
    
    if m := re.search(r'monster\.loot\s*=\s*\{', texto):
        start = m.end()
        depth, end = 1, start
        while depth > 0 and end < len(texto):
            if texto[end] == '{': depth += 1
            elif texto[end] == '}': depth -= 1
            end += 1
        block = texto[start:end-1]
        loot = []
        for item_text in re.finditer(r'\{(.+?)\}', block):
            item = {}
            for kv in re.finditer(r'(\w+)\s*=\s*(.+?)(?:,|\n|$)', item_text.group(1)):
                val = kv.group(2).strip().strip(',')
                if val.isdigit(): val = int(val)
                item[kv.group(1)] = val
            if item: loot.append(item)
        dados["loot"] = loot
    
    if m := re.search(r'monster\.attacks\s*=\s*\{', texto):
        start = m.end()
        depth, end = 1, start
        while depth > 0 and end < len(texto):
            if texto[end] == '{': depth += 1
            elif texto[end] == '}': depth -= 1
            end += 1
        block = texto[start:end-1]
        attacks = []
        for at_text in re.finditer(r'\{(.+?)\}', block):
            atk = {}
            for kv in re.finditer(r'(\w+)\s*=\s*(.+?)(?:,|\n|$)', at_text.group(1)):
                val = kv.group(2).strip().strip(',')
                if val.isdigit(): val = int(val)
                elif val.replace('-','',1).isdigit(): val = int(val)  
                atk[kv.group(1)] = val
            if atk: attacks.append(atk)
        dados["attacks"] = attacks
    
    if m := re.search(r'monster\.voices\s*=\s*\{', texto):
        start = m.end()
        depth, end = 1, start
        while depth > 0 and end < len(texto):
            if texto[end] == '{': depth += 1
            elif texto[end] == '}': depth -= 1
            end += 1
        block = texto[start:end-1]
        # Extract interval and chance
        interval = re.search(r'interval\s*=\s*(\d+)', block)
        chance = re.search(r'chance\s*=\s*(\d+)', block)
        if interval: dados["voices_interval"] = int(interval.group(1))
        if chance: dados["voices_chance"] = int(chance.group(1))
        # Extract individual voice entries
        voices = []
        for v in re.finditer(r'\{\s*text\s*=\s*"(.+?)"\s*(?:,\s*yell\s*=\s*(true|false))?\s*\}', block):
            voices.append({"text": v.group(1), "yell": v.group(2) == 'true' if v.group(2) else False})
        if voices: dados["voices"] = voices
    
    return nome, dados


# Process all monster files
db = {}
total = 0
for raiz, dirs, files in os.walk(RAIZ_MON):
    for f in sorted(files):
        if not f.endswith('.lua'): continue
        fp = os.path.join(raiz, f)
        try:
            nome, dados = extract(fp)
            if nome:
                db[nome] = dados
                total += 1
        except Exception as e:
            print(f"  ERRO {f}: {e}")

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=1)

print(f"\nMonstros extraidos: {total}")
print(f"Salvo em: {OUT_JSON} ({os.path.getsize(OUT_JSON)/1024:.0f} KB)")
