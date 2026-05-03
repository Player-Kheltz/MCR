#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re, sys
from pathlib import Path

CHECK_DIRS = ['data', 'data-canary', 'data-otservbr-global']
PROTECTED_RACES = {'blood', 'energy', 'fire', 'earth', 'venom', 'undead', 'ice', 'holy'}
PROTECTED_IMMUN = {'paralyze', 'invisible', 'bleed', 'outfit', 'drunk', 'lifedrain'}

def is_latin1(filepath):
    if filepath.suffix != '.lua': return True
    try:
        with open(filepath, 'rb') as f:
            raw = f.read()
            raw.decode('iso-8859-1')
            # Tenta detectar UTF-8: se decodificar como UTF-8 sem erros e tiver caracteres multi-byte, é suspeito
            try:
                raw.decode('utf-8')
                # Se tem bytes acima de 127 que formam sequências UTF-8 válidas, pode ser um ficheiro UTF-8 disfarçado
                if any(b > 127 for b in raw):
                    return False  # provavelmente UTF-8
            except:
                pass
            return True
    except:
        return False

def main():
    if len(sys.argv) < 2:
        print("Uso: python 5-revisar.py <raiz_servidor>"); return
    root = Path(sys.argv[1])
    relatorio = []
    for dire in CHECK_DIRS:
        base = root / dire
        if not base.exists(): continue
        for fp in base.rglob('*.lua'):
            if not is_latin1(fp):
                relatorio.append(f"[Encoding] {fp} não é Latin‑1 (provavelmente UTF‑8)")
            try:
                with open(fp, 'r', encoding='iso-8859-1', errors='replace') as f:
                    content = f.read()
            except: continue
            for m in re.finditer(r'race\s*=\s*"([^"]+)"', content):
                if m.group(1).lower() not in PROTECTED_RACES:
                    relatorio.append(f"[Race] '{m.group(1)}' em {fp}")
            for m in re.finditer(r'{ type = "([^"]+)"', content):
                if m.group(1).lower() not in PROTECTED_IMMUN:
                    relatorio.append(f"[Immunity] '{m.group(1)}' em {fp}")
            for m in re.finditer(r'\{ name = "([^"]+)"', content):
                relatorio.append(f"[Loot por nome] '{m.group(1)}' em {fp}")

    nomes = {}
    for dire in CHECK_DIRS:
        for fp in (root / dire).rglob('*/monster/**/*.lua'):
            try:
                with open(fp, 'r', encoding='iso-8859-1', errors='replace') as f:
                    content = f.read()
            except: continue
            m = re.search(r'createMonsterType\("([^"]+)"\)', content)
            if m:
                nome = m.group(1)
                if nome in nomes: relatorio.append(f"[Duplicado] '{nome}' em {fp} e {nomes[nome]}")
                else: nomes[nome] = str(fp)

    if relatorio:
        print("Problemas encontrados:")
        for r in relatorio: print(r)
    else:
        print("✅ Nenhum problema detectado!")

if __name__ == '__main__':
    main()