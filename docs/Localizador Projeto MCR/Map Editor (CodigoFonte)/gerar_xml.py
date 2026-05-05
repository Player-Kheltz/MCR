import os, re, sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

BASE = r"E:\Projeto MCR\Canary\data-canary"
MONSTERS_XML = "monsters.xml"
NPCS_XML = "npcs.xml"

def ler_latin1(path):
    with open(path, "r", encoding="latin-1") as f:
        return f.read()

# ---------- Monstros ----------
def extrair_monstro(conteudo):
    m = re.search(r'Game\.createMonsterType\s*\(\s*"([^"]*)"\s*\)', conteudo)
    if not m:
        return None, None, None
    nome = m.group(1)
    looktype = 0
    m2 = re.search(r'lookType\s*=\s*(\d+)', conteudo)
    if m2:
        looktype = int(m2.group(1))
    lookitem = 0
    m3 = re.search(r'lookTypeEx\s*=\s*(\d+)', conteudo)
    if m3:
        lookitem = int(m3.group(1))
    return nome, looktype, lookitem

def gerar_xml_monstro(nome, looktype, lookitem):
    monster = ET.Element("monster")
    monster.set("name", nome)
    look = ET.SubElement(monster, "look")
    if lookitem:
        look.set("item", str(lookitem))
    if looktype:
        look.set("type", str(looktype))
    return monster

# ---------- NPCs ----------
def extrair_nome_npc(conteudo):
    m = re.search(r'Game\.createNpcType\s*\(\s*"([^"]*)"\s*\)', conteudo)
    if m:
        return m.group(1)
    local_match = re.search(r'local\s+(\w+)\s*=\s*"([^"]+)"', conteudo)
    if local_match:
        var_name = local_match.group(1)
        nome = local_match.group(2)
        if re.search(rf'Game\.createNpcType\s*\(\s*{var_name}\s*\)', conteudo):
            return nome
    return None

def extrair_dados_npc(conteudo):
    dados = {"looktype": 0, "lookitem": 0, "lookhead": 0, "lookbody": 0, "looklegs": 0, "lookfeet": 0, "lookaddons": 0}
    bloco = re.search(r'outfit\s*=\s*\{([^}]+)\}', conteudo)
    if bloco:
        for campo in ["lookType", "lookHead", "lookBody", "lookLegs", "lookFeet", "lookAddons", "lookTypeEx"]:
            v = re.search(campo + r'\s*=\s*(\d+)', bloco.group(1))
            if v:
                if campo == "lookType":
                    dados["looktype"] = int(v.group(1))
                elif campo == "lookTypeEx":
                    dados["lookitem"] = int(v.group(1))
                elif campo == "lookHead":
                    dados["lookhead"] = int(v.group(1))
                elif campo == "lookBody":
                    dados["lookbody"] = int(v.group(1))
                elif campo == "lookLegs":
                    dados["looklegs"] = int(v.group(1))
                elif campo == "lookFeet":
                    dados["lookfeet"] = int(v.group(1))
                elif campo == "lookAddons":
                    dados["lookaddons"] = int(v.group(1))
    return dados

def gerar_xml_npc(nome, dados):
    npc = ET.Element("npc")
    npc.set("name", nome)
    look = ET.SubElement(npc, "look")
    if dados["lookitem"]:
        look.set("item", str(dados["lookitem"]))
    if dados["looktype"]:
        look.set("type", str(dados["looktype"]))
    if dados["lookhead"]:
        look.set("head", str(dados["lookhead"]))
    if dados["lookbody"]:
        look.set("body", str(dados["lookbody"]))
    if dados["looklegs"]:
        look.set("legs", str(dados["looklegs"]))
    if dados["lookfeet"]:
        look.set("feet", str(dados["lookfeet"]))
    if dados["lookaddons"]:
        look.set("addon", str(dados["lookaddons"]))
    return npc

def exportar_xml(elemento_raiz, nome_arquivo):
    # Gera string XML com declaração Latin‑1
    xml_string = ET.tostring(elemento_raiz, encoding='utf-8')
    # Substitui a declaração de encoding para ISO‑8859‑1
    pretty = minidom.parseString(xml_string).toprettyxml(indent="  ")
    pretty = pretty.replace('encoding="utf-8"', 'encoding="ISO-8859-1"')
    # Escreve o arquivo em Latin‑1
    with open(nome_arquivo, "w", encoding="latin-1") as f:
        f.write(pretty)

# ---------- Processamento ----------
monstros = []
npcs = []

for root, _, files in os.walk(BASE):
    for f in files:
        if not f.endswith(".lua"): continue
        path = os.path.join(root, f)
        try:
            conteudo = ler_latin1(path)
        except:
            continue

        nome_m, lt, li = extrair_monstro(conteudo)
        if nome_m:
            monstros.append((nome_m, lt, li))
            continue

        nome_npc = extrair_nome_npc(conteudo)
        if nome_npc:
            dados = extrair_dados_npc(conteudo)
            npcs.append((nome_npc, dados))

# Monsters
root_m = ET.Element("monsters")
for nome, lt, li in sorted(monstros, key=lambda x: x[0].lower()):
    root_m.append(gerar_xml_monstro(nome, lt, li))
exportar_xml(root_m, MONSTERS_XML)

# NPCs
root_n = ET.Element("npcs")
for nome, dados in sorted(npcs, key=lambda x: x[0].lower()):
    root_n.append(gerar_xml_npc(nome, dados))
exportar_xml(root_n, NPCS_XML)

print(f"Monstros: {len(monstros)}, NPCs: {len(npcs)}")