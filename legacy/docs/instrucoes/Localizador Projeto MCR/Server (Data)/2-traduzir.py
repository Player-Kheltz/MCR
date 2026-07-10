#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, re, time, sys
from pathlib import Path
import requests
from deep_translator import GoogleTranslator
from mcr_dict import MCR_CORRECTIONS

CACHE_ARQUIVO = "translation_cache.json"
SEPARADOR = " ||| "
MAX_CHARS = 4800
DELAY = 0.06
TENTATIVAS = 3
TIMEOUT = 25
USAR_CONCATENACAO = True

original_get = requests.get
requests.get = lambda *a, **kw: original_get(*a, timeout=TIMEOUT, **kw)
original_send = requests.Session.send
def patched_send(self, req, **kw):
    kw.setdefault('timeout', TIMEOUT)
    return original_send(self, req, **kw)
requests.Session.send = patched_send

def carregar_cache():
    if Path(CACHE_ARQUIVO).exists():
        with open(CACHE_ARQUIVO, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def salvar_cache(cache):
    with open(CACHE_ARQUIVO, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def is_translatable(text):
    if not text or len(text.strip()) < 2:
        return False
    if re.match(r'^%[a-zA-Z%\[\]\.\d]+$', text.strip()):
        return False
    if re.match(r'^[\d\s\.\-+]+$', text.strip()):
        return False
    if re.match(r'^[^\w\s]+$', text.strip()):
        return False
    return True

def extrair_strings_do_extraido(extraido_path):
    textos_unicos = {}
    linhas_orig = []
    with open(extraido_path, 'r', encoding='utf-8') as f:
        for linha in f:
            linhas_orig.append(linha)
            if '=' in linha and not linha.startswith('['):
                _, texto = linha.strip().split('=', 1)
                texto = texto.strip()
                if texto and is_translatable(texto):
                    textos_unicos[texto] = None
    return list(textos_unicos.keys()), linhas_orig

def traduzir_lote_concatenado(lote, tradutor, cache):
    texto_concatenado = SEPARADOR.join(lote)
    for tent in range(TENTATIVAS):
        try:
            resultado = tradutor.translate(texto_concatenado)
            if resultado is None: continue
            partes = resultado.split(SEPARADOR)
            if len(partes) == len(lote):
                for orig, trad in zip(lote, partes): cache[orig] = trad.strip()
                salvar_cache(cache)
                return {orig: trad.strip() for orig, trad in zip(lote, partes)}
            partes_alt = [p.strip() for p in resultado.split("|") if p.strip()]
            if len(partes_alt) == len(lote):
                for orig, trad in zip(lote, partes_alt): cache[orig] = trad.strip()
                salvar_cache(cache)
                return {orig: trad.strip() for orig, trad in zip(lote, partes_alt)}
            print("   ⚠️ concat falhou, fallback...")
            break
        except Exception as e:
            print(f"   ⚠️ erro concat: {e}")
            time.sleep(2 ** tent)
    return traduzir_lote_tradicional(lote, tradutor, cache)

def traduzir_lote_tradicional(lote, tradutor, cache):
    trads = {}
    for orig in lote:
        if not is_translatable(orig):
            cache[orig] = orig; trads[orig] = orig; continue
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

def main():
    if len(sys.argv) < 3:
        print("Uso: python 2-traduzir.py extraido.txt traduzido.txt"); return
    extraido, traduzido = sys.argv[1], sys.argv[2]
    cache = carregar_cache()
    for eng, pt in MCR_CORRECTIONS.items(): cache[eng] = pt
    salvar_cache(cache)
    print(f"Cache + MCR: {len(cache)} entradas.")
    textos, linhas = extrair_strings_do_extraido(extraido)
    print(f"Strings únicas: {len(textos)}")
    pendentes = [t for t in textos if t not in cache]
    print(f"Pendentes: {len(pendentes)}")
    if pendentes:
        tradutor = GoogleTranslator(source='en', target='pt')
        lotes = montar_lotes_concatenacao(pendentes) if USAR_CONCATENACAO else [[t] for t in pendentes]
        traducoes = {}
        for lote in lotes:
            if USAR_CONCATENACAO and len(lote) > 1:
                trads = traduzir_lote_concatenado(lote, tradutor, cache)
            else:
                trads = traduzir_lote_tradicional(lote, tradutor, cache)
            traducoes.update(trads)
            print(f"   Progresso: {len(traducoes)}/{len(pendentes)}")
        traducoes.update({t: cache[t] for t in pendentes if t in cache})
    else:
        traducoes = {t: cache[t] for t in textos if t in cache}
    salvar_cache(cache)
    with open(traduzido, 'w', encoding='utf-8') as f:
        for linha in linhas:
            if '=' in linha and not linha.startswith('['):
                chave, orig = linha.strip().split('=', 1)
                orig = orig.strip()
                trad = traducoes.get(orig, orig) if is_translatable(orig) else orig
                f.write(f"{chave}={trad}\n")
            else:
                f.write(linha)
    print(f"Tradução concluída: {traduzido}")

if __name__ == '__main__':
    main()