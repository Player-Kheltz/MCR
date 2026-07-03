#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converte entradas de loot do tipo { name = "..." } em ficheiros como custom_monster_loot.lua.
"""
import re, os, sys, xml.etree.ElementTree as ET

ITEMS_XML = "items_original.xml"
TARGET_FILES = [
    "data/scripts/systems/custom_monster_loot.lua",
    "data-canary/scripts/systems/custom_monster_loot.lua",
    "data-otservbr-global/scripts/systems/custom_monster_loot.lua",
]

def carregar_ids():
    tree = ET.parse(ITEMS_XML)
    root = tree.getroot()
    mapping = {}
    for item in root.iter('item'):
        name = item.get('name')
        iid = item.get('id')
        if name and iid:
            mapping[name] = int(iid)
            mapping[name.lower()] = int(iid)
    return mapping

def corrigir_ficheiro(fp, mapping):
    try:
        with open(fp, 'r', encoding='iso-8859-1') as f:
            conteudo = f.read()
    except:
        return False
    changed = False
    def repl(m):
        nonlocal changed
        nome = m.group(1)
        if nome in mapping:
            changed = True
            return f'{{ id = {mapping[nome]}'
        if nome.lower() in mapping:
            changed = True
            return f'{{ id = {mapping[nome.lower()]}'
        return m.group(0)
    novo = re.sub(r'\{\s*name\s*=\s*"([^"]+)"', repl, conteudo)
    if changed:
        with open(fp, 'w', encoding='iso-8859-1') as f:
            f.write(novo)
        return True
    return False

def main():
    if len(sys.argv) < 2:
        print("Uso: python 0-converter-custom-loot.py <raiz_servidor>")
        return
    root = sys.argv[1]
    mapping = carregar_ids()
    for rel in TARGET_FILES:
        fp = os.path.join(root, rel)
        if os.path.exists(fp):
            if corrigir_ficheiro(fp, mapping):
                print(f"✔ {fp}")

if __name__ == '__main__':
    main()