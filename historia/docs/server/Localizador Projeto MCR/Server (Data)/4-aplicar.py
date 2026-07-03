#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re, sys, json
from pathlib import Path

ALLOWED_BASES = ['data', 'data-canary', 'data-otservbr-global']
FORBIDDEN_DIRS = {'lib', 'libs', 'migrations', 'npclib', 'scripts/lib',
                  'MCR Scripts', 'modules', 'json', 'reports', 'logs'}

def is_allowed(filepath):
    parts = Path(filepath).parts
    for part in parts:
        if part in FORBIDDEN_DIRS: return False
        if part in ALLOWED_BASES: return True
    return False

def latin1_safe(text):
    return text.encode('latin-1', errors='replace').decode('latin-1')

def load_map(filepath):
    data = {}
    current = None
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                current = line[1:-1]; data[current] = {}
            elif '=' in line and current:
                k, v = line.split('=', 1); data[current][k] = v
    return data

def apply_lua(filepath, translations, original_map):
    is_lua = filepath.endswith('.lua')
    encoding = 'iso-8859-1' if is_lua else 'utf-8'
    with open(filepath, 'r', encoding=encoding) as f:
        lines = f.readlines()
    changed = False
    for key, new_text in translations.items():
        parts = key.split('_')
        if len(parts) < 2: continue
        try: line_idx = int(parts[0]) - 1
        except: continue
        if line_idx >= len(lines): continue
        line = lines[line_idx]
        orig = original_map.get(filepath, {}).get(key)
        if not orig: continue
        replacement = new_text
        # Força MCR se disponível
        from mcr_dict import MCR_CORRECTIONS
        if orig in MCR_CORRECTIONS:
            replacement = MCR_CORRECTIONS[orig]
        elif orig.lower() in MCR_CORRECTIONS:
            replacement = MCR_CORRECTIONS[orig.lower()]
        replacement = latin1_safe(replacement)
        if f'"{orig}"' in line:
            lines[line_idx] = line.replace(f'"{orig}"', f'"{replacement}"', 1)
            changed = True
    if changed:
        # Garantir que todas as linhas são Latin‑1 seguras
        lines = [latin1_safe(l) for l in lines]
        with open(filepath, 'w', encoding=encoding) as f:
            f.writelines(lines)

def main():
    if len(sys.argv) < 3:
        print("Uso: python 4-aplicar.py extraido.txt reparado.txt"); return
    original_map = load_map(sys.argv[1])
    repaired_map = load_map(sys.argv[2])

    for fp, strings in repaired_map.items():
        if not is_allowed(fp) or fp.endswith('items.xml'): continue
        if not os.path.exists(fp): continue
        apply_lua(fp, strings, original_map)
        print(f"✔ {fp}")

    print("Aplicação concluída (apenas scripts).")

if __name__ == '__main__':
    main()