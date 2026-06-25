"""Fix parser - handle nome in first field"""
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

plano = {'sistema': '', 'npcs': [], 'monsters': [], 'items': [], 'spells': []}
current = None

for line in text.split('\n'):
    line = line.strip()
    if not line: continue
    
    upper = line.upper()
    if upper.startswith('SISTEMA:'):
        plano['sistema'] = line.split(':', 1)[1].strip()
    elif upper.startswith('NPCS:'):
        current = 'npcs'
    elif upper.startswith('MONSTERS:'):
        current = 'monsters'
    elif upper.startswith('ITEMS:'):
        current = 'items'
    elif upper.startswith('SPELLS:'):
        current = 'spells'
    elif current and '|' in line:
        parts = [p.strip() for p in line.split('|')]
        entry = {}
        
        # First part: "key: Nome Real" -> nome = "Nome Real"
        first = parts[0]
        if ':' in first:
            entry['nome'] = first.split(':', 1)[1].strip()
        
        # Rest: "chave: valor" 
        for p in parts[1:]:
            if ':' in p:
                k, v = p.split(':', 1)
                k = k.strip().lower()
                v = v.strip().strip('"').strip("'")
                for num_field in ('hp', 'atk', 'def', 'dano', 'mana', 'cd', 'item_id', 'item_preco',
                                 'loot_id', 'id', 'peso'):
                    if k == num_field:
                        try: v = int(v) if '.' not in v else float(v)
                        except: pass
                        break
                entry[k] = v
        
        if entry and 'nome' in entry:
            plano[current].append(entry)

print(f"Sistema: {plano['sistema']}")
print(f"NPCs: {len(plano['npcs'])}")
for n in plano['npcs']:
    print(f"  {n.get('nome','?')} - saudacao: {str(n.get('saudacao',''))[:40]}")
print(f"Monsters: {len(plano['monsters'])}")
for m in plano['monsters']:
    print(f"  {m.get('nome','?')} - HP:{m.get('hp','?')} ATK:{m.get('atk','?')}")
print(f"Items: {len(plano['items'])}")
for i in plano['items']:
    print(f"  {i.get('nome','?')} - ID:{i.get('id','?')}")
print(f"Spells: {len(plano['spells'])}")
for s in plano['spells']:
    print(f"  {s.get('nome','?')} - Dano:{s.get('dano','?')}")
