#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converte player:addItem("Nome", qtd) para player:addItem(ID, qtd).
Usa items_original.xml e procura case‑insensitive.
"""
import re, os, sys, xml.etree.ElementTree as ET

ITEMS_XML = "items_original.xml"
SCRIPT_DIRS = ["data", "data-canary", "data-otservbr-global"]
EXCLUDE_FILES = {'items.xml', 'titles.lua', 'achievements.lua', 'config.lua'}

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

def converter_ficheiro(fp, mapping):
    try:
        with open(fp, 'r', encoding='iso-8859-1') as f:
            conteudo = f.read()
    except:
        with open(fp, 'r', encoding='utf-8') as f:
            conteudo = f.read()
    changed = False
    def repl(m):
        nonlocal changed
        nome = m.group(1)
        if nome in mapping:
            changed = True
            return f'addItem({mapping[nome]}, '
        if nome.lower() in mapping:
            changed = True
            return f'addItem({mapping[nome.lower()]}, '
        return m.group(0)
    novo = re.sub(r'addItem\(\s*"([^"]+)"\s*,', repl, conteudo)
    if changed:
        with open(fp, 'w', encoding='iso-8859-1') as f:
            f.write(novo)
        return True
    return False

def main():
    if len(sys.argv) < 2:
        print("Uso: python 0-converter-additem.py <raiz_servidor>")
        return
    root = sys.argv[1]
    if not os.path.exists(ITEMS_XML):
        print(f"ERRO: {ITEMS_XML} não encontrado.")
        return
    mapping = carregar_ids()
    print(f'{len(mapping)} itens carregados.')
    for base in SCRIPT_DIRS:
        full = os.path.join(root, base)
        if not os.path.exists(full):
            continue
        for dirpath, _, filenames in os.walk(full):
            for fn in filenames:
                if fn in EXCLUDE_FILES or not fn.endswith('.lua'):
                    continue
                fp = os.path.join(dirpath, fn)
                if converter_ficheiro(fp, mapping):
                    print(f'✔ {fp}')

if __name__ == '__main__':
    main()