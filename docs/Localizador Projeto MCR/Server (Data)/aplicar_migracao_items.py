#!/usr/bin/env python3
"""
Aplica a migração de nomes de itens nos scripts Lua com base na comparação
entre items.xml original e traduzido. Ignora falsos positivos como "table", "ice", etc.
Uso: python aplicar_migracao_items.py items_original.xml items_traduzido.xml pasta_data
"""

import xml.etree.ElementTree as ET
import os
import re
import sys

# ----------------------------------------------------------------------
# Palavras que NUNCA devem ser substituídas (falsos positivos comuns)
# ----------------------------------------------------------------------
FALSOS_POSITIVOS = {
    "table", "unknown", "can", "staff", "ice", "crystal", "armor",
    "skull", "arrow", "name", "type", "id", "count", "true", "false",
    "nil", "self", "local", "function", "return", "end", "if", "then",
    "else", "elseif", "for", "do", "while", "repeat", "until", "in",
    "pairs", "ipairs", "next", "string", "number", "boolean",
}

# ----------------------------------------------------------------------
# Leitura de XML com fallback de encoding e correção de ampersands
# ----------------------------------------------------------------------
def read_xml_with_fallback(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            raw = f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin-1') as f:
            raw = f.read()
    raw = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', raw)
    return raw

def parse_items(xml_path):
    """Extrai {nome: id} de items.xml."""
    raw = read_xml_with_fallback(xml_path)
    root = ET.fromstring(raw)
    items = {}
    for item in root.iter('item'):
        item_id = item.get('id')
        name_attr = item.get('name')
        if name_attr and item_id:
            items[name_attr] = item_id
    return items

# ----------------------------------------------------------------------
# Leitura e escrita de ficheiros Lua com encoding seguro
# ----------------------------------------------------------------------
def read_lua_file(filepath):
    """Lê um ficheiro Lua tentando UTF-8 e Latin-1."""
    for enc in ('utf-8', 'latin-1'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.read(), enc
        except (UnicodeDecodeError, Exception):
            continue
    return None, None

def write_lua_file(filepath, content, original_encoding):
    """Escreve o ficheiro Lua mantendo o encoding original (ou UTF-8 como fallback)."""
    enc = original_encoding if original_encoding else 'utf-8'
    with open(filepath, 'w', encoding=enc) as f:
        f.write(content)

# ----------------------------------------------------------------------
# Substituição segura de nomes de itens numa string Lua
# ----------------------------------------------------------------------
def substituir_nomes(texto, mudancas):
    """
    Substitui no texto as ocorrências dos nomes antigos (entre aspas)
    pelos nomes novos, desde que não sejam falsos positivos.
    Retorna (texto_modificado, numero_substituicoes).
    """
    # Ordenar os nomes antigos por comprimento decrescente para evitar
    # substituições parciais (ex.: "gem" vs "lesser gem")
    nomes_ordenados = sorted(mudancas.keys(), key=lambda n: -len(n))

    # Construir um regex que captura qualquer nome antigo entre aspas
    padrao = re.compile(
        r'(["\'])' + 
        '(' + '|'.join(re.escape(nome) for nome in nomes_ordenados) + ')' +
        r'\1'
    )

    def repl(m):
        nome_encontrado = m.group(2)
        # Só substitui se não for falso positivo
        if nome_encontrado.lower() in FALSOS_POSITIVOS:
            return m.group(0)  # mantém inalterado
        novo_nome = mudancas.get(nome_encontrado)
        if novo_nome:
            return m.group(1) + novo_nome + m.group(1)
        return m.group(0)

    texto_modificado, n = padrao.subn(repl, texto)
    return texto_modificado, n

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    if len(sys.argv) < 4:
        print("Uso: python aplicar_migracao_items.py items_original.xml items_traduzido.xml pasta_data")
        return

    original_xml = sys.argv[1]
    traduzido_xml = sys.argv[2]
    data_folder = sys.argv[3]

    print("A ler items originais...")
    orig = parse_items(original_xml)
    print(f"{len(orig)} itens no ficheiro original.")

    print("A ler items traduzidos...")
    trad = parse_items(traduzido_xml)
    print(f"{len(trad)} itens no ficheiro traduzido.")

    # Construir mapeamento nome_antigo -> nome_novo (mesmo ID, nome diferente)
    id_to_novo = {trad[nome]: nome for nome in trad}
    mudancas = {}
    for nome_antigo, item_id in orig.items():
        if item_id in id_to_novo:
            nome_novo = id_to_novo[item_id]
            if nome_novo != nome_antigo:
                mudancas[nome_antigo] = nome_novo

    print(f"{len(mudancas)} itens tiveram o nome alterado.")
    if not mudancas:
        print("Nenhuma alteração a fazer.")
        return

    # Excluir da lista de mudanças os falsos positivos (para não gerar substituições perigosas)
    mudancas_filtradas = {
        k: v for k, v in mudancas.items()
        if k.lower() not in FALSOS_POSITIVOS
    }
    print(f"{len(mudancas_filtradas)} após filtrar falsos positivos.")

    # Percorrer scripts Lua
    total_substituicoes = 0
    ficheiros_alterados = 0
    for root, dirs, files in os.walk(data_folder):
        for file in files:
            if not file.endswith('.lua'):
                continue
            fullpath = os.path.join(root, file)
            conteudo, encoding = read_lua_file(fullpath)
            if conteudo is None:
                print(f"⚠️ Não foi possível ler {fullpath}")
                continue

            novo_conteudo, n = substituir_nomes(conteudo, mudancas_filtradas)
            if n > 0:
                write_lua_file(fullpath, novo_conteudo, encoding)
                print(f"✔ {fullpath} – {n} substituições")
                total_substituicoes += n
                ficheiros_alterados += 1

    print(f"\n🎉 Total de substituições: {total_substituicoes}")
    print(f"📁 Ficheiros alterados: {ficheiros_alterados}")

if __name__ == '__main__':
    main()