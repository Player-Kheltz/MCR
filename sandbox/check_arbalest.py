"""Verifica Arbalest no items.xml."""
import re, os

path = r"E:\Projeto MCR\Canary\data\items\items.xml"
with open(path, encoding="utf-8", errors="replace") as f:
    content = f.read()

# Procura Arbalest (case insensitive)
for m in re.finditer(r'name="([^"]*Arbalest[^"]*)"', content, re.IGNORECASE):
    name = m.group(1)
    idx = m.start()
    item_start = content.rfind("<item", 0, idx)
    id_match = re.search(r'id="(\d+)"', content[item_start:idx])
    item_id = id_match.group(1) if id_match else "?"
    print(f'Item: id={item_id}, name="{name}"')

# Procura por "Arbalest" sem case
matches = [m for m in re.finditer(r'name="([^"]*)"', content) if "arbalest" in m.group(1).lower()]
if not matches:
    print("Arbalest NAO encontrado no items.xml")
    # Procura item 5803
    for m in re.finditer(r'<item id="5803"', content):
        end = content.find("/>", m.start())
        print(f"Item id 5803: {content[m.start():end+2]}")
else:
    for m in matches:
        item_start = content.rfind("<item", 0, m.start())
        id_match = re.search(r'id="(\d+)"', content[item_start:m.start()])
        item_id = id_match.group(1) if id_match else "?"
        print(f'Item: id={item_id}, name="{m.group(1)}"')
