#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplica traduções de nomes de monstros com uma única regex combinada (ultra rápido)."""
import sys, re
from pathlib import Path

FORBIDDEN_DIRS = {'lib', 'libs', 'migrations', 'vcproj', 'tests', 'src', 'cmake',
                  '.github', 'docker', 'docs', 'metrics', 'npclib', 'scripts/lib',
                  'MCR Scripts', 'modules', 'json', 'reports', 'logs', 'XML'}
FORBIDDEN_FILES = {'config.lua', 'global.lua', 'core.lua', 'stages.lua', 'update.lua',
                   'titles.lua', 'achievements.lua', 'badges.lua',
                   'register_npc_type.lua', 'register_monster_type.lua'}

def is_allowed(filepath):
    parts = filepath.parts
    for part in parts:
        if part in FORBIDDEN_DIRS:
            return False
    return filepath.name not in FORBIDDEN_FILES and filepath.suffix == '.lua'

def latin1_safe(text):
    return text.encode('latin-1', errors='replace').decode('latin-1')

def carregar_mapeamento(ficheiro):
    mapeamento = {}
    with open(ficheiro, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '=' in line:
                orig, trad = line.split('=', 1)
                # garantir que a tradução é segura para Latin‑1
                mapeamento[orig] = latin1_safe(trad)
    return mapeamento

def compilar_regex(mapeamento):
    """Cria uma regex que captura qualquer um dos nomes originais (entre aspas)."""
    # Escapa cada chave e junta com '|', ordenando por tamanho decrescente
    escaped = [re.escape(name) for name in sorted(mapeamento, key=len, reverse=True)]
    pattern = r'"(' + '|'.join(escaped) + r')"'
    return re.compile(pattern)

def substituir_em_ficheiro(filepath, pattern, mapeamento):
    try:
        with open(filepath, 'r', encoding='iso-8859-1') as f:
            content = f.read()
    except:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return False

    # Pré‑filtro rápido
    if not any(original in content for original in mapeamento):
        return False

    original_content = content

    def replacer(match):
        nome_encontrado = match.group(1)
        trad = mapeamento.get(nome_encontrado)
        if trad:
            return f'"{trad}"'
        return match.group(0)  # não substitui (nunca deve acontecer)

    content = pattern.sub(replacer, content)

    if content != original_content:
        with open(filepath, 'w', encoding='iso-8859-1') as f:
            f.write(content)
        return True
    return False

def main():
    if len(sys.argv) < 3:
        print("Uso: python 3b-aplicar.py nomes_monstros_traduzidos.txt <raiz_servidor>")
        return
    map_file = sys.argv[1]
    root = Path(sys.argv[2])

    mapeamento = carregar_mapeamento(map_file)
    pattern = compilar_regex(mapeamento)
    print(f"Aplicando {len(mapeamento)} traduções de monstros (regex combinada)...")

    count = 0
    for fp in root.rglob('*.lua'):
        if not is_allowed(fp):
            continue
        if substituir_em_ficheiro(fp, pattern, mapeamento):
            count += 1
            print(f"✔ {fp}")

    print(f"Alterados {count} ficheiros com sucesso.")

if __name__ == '__main__':
    main()