#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de monsters.xml e npcs.xml para o RME a partir dos scripts Lua do Canary.
Percorre a pasta data-canary, extrai dados de monstros e NPCs e gera os XMLs.
Uso: python gerar_xml_rme.py [--base "E:\Projeto MCR\Canary\data-canary"]
"""

import os
import re
import sys
import argparse
from xml.dom import minidom
import xml.etree.ElementTree as ET

# ------------------------------------------------------------
# CONFIGURAÇÕES PADRÃO
# ------------------------------------------------------------
DEFAULT_BASE = r"E:\Projeto MCR\Canary\data-canary"
MONSTERS_XML = "monsters.xml"
NPCS_XML = "npcs.xml"

# ------------------------------------------------------------
# FUNÇÕES AUXILIARES DE LEITURA
# ------------------------------------------------------------

def ler_arquivo(caminho):
    """Tenta ler um arquivo Lua como Latin-1 (padrão do Canary) e depois UTF-8."""
    for enc in ('latin-1', 'utf-8'):
        try:
            with open(caminho, 'r', encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    return ""


def extrair_dados_monstro(conteudo):
    """
    Procura pela assinatura 'Game.createMonsterType("Nome")' e
    pelo lookType dentro da tabela 'monster.outfit'.
    Retorna (nome, looktype) ou (None, None).
    """
    # 1. Nome do monstro
    match = re.search(r'Game\.createMonsterType\s*\(\s*"([^"]*)"\s*\)', conteudo)
    if not match:
        return None, None
    nome = match.group(1)

    # 2. lookType dentro de monster.outfit
    match_outfit = re.search(r'lookType\s*=\s*(\d+)', conteudo)
    if not match_outfit:
        return nome, 0  # sem looktype definido, usa 0
    looktype = int(match_outfit.group(1))
    return nome, looktype


def extrair_dados_npc(conteudo):
    """
    Procura por 'Game.createNpcType("Nome")' e os campos do outfit
    dentro de 'npcConfig.outfit' ou 'outfit = {'.
    Retorna dicionário com name, looktype, lookhead, lookbody, looklegs, lookfeet, lookaddons,
    ou None se não for um NPC.
    """
    match = re.search(r'Game\.createNpcType\s*\(\s*"([^"]*)"\s*\)', conteudo)
    if not match:
        return None
    nome = match.group(1)

    dados = {
        'name': nome,
        'looktype': 0,
        'lookhead': 0,
        'lookbody': 0,
        'looklegs': 0,
        'lookfeet': 0,
        'lookaddons': 0
    }

    # Encontra bloco do outfit (pode estar em npcConfig.outfit ou direto em outfit = {)
    bloco = re.search(r'outfit\s*=\s*\{([^}]+)\}', conteudo)
    if not bloco:
        return dados  # sem outfit, retorna com zeros

    campos = ['lookType', 'lookHead', 'lookBody', 'lookLegs', 'lookFeet', 'lookAddons']
    for campo in campos:
        m = re.search(campo + r'\s*=\s*(\d+)', bloco.group(1))
        if m:
            chave = campo.lower()
            if chave == 'looktype':
                chave = 'looktype'
            dados[chave] = int(m.group(1))

    return dados


def xml_pretty(element):
    """Retorna string XML formatada."""
    rough = ET.tostring(element, 'utf-8')
    return minidom.parseString(rough).toprettyxml(indent="  ")


# ------------------------------------------------------------
# LÓGICA PRINCIPAL
# ------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Gera XMLs de monstros e NPCs para o RME.")
    parser.add_argument('--base', default=DEFAULT_BASE, help="Caminho da pasta data-canary")
    parser.add_argument('--monsters-out', default=MONSTERS_XML, help="Arquivo de saída monsters.xml")
    parser.add_argument('--npcs-out', default=NPCS_XML, help="Arquivo de saída npcs.xml")
    args = parser.parse_args()

    base = args.base
    if not os.path.isdir(base):
        print(f"[ERRO] Pasta base não encontrada: {base}")
        sys.exit(1)

    monsters = []
    npcs = []
    total_lua = 0

    print(f"[INFO] Varrendo {base} ...")
    for raiz, dirs, files in os.walk(base):
        for f in files:
            if not f.lower().endswith('.lua'):
                continue
            total_lua += 1
            caminho = os.path.join(raiz, f)
            conteudo = ler_arquivo(caminho)
            if not conteudo:
                continue

            # Tenta extrair monstro
            nome_monstro, looktype = extrair_dados_monstro(conteudo)
            if nome_monstro:
                monsters.append((nome_monstro, looktype))
                continue  # se é monstro, não é NPC

            # Tenta extrair NPC
            dados_npc = extrair_dados_npc(conteudo)
            if dados_npc:
                npcs.append(dados_npc)

    print(f"[INFO] {total_lua} arquivos .lua processados.")
    print(f"[INFO] Monstros encontrados: {len(monsters)}")
    print(f"[INFO] NPCs encontrados: {len(npcs)}")

    # --------------------------------------------------------
    # GERA monsters.xml
    # --------------------------------------------------------
    root_monsters = ET.Element('monsters')
    for nome, looktype in sorted(monsters, key=lambda x: x[0].lower()):
        ET.SubElement(root_monsters, 'monster', {
            'name': nome,
            'looktype': str(looktype)
        })

    with open(args.monsters_out, 'w', encoding='utf-8') as f:
        f.write(xml_pretty(root_monsters))
    print(f"[OK] {args.monsters_out} gerado.")

    # --------------------------------------------------------
    # GERA npcs.xml
    # --------------------------------------------------------
    root_npcs = ET.Element('npcs')
    for d in sorted(npcs, key=lambda x: x['name'].lower()):
        ET.SubElement(root_npcs, 'npc', {
            'name': d['name'],
            'looktype': str(d.get('looktype', 0)),
            'lookitem': '0',  # sempre 0, não extraível de Lua
            'lookaddon': str(d.get('lookaddons', 0)),
            'lookhead': str(d.get('lookhead', 0)),
            'lookbody': str(d.get('lookbody', 0)),
            'looklegs': str(d.get('looklegs', 0)),
            'lookfeet': str(d.get('lookfeet', 0))
        })

    with open(args.npcs_out, 'w', encoding='utf-8') as f:
        f.write(xml_pretty(root_npcs))
    print(f"[OK] {args.npcs_out} gerado.")


if __name__ == '__main__':
    main()