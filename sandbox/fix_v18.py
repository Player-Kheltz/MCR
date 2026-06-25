"""Fix V18 variable initialization"""
with open(r'E:\Projeto MCR\sandbox\mcr_crew_v18.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix: initialize qualidade before first use
c = c.replace(
    "        lore_npc = gerar_lore(ia, 'NPC', vals_npc['nome'])\n        if lore_npc:",
    "        lore_npc = gerar_lore(ia, 'NPC', vals_npc['nome'])\n        qualidade = Quality.pontuar_texto(str(lore_npc)) if lore_npc else 0\n        if lore_npc:"
)

# Fix same for item
c = c.replace(
    "        lore_item = gerar_lore(ia, 'ITEM', vals_item['nome'])\n        qual_item = Quality.pontuar_texto(str(lore_item))",
    "        lore_item = gerar_lore(ia, 'ITEM', vals_item['nome'])\n        qual_item = Quality.pontuar_texto(str(lore_item)) if lore_item else 0"
)

# Fix same for quest
c = c.replace(
    "    lore_quest = gerar_lore(ia, 'QUEST', vals_quest['nome'],\n        f\"NPC: {vals_npc['nome']}, Itens: {', '.join(itens_gerados)}\")\n    qual_quest = Quality.pontuar_texto(str(lore_quest))",
    "    lore_quest = gerar_lore(ia, 'QUEST', vals_quest['nome'], f\"NPC: {vals_npc['nome']}, Itens: {', '.join(itens_gerados)}\")\n    qual_quest = Quality.pontuar_texto(str(lore_quest)) if lore_quest else 0"
)

# Also fix the NPC quality append line  
c = c.replace(
    "    resultados.append(('NPC', vals_npc['nome'], qualidade))\n    if 'PERSONALIDADE' in lore_npc:",
    "    resultados.append(('NPC', vals_npc['nome'], qualidade))\n    if lore_npc and 'PERSONALIDADE' in lore_npc:"
)

with open(r'E:\Projeto MCR\sandbox\mcr_crew_v18.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'v18.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error: {e}')
