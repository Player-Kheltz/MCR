"""Fix parser to be more flexible"""
import re

text = """SISTEMA: Dragoes Ancestrais de Eridanus

NPCs:
  draco_ancieta: Draconida Sua Mae | saudacao: "Ola, jovem!" | item_id: 12345 | item_preco: 1000

MONSTERS:
  drago_ancieta: Dragao Ancestral | hp: 800 | atk: 60 | def: 20 | loot_id: 41002 | loot_chance: 0.7
  drago_boss: Dragao Boss | hp: 1500 | atk: 85 | def: 35 | loot_id: 41004 | loot_chance: 0.5

ITEMS:
  ouro_dragonico: Ouro Dragonico | id: 41002 | tipo: quest | atk: 0 | def: 0 | peso: 3

SPELLS:
  fogo_divino: Fogo Divino | elemento: holy | dano: 200 | mana: 80 | cd: 10"""

plano = {'npcs': [], 'monsters': [], 'items': [], 'spells': []}

current = None
for line in text.split('\n'):
    line = line.strip()
    upper = line.upper()
    
    if 'SISTEMA:' in upper:
        plano['sistema'] = line.split(':',1)[1].strip()
    elif 'NPCS:' in upper:
        current = 'npcs'
    elif 'MONSTERS:' in upper:
        current = 'monsters'
    elif 'ITEMS:' in upper:
        current = 'items'
    elif 'SPELLS:' in upper:
        current = 'spells'
    elif current and '|' in line:
        parts = [p.strip() for p in line.split('|')]
        entry = {}
        for p in parts:
            if ':' in p:
                k, v = p.split(':', 1)
                k = k.strip().lower()
                v = v.strip().strip('"').strip("'")
                if k in ('hp', 'atk', 'def', 'dano', 'mana', 'cd', 'item_id', 'item_preco', 
                        'loot_id', 'id', 'peso', 'loot_chance'):
                    try: v = int(v) if '.' not in v else float(v)
                    except: pass
                entry[k] = v
        
        if entry:
            plano[current].append(entry)

print(f"Sistema: {plano.get('sistema','')}")
print(f"NPCs: {len(plano['npcs'])} - {[n.get('nome','?') for n in plano['npcs']]}")
print(f"Monsters: {len(plano['monsters'])} - {[m.get('nome','?') for m in plano['monsters']]}")
print(f"Items: {len(plano['items'])} - {[i.get('nome','?') for i in plano['items']]}")
print(f"Spells: {len(plano['spells'])} - {[s.get('nome','?') for s in plano['spells']]}")
