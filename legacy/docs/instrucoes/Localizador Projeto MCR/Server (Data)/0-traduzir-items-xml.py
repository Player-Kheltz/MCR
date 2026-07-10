#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Traduz o items.xml (nome, plural, descrição) com artigo inteligente e dicionário MCR.
Para itens sem plural, gera o plural via API a partir do singular em inglês.
Nomes de equipamentos são forçados ao singular.
Grava em ISO‑8859‑1.
"""

import json, time, sys, shutil, re, xml.etree.ElementTree as ET
from pathlib import Path
from deep_translator import GoogleTranslator
from mcr_dict import MCR_CORRECTIONS

# ===== CONFIGURAÇÃO =====
BACKUP_ORIGINAL = "items_original.xml"
CACHE_ARQUIVO    = "translation_cache.json"

SEPARADOR        = " ||| "
MAX_CHARS        = 4800
DELAY            = 0.02
TENTATIVAS       = 3
TIMEOUT          = 25
USAR_CONCATENACAO = True

# ===== TIMEOUT GLOBAL =====
import requests
original_get = requests.get
requests.get = lambda *a, **kw: original_get(*a, timeout=TIMEOUT, **kw)
original_send = requests.Session.send
def patched_send(self, req, **kw):
    kw.setdefault('timeout', TIMEOUT)
    return original_send(self, req, **kw)
requests.Session.send = patched_send

# ===== CAPITALIZAÇÃO =====
LOWERCASE_WORDS = {'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'no', 'na',
                   'para', 'com', 'sem', 'por', 'ou', 'a', 'o', 'as', 'os'}

def title_case_pt(text):
    if not text: return text
    words = text.split()
    result = []
    for i, w in enumerate(words):
        if i == 0 or i == len(words)-1:
            result.append(w.capitalize())
        elif w.lower() in LOWERCASE_WORDS:
            result.append(w.lower())
        else:
            result.append(w.capitalize())
    return ' '.join(result)

# ===== GÉNERO DO SUBSTANTIVO PRINCIPAL =====
def genero_principal(nome):
    stopwords = {'a', 'o', 'as', 'os', 'de', 'da', 'do', 'das', 'dos',
                 'e', 'para', 'com', 'em', 'no', 'na'}
    palavras = nome.lower().split()
    principal = palavras[0]
    for p in palavras:
        if p not in stopwords:
            principal = p
            break
    if principal.endswith(('a', 'as', 'ção', 'ções', 'dade', 'gem')):
        return 'f'
    return 'm'

def artigo_para(nome):
    return 'uma' if genero_principal(nome) == 'f' else 'um'

# ===== SINGULARIZAÇÃO PARA EQUIPAMENTOS =====
def singular_pt(palavra):
    """Converte uma palavra ou expressão do plural para o singular, de forma heurística."""
    if not palavra:
        return palavra
    # Divide em palavras, aplica singular na primeira palavra significativa
    words = palavra.split()
    if not words:
        return palavra
    # Encontra o índice do primeiro substantivo (ignorar artigos/preposições)
    first = 0
    stopwords = {'a', 'o', 'as', 'os', 'de', 'da', 'do', 'das', 'dos', 'e', 'para', 'com', 'em', 'no', 'na'}
    for i, w in enumerate(words):
        if w.lower() not in stopwords:
            first = i
            break
    # Aplica regras de singular no primeiro substantivo
    w = words[first]
    lower = w.lower()
    # Plurais terminados em "ões" -> "ão"
    if lower.endswith('ões'):
        w = w[:-3] + 'ão'
    # Plurais terminados em "ães" -> "ão" (ex.: pães -> pão) mas pode ser "ães" -> "ão"
    elif lower.endswith('ães'):
        w = w[:-3] + 'ão'
    # Plurais terminados em "ais" -> "al" (ex.: jornais -> jornal)
    elif lower.endswith('ais'):
        w = w[:-3] + 'al'
    # Plurais terminados em "éis" -> "el" (ex.: papéis -> papel)
    elif lower.endswith('éis'):
        w = w[:-3] + 'el'
    # Plurais terminados em "ois" -> "ol" (ex.: lençóis -> lençol)
    elif lower.endswith('ois'):
        w = w[:-3] + 'ol'
    # Plurais terminados em "zes" -> "z" (ex.: raízes -> raiz)
    elif lower.endswith('zes'):
        w = w[:-3] + 'z'
    # Plurais terminados em "res" -> "r" (ex.: mares -> mar)
    elif lower.endswith('res'):
        w = w[:-3] + 'r'
    # Plurais terminados em "ses" -> "s" (ex.: meses -> mês)
    elif lower.endswith('ses'):
        w = w[:-3] + 's'
    # Plurais terminados em "gens" -> "gem" (ex.: imagens -> imagem)
    elif lower.endswith('gens'):
        w = w[:-4] + 'gem'
    # Plurais terminados em "ns" -> "m" (ex.: viagens -> viagem) - cuidado, pode ser "n"
    elif lower.endswith('ns'):
        w = w[:-2] + 'm'
    # Caso geral: se termina em "s" e não é monossílabo, remove o "s"
    elif lower.endswith('s') and len(w) > 1:
        w = w[:-1]
    # Atualiza a palavra na lista
    words[first] = w
    return ' '.join(words)

# ===== PLURAL EM INGLÊS (PARA GERAR VIA API) =====
def plural_en(word):
    """Gera o plural de uma palavra em inglês usando regras básicas."""
    if not word:
        return word
    w = word.strip()
    lower = w.lower()
    # Exceções comuns (pode ser expandido)
    exceptions = {
        'man': 'men', 'woman': 'women', 'child': 'children', 'foot': 'feet',
        'tooth': 'teeth', 'mouse': 'mice', 'goose': 'geese', 'ox': 'oxen',
        'die': 'dice', 'fish': 'fishes', 'sheep': 'sheep', 'deer': 'deer'
    }
    if lower in exceptions:
        return exceptions[lower] if exceptions[lower] != w else w
    # Palavras compostas (ex.: "crafting rune" -> "crafting runes")
    parts = w.rsplit(' ', 1)
    if len(parts) > 1:
        return parts[0] + ' ' + plural_en(parts[1])
    # Regras comuns
    if lower.endswith(('s', 'x', 'z', 'sh', 'ch')):
        return w + 'es'
    if lower.endswith('y') and w[-2] not in 'aeiou':
        return w[:-1] + 'ies'
    if lower.endswith('f'):
        return w[:-1] + 'ves'
    if lower.endswith('fe'):
        return w[:-2] + 'ves'
    return w + 's'

# ===== CACHE =====
def carregar_cache():
    if Path(CACHE_ARQUIVO).exists():
        with open(CACHE_ARQUIVO, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def salvar_cache(cache):
    with open(CACHE_ARQUIVO, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

# ===== EXTRAÇÃO DO XML (agora com tipo primário) =====
def extrair_textos(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    nomes_unicos = []
    plurais_unicos = []
    descs_unicos = []
    str_idx_name = {}
    str_idx_plural = {}
    str_idx_desc = {}
    itens = []

    for item in root.iter('item'):
        nome = item.get('name')
        if nome and "RESERVED" not in nome and "DEPRECATED" not in nome:
            if nome not in str_idx_name:
                str_idx_name[nome] = len(nomes_unicos)
                nomes_unicos.append(nome)
            name_idx = str_idx_name[nome]
        else:
            name_idx = None

        plural = item.get('plural')
        if plural and "RESERVED" not in plural and "DEPRECATED" not in plural:
            if plural not in str_idx_plural:
                str_idx_plural[plural] = len(plurais_unicos)
                plurais_unicos.append(plural)
            plural_idx = str_idx_plural[plural]
        else:
            plural_idx = None   # será gerado depois

        desc_elem = item.find('./attribute[@key="description"]')
        desc_text = desc_elem.get('value') if desc_elem is not None else None
        if desc_text:
            if desc_text not in str_idx_desc:
                str_idx_desc[desc_text] = len(descs_unicos)
                descs_unicos.append(desc_text)
            desc_idx = str_idx_desc[desc_text]
        else:
            desc_idx = None

        # Tipo primário para correção de singular/plural
        primary_type = item.get('primarytype') or ''
        itens.append({
            "elem": item,
            "name_idx": name_idx,
            "plural_idx": plural_idx,
            "desc_idx": desc_idx,
            "type": primary_type
        })

    return {
        "names": nomes_unicos,
        "plurals": plurais_unicos,
        "descs": descs_unicos,
        "itens": itens
    }

# ===== MOTOR DE TRADUÇÃO (mesmo código anterior) =====
def montar_lotes_concatenacao(textos):
    lotes, atual, chars = [], [], 0
    for txt in textos:
        extra = len(txt) + (len(SEPARADOR) if atual else 0)
        if atual and chars + extra > MAX_CHARS:
            lotes.append(atual); atual, chars = [], 0
        atual.append(txt)
        chars += len(txt) + (len(SEPARADOR) if len(atual) > 1 else 0)
    if atual: lotes.append(atual)
    return lotes

def traduzir_lote_concatenado(lote, tradutor, cache):
    texto = SEPARADOR.join(lote)
    for tent in range(TENTATIVAS):
        try:
            res = tradutor.translate(texto)
            if res is None: continue
            partes = res.split(SEPARADOR)
            if len(partes) == len(lote):
                for orig, trad in zip(lote, partes): cache[orig] = trad.strip()
                salvar_cache(cache)
                return {orig: trad.strip() for orig, trad in zip(lote, partes)}
            partes_alt = [p.strip() for p in res.split("|") if p.strip()]
            if len(partes_alt) == len(lote):
                for orig, trad in zip(lote, partes_alt): cache[orig] = trad.strip()
                salvar_cache(cache)
                return {orig: trad.strip() for orig, trad in zip(lote, partes_alt)}
            print("   ⚠️ concat falhou, fallback tradicional...")
            break
        except Exception as e:
            print(f"   ⚠️ erro concat: {e}")
            time.sleep(2 ** tent)
    return traduzir_lote_tradicional(lote, tradutor, cache)

def traduzir_lote_tradicional(lote, tradutor, cache):
    trads = {}
    for orig in lote:
        if orig in cache:
            trads[orig] = cache[orig]; continue
        trad = None
        for tent in range(TENTATIVAS):
            try:
                trad = tradutor.translate(orig)
                if trad: trad = trad.strip(); break
            except Exception as e:
                print(f"   ⚠️ erro '{orig}': {e}")
                time.sleep(2 ** tent)
        if trad:
            cache[orig] = trad; trads[orig] = trad
        else:
            cache[orig] = orig; trads[orig] = orig
        salvar_cache(cache)
        time.sleep(DELAY)
    return trads

def traduzir_todas(textos, descricao, cache):
    pendentes = [t for t in textos if t not in cache]
    traducoes = {t: cache[t] for t in textos if t in cache}
    if not pendentes:
        print(f"✅ {descricao}: todas em cache.")
        return traducoes
    print(f"✅ {descricao}: {len(textos)-len(pendentes)} em cache, {len(pendentes)} a traduzir.")
    tradutor = GoogleTranslator(source='en', target='pt')
    lotes = montar_lotes_concatenacao(pendentes) if USAR_CONCATENACAO else [[t] for t in pendentes]
    for lote in lotes:
        if USAR_CONCATENACAO and len(lote) > 1:
            trads = traduzir_lote_concatenado(lote, tradutor, cache)
        else:
            trads = traduzir_lote_tradicional(lote, tradutor, cache)
        traducoes.update(trads)
        print(f"   Progresso: {len(traducoes)}/{len(textos)}")
        time.sleep(DELAY)
    return traducoes

# ===== MAIN =====
def main():
    inicio = time.time()

    if len(sys.argv) < 2:
        arquivo = "items/items.xml"
    else:
        arquivo = sys.argv[1]

    if not Path(arquivo).exists():
        print(f"❌ Ficheiro '{arquivo}' não encontrado.")
        sys.exit(1)

    if not Path(BACKUP_ORIGINAL).exists():
        shutil.copy(arquivo, BACKUP_ORIGINAL)
        print(f"💾 Backup criado: {BACKUP_ORIGINAL}")

    dados = extrair_textos(arquivo)
    nomes   = dados["names"]
    descs   = dados["descs"]
    itens   = dados["itens"]

    # ----- Tratar plurais: gerar plurais em inglês para itens sem plural -----
    plurais_originais = dados["plurals"]   # plurais já existentes no XML
    # Coletar plurais gerados (inglês) para itens sem plural
    generated_plurals_en = []
    for item_info in itens:
        if item_info["plural_idx"] is None and item_info["name_idx"] is not None:
            singular_en = dados["names"][item_info["name_idx"]]
            plural_en_str = plural_en(singular_en)
            if plural_en_str != singular_en:   # não adiciona se for igual
                generated_plurals_en.append(plural_en_str)

    # Remover duplicatas
    generated_plurals_en = list(set(generated_plurals_en))
    # Adicionar aos plurais existentes para tradução
    todos_plurais_en = plurais_originais + generated_plurals_en
    # Remover duplicatas com os originais (caso algum coincida)
    todos_plurais_en = list(set(todos_plurais_en))

    print(f"📊 {len(nomes)} nomes, {len(plurais_originais)} plurais originais, {len(generated_plurals_en)} plurais gerados, {len(descs)} descrições.")

    # 3. Cache + MCR (com minúsculas)
    cache = carregar_cache()
    for eng, pt in MCR_CORRECTIONS.items():
        cache[eng] = pt
        cache[eng.lower()] = pt
    salvar_cache(cache)

    # 4. Traduzir
    trads_nomes   = traduzir_todas(nomes,   "nomes",   cache)
    trads_plurais = traduzir_todas(todos_plurais_en, "plurais", cache)
    trads_descs   = traduzir_todas(descs,   "descrições", cache)
    salvar_cache(cache)

    # 5. Capitalização + MCR forçado
    for nome, trad in trads_nomes.items():
        trad = title_case_pt(trad)
        if nome in MCR_CORRECTIONS:
            trad = MCR_CORRECTIONS[nome]
        elif nome.lower() in MCR_CORRECTIONS:
            trad = MCR_CORRECTIONS[nome.lower()]
        trads_nomes[nome] = trad

    for plural, trad in trads_plurais.items():
        trad = title_case_pt(trad)
        if plural in MCR_CORRECTIONS:
            trad = MCR_CORRECTIONS[plural]
        elif plural.lower() in MCR_CORRECTIONS:
            trad = MCR_CORRECTIONS[plural.lower()]
        trads_plurais[plural] = trad

    # 6. Aplicar no XML
    tree = ET.parse(arquivo)
    root = tree.getroot()

    # Tipos de equipamento que forçam o singular
    equip_types = {'armor', 'helmet', 'legs', 'shield', 'boots', 'sword', 'axe', 'club', 'bow', 'crossbow', 'wand', 'rod', 'spellbook', 'ring', 'amulet', 'necklace', 'touches'}   # 'touches' para luvas? 

    for item_info, elem in zip(itens, root.iter('item')):
        # Nome singular
        if item_info["name_idx"] is not None:
            nome_orig = dados["names"][item_info["name_idx"]]
            nome_trad = trads_nomes.get(nome_orig, nome_orig)
            artigo = artigo_para(nome_trad)

            # Se for equipamento, forçar singular
            if item_info["type"] in equip_types:
                nome_trad = singular_pt(nome_trad)

            elem.set('name', nome_trad)
            elem.set('article', artigo)

        # Plural
        if item_info["plural_idx"] is not None:
            # Já existia plural original
            plural_orig = dados["plurals"][item_info["plural_idx"]]
            plural_trad = trads_plurais.get(plural_orig, plural_orig)
        else:
            # Gerar a partir do singular em inglês
            if item_info["name_idx"] is not None:
                singular_en = dados["names"][item_info["name_idx"]]
                plural_en_str = plural_en(singular_en)
                plural_trad = trads_plurais.get(plural_en_str, plural_en_str)
            else:
                plural_trad = None

        if plural_trad:
            # Se o item é equipamento, o plural também deve estar no singular? Não, geralmente plural é usado para itens stackáveis (flechas, runas). Equipamentos não têm plural, então não definimos plural para eles.
            # Apenas definimos se não for vazio
            pass
        else:
            # Se não conseguimos plural, removemos o atributo se existir
            pass

        # Aplicar plural no XML
        if plural_trad:
            elem.set('plural', plural_trad)
        else:
            if elem.get('plural') is not None:
                del elem.attrib['plural']

        # Descrição
        if item_info["desc_idx"] is not None:
            desc_elem = elem.find('./attribute[@key="description"]')
            if desc_elem is not None:
                desc_orig = dados["descs"][item_info["desc_idx"]]
                desc_trad = trads_descs.get(desc_orig, desc_orig)
                desc_elem.set('value', desc_trad)

    # 7. Gravar em ISO‑8859‑1
    xml_str = ET.tostring(root, encoding='utf-8').decode('utf-8')
    decl = '<?xml version="1.0" encoding="ISO-8859-1"?>\n'
    body = xml_str[xml_str.find('?>')+2:]
    safe = (decl + body).encode('latin-1', errors='replace').decode('latin-1')

    with open(arquivo, 'w', encoding='iso-8859-1') as f:
        f.write(safe)

    print(f"\n✨ items.xml traduzido (plurais via API + singularização de equipamentos) em {time.time()-inicio:.1f}s.")

if __name__ == "__main__":
    main()