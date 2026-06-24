"""Verifica itens no items.xml."""
import re

with open(r"E:\Projeto MCR\Canary\data\items\items.xml", encoding="utf-8", errors="replace") as f:
    content = f.read()

for nome in ["War Hammer", "Espada de Fogo", "Fire Sword"]:
    matches = re.findall(f'name="{nome}"', content)
    print(f"{nome}: {len(matches)} ocorrencias")
    if matches:
        idx = content.find(f'name="{nome}"')
        start = content.rfind("<item", 0, idx)
        end = content.find("/>", idx)
        print(f"  Item: {content[start:end+2][:200]}")
    print()
