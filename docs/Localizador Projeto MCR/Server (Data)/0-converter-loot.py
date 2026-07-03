#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converte loots de monstros de 'name' para 'id' apenas dentro de monster.loot.
Mantém os ficheiros Lua em ISO‑8859‑1.
"""

import re, os, sys, xml.etree.ElementTree as ET

ITEMS_XML = "items_original.xml"
MONSTER_DIRS = ["data/monster", "data-canary/monster", "data-otservbr-global/monster"]

def carregar_ids():
    tree = ET.parse(ITEMS_XML)
    root = tree.getroot()
    name_to_id = {}
    for item in root.iter('item'):
        name = item.get('name')
        iid = item.get('id')
        if name and iid:
            name_to_id[name] = int(iid)
            name_to_id[name.lower()] = int(iid)
    return name_to_id

def ler_arquivo(path):
    try:
        with open(path, 'r', encoding='iso-8859-1') as f:
            return f.read()
    except:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

def substituir_nome_por_id(conteudo, name_to_id):
    linhas = conteudo.splitlines(True)
    resultado = []
    dentro_loot = False
    loot_brace_count = 0  # contagem de { e } dentro do monster.loot

    for linha in linhas:
        # Detecta o início de monster.loot = {
        if not dentro_loot and re.search(r'\bmonster\.loot\s*=\s*\{', linha):
            dentro_loot = True
            loot_brace_count = 0  # vamos contar a partir da próxima chave

        if dentro_loot:
            # Conta as chaves na linha actual
            loot_brace_count += linha.count('{') - linha.count('}')
            # Se chegou a zero (fechou a tabela monster.loot), sai do bloco
            if loot_brace_count <= 0:
                dentro_loot = False

            # Só substitui se estiver DENTRO do bloco
            def replacer(match):
                nome = match.group(1)
                if nome in name_to_id:
                    return f'{{ id = {name_to_id[nome]}'
                if nome.lower() in name_to_id:
                    return f'{{ id = {name_to_id[nome.lower()]}'
                # Se não encontrou, deixa como está (não converte)
                return match.group(0)

            linha = re.sub(r'\{\s*name\s*=\s*"([^"]+)"', replacer, linha)
        # else: fora do bloco, não mexe

        resultado.append(linha)
    return ''.join(resultado)

def main():
    if len(sys.argv) < 2:
        print("Uso: python 0-converter-loot.py <raiz_servidor>")
        return
    root = sys.argv[1]
    if not os.path.exists(ITEMS_XML):
        print(f"ERRO: {ITEMS_XML} não encontrado. Faça uma cópia do items.xml original com:\n  copy data\\items\\items.xml {ITEMS_XML}")
        return
    name_to_id = carregar_ids()
    print(f'{len(name_to_id)} itens carregados (incl. lowercase).')
    for base in MONSTER_DIRS:
        full = os.path.join(root, base)
        if not os.path.exists(full):
            continue
        for dirpath, _, filenames in os.walk(full):
            for fn in filenames:
                if fn.endswith(('.lua', '.xml')):
                    fp = os.path.join(dirpath, fn)
                    conteudo = ler_arquivo(fp)
                    novo = substituir_nome_por_id(conteudo, name_to_id)
                    if novo != conteudo:
                        enc = 'iso-8859-1' if fn.endswith('.lua') else 'utf-8'
                        with open(fp, 'w', encoding=enc) as f:
                            f.write(novo)
                        print(f'✔ {fp}')

if __name__ == '__main__':
    main()