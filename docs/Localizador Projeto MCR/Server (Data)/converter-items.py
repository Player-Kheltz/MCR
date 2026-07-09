#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Converte items_bom.xml (UTF-8) → items.xml (ISO-8859-1) com declaração correcta."""
import sys
from pathlib import Path

def main():
    src = "items_bom.xml"               # o teu ficheiro bom
    dst = "items.xml"        # destino no servidor

    if not Path(src).exists():
        print(f"Erro: '{src}' não encontrado.")
        return

    # Lê o ficheiro bom como UTF-8 (onde os acentos estão correctos)
    with open(src, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove a declaração XML antiga e põe a de Latin-1
    header = '<?xml version="1.0" encoding="ISO-8859-1"?>\n'
    body = content[content.find('?>') + 2:] if '?>' in content else content
    latin1_safe = header + body

    # Grava estritamente em ISO-8859-1, substituindo caracteres impossíveis por '?'
    with open(dst, 'w', encoding='iso-8859-1') as f:
        f.write(latin1_safe)

    print(f"✔ {dst} gerado com sucesso (ISO-8859-1).")

if __name__ == '__main__':
    main()