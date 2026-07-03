#!/usr/bin/env python3
"""
Compara items.xml original vs traduzido e procura nos scripts Lua
referências a nomes de itens que mudaram. Gera um relatório de migração.
Uso: python migra_items.py items_original.xml items_traduzido.xml pasta_data [relatorio.txt]
"""

import xml.etree.ElementTree as ET
import os
import re
import sys

def read_xml_with_fallback(filepath):
    """Lê um ficheiro XML tentando UTF-8, depois Latin-1, e corrige ampersands."""
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            raw = f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin-1') as f:
            raw = f.read()
    # Corrigir ampersands solitários (comum em XML mal formado)
    raw = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', raw)
    return raw

def parse_items(xml_path):
    """Extrai um dicionário {nome: id} de um ficheiro items.xml."""
    raw = read_xml_with_fallback(xml_path)
    root = ET.fromstring(raw)
    items = {}
    for item in root.iter('item'):
        item_id = item.get('id')
        name_attr = item.get('name')
        if name_attr and item_id:
            items[name_attr] = item_id
    return items

def read_lua_file(filepath):
    """Lê um ficheiro Lua, tentando UTF-8 e Latin-1. Retorna as linhas ou None."""
    for enc in ('utf-8', 'latin-1'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.readlines()
        except (UnicodeDecodeError, Exception):
            continue
    return None

def main():
    if len(sys.argv) < 4:
        print("Uso: python migra_items.py items_original.xml items_traduzido.xml pasta_data [relatorio.txt]")
        return

    original_xml = sys.argv[1]
    traduzido_xml = sys.argv[2]
    data_folder = sys.argv[3]
    relatorio = sys.argv[4] if len(sys.argv) >= 5 else "relatorio_migracao.txt"

    print("A ler items originais...")
    orig = parse_items(original_xml)
    print(f"{len(orig)} itens no ficheiro original.")

    print("A ler items traduzidos...")
    trad = parse_items(traduzido_xml)
    print(f"{len(trad)} itens no ficheiro traduzido.")

    # Mapear alterações: nome_antigo -> nome_novo (se o ID coincidir)
    mudancas = {}
    for nome_antigo, item_id in orig.items():
        # Procurar um item com o mesmo ID no traduzido
        # Podemos optimizar criando um dicionário reverso: id -> nome_novo
        pass
    # Vamos construir o dicionário reverso para busca rápida
    id_to_novo = {trad[nome]: nome for nome in trad}
    for nome_antigo, item_id in orig.items():
        if item_id in id_to_novo:
            nome_novo = id_to_novo[item_id]
            if nome_novo != nome_antigo:
                mudancas[nome_antigo] = nome_novo

    print(f"{len(mudancas)} itens tiveram o nome alterado.")
    if not mudancas:
        print("Nenhuma alteração encontrada. Relatório vazio.")
        return

    # Construir uma lista de padrões regex pré-compilados para todos os nomes antigos
    escaped_names = [(re.escape(name), name) for name in mudancas.keys()]
    # Ordenar por comprimento decrescente para evitar matches parciais (ex.: "gem" vs "lesser gem")
    escaped_names.sort(key=lambda x: -len(x[0]))
    # Criar um único regex que captura qualquer um dos nomes
    pattern = re.compile(r'["\'](' + '|'.join(e[0] for e in escaped_names) + r')["\']')

    print(f"A percorrer scripts Lua em {data_folder}...")
    resultados = []
    lua_files = 0
    for root, dirs, files in os.walk(data_folder):
        for file in files:
            if not file.endswith('.lua'):
                continue
            lua_files += 1
            fullpath = os.path.join(root, file)
            lines = read_lua_file(fullpath)
            if lines is None:
                continue
            for num, line in enumerate(lines, 1):
                for match in pattern.finditer(line):
                    nome_antigo_encontrado = match.group(1)
                    # Verificar se o nome antigo existe no dicionário de mudanças
                    # (deveria sempre existir, mas por segurança)
                    if nome_antigo_encontrado in mudancas:
                        nome_novo = mudancas[nome_antigo_encontrado]
                        resultados.append((fullpath, num, nome_antigo_encontrado, nome_novo, line.rstrip()))

    # Escrever relatório
    with open(relatorio, 'w', encoding='utf-8') as f:
        f.write("Relatório de migração de nomes de itens nos scripts Lua\n")
        f.write("=" * 60 + "\n")
        f.write(f"Ficheiros Lua analisados: {lua_files}\n")
        f.write(f"Itens alterados: {len(mudancas)}\n")
        f.write(f"Ocorrências encontradas: {len(resultados)}\n\n")

        if not resultados:
            f.write("Nenhuma ocorrência encontrada. Nenhuma migração necessária.\n")
        else:
            for path, num, old, new, linha in resultados:
                f.write(f"\nFicheiro: {path}\n")
                f.write(f"Linha {num}: {linha.strip()}\n")
                f.write(f"  ❌ '{old}' -> ✅ '{new}'\n")

    print(f"Relatório guardado em {relatorio}.")
    print(f"Encontradas {len(resultados)} ocorrências para migrar.")

if __name__ == '__main__':
    main()