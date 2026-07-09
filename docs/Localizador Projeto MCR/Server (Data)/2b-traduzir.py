#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Traduz nomes de monstros usando API com concatenação inteligente e dicionário MCR.
Muito mais rápido que a versão sequencial.
"""
import json, time, sys
from pathlib import Path
from deep_translator import GoogleTranslator

# Configurações
CACHE_ARQUIVO = "translation_cache_monsters.json"
DICT_MONSTERS  = "mcr_dict_monsters.py"   # dicionário opcional
SEPARADOR = " ||| "
MAX_CHARS = 4800
DELAY = 0.06
TENTATIVAS = 3
TIMEOUT = 25

# Patch de timeout global
import requests
original_get = requests.get
requests.get = lambda *a, **kw: original_get(*a, timeout=TIMEOUT, **kw)
def patched_send(self, req, **kw):
    kw.setdefault('timeout', TIMEOUT)
    return requests.Session.send.__wrapped__(self, req, **kw) if hasattr(requests.Session.send, '__wrapped__') else original_send(self, req, **kw)
original_send = requests.Session.send
requests.Session.send = patched_send

def carregar_cache():
    if Path(CACHE_ARQUIVO).exists():
        with open(CACHE_ARQUIVO, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def salvar_cache(cache):
    with open(CACHE_ARQUIVO, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def carregar_dicionario():
    if Path(DICT_MONSTERS).exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("mcr_monsters", DICT_MONSTERS)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return getattr(mod, 'MCR_MONSTERS', {})
    return {}

def montar_lotes(textos):
    lotes, atual, chars = [], [], 0
    for txt in textos:
        extra = len(txt) + (len(SEPARADOR) if atual else 0)
        if atual and chars + extra > MAX_CHARS:
            lotes.append(atual); atual, chars = [], 0
        atual.append(txt)
        chars += len(txt) + (len(SEPARADOR) if len(atual) > 1 else 0)
    if atual:
        lotes.append(atual)
    return lotes

def traduzir_lote_concatenado(lote, tradutor, cache):
    texto = SEPARADOR.join(lote)
    for tent in range(TENTATIVAS):
        try:
            res = tradutor.translate(texto)
            if res is None: continue
            partes = res.split(SEPARADOR)
            if len(partes) == len(lote):
                for orig, trad in zip(lote, partes):
                    cache[orig] = trad.strip()
                salvar_cache(cache)
                return {orig: trad.strip() for orig, trad in zip(lote, partes)}
            # Fallback com "|"
            partes_alt = [p.strip() for p in res.split("|") if p.strip()]
            if len(partes_alt) == len(lote):
                for orig, trad in zip(lote, partes_alt):
                    cache[orig] = trad.strip()
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
            trads[orig] = cache[orig]
            continue
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

def main():
    if len(sys.argv) < 3:
        print("Uso: python 2b-traduzir-monster-names.py nomes_monstros.txt nomes_monstros_traduzidos.txt")
        return
    input_file, output_file = sys.argv[1], sys.argv[2]
    with open(input_file, 'r', encoding='utf-8') as f:
        nomes = [line.strip() for line in f if line.strip()]

    cache = carregar_cache()
    mcr = carregar_dicionario()
    # Injetar MCR na cache
    for en, pt in mcr.items():
        cache[en] = pt
        cache[en.lower()] = pt
    salvar_cache(cache)

    pendentes = [n for n in nomes if n not in cache]
    print(f"Nomes a traduzir: {len(pendentes)} de {len(nomes)}")

    if pendentes:
        tradutor = GoogleTranslator(source='en', target='pt')
        lotes = montar_lotes(pendentes)
        traducoes = {}
        for lote in lotes:
            if len(lote) > 1:
                trads = traduzir_lote_concatenado(lote, tradutor, cache)
            else:
                trads = traduzir_lote_tradicional(lote, tradutor, cache)
            traducoes.update(trads)
            print(f"   Progresso: {len(traducoes)+len(nomes)-len(pendentes)}/{len(nomes)}")
            time.sleep(DELAY)
    else:
        traducoes = {}

    # Escrever resultado
    with open(output_file, 'w', encoding='utf-8') as f:
        for nome in nomes:
            trad = cache.get(nome, nome)
            f.write(f"{nome}={trad}\n")
    print(f"Traduções guardadas em {output_file}")

if __name__ == '__main__':
    main()