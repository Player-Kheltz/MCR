#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys
from mcr_dict import MCR_CORRECTIONS

LOWERCASE_WORDS = {'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'no', 'na', 'para', 'com', 'sem', 'por', 'ou', 'a', 'o', 'as', 'os'}

def title_case_pt(text):
    if not text: return text
    words = text.split()
    result = []
    for i, w in enumerate(words):
        if i == 0 or i == len(words)-1: result.append(w.capitalize())
        elif w.lower() in LOWERCASE_WORDS: result.append(w.lower())
        else: result.append(w.capitalize())
    return ' '.join(result)

def apply_gender_fixes(original, translated, corrections):
    for eng, ptbr in corrections.items():
        if eng in original and ptbr not in translated:
            translated = re.sub(re.escape(eng), ptbr, translated, flags=re.IGNORECASE)
    return translated

def main():
    if len(sys.argv) < 4:
        print("Uso: python 3-reparar.py extraido.txt traduzido.txt reparado.txt"); return
    orig_texts = {}
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        current = None
        for line in f:
            line = line.strip()
            if line.startswith('['): current = line[1:-1]
            elif '=' in line: k, v = line.split('=', 1); orig_texts[k] = v
    output = []
    with open(sys.argv[2], 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('[') or '=' not in line:
                output.append(line); continue
            key, trad = line.strip().split('=', 1)
            orig = orig_texts.get(key)
            if orig and len(orig.split()) <= 5 and not any(c.isdigit() for c in orig):
                trad = title_case_pt(trad)
            if orig:
                trad = apply_gender_fixes(orig, trad, MCR_CORRECTIONS)
            if orig and orig in MCR_CORRECTIONS:
                trad = MCR_CORRECTIONS[orig]
            elif orig and orig.lower() in MCR_CORRECTIONS:
                trad = MCR_CORRECTIONS[orig.lower()]
            output.append(f"{key}={trad}\n")
    with open(sys.argv[3], 'w', encoding='utf-8') as f:
        f.writelines(output)
    print(f"Reparação concluída: {sys.argv[3]}")

if __name__ == '__main__':
    main()